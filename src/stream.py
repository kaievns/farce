import random
import asyncio
from event_bus import EventBus
from .message import Message

bus = EventBus()


class Stream:
    def __init__(self) -> None:
        self.key = f"stream:{random.random()}"

        self.iterators = []
        self.listeners = []
        self.filters = []
        self.maps = []

        @bus.on(self.key)
        def pipe_to_listeners(message):
            for func in self.listeners:
                if asyncio.iscoroutinefunction(func):
                    asyncio.create_task(func(message))
                else:
                    func(message)

        @bus.on(self.key)
        def pipe_to_filters(message):
            for [filter, stream] in self.filters:
                if filter(message):
                    stream.put(message)

        @bus.on(self.key)
        def pipe_to_maps(message):
            for [transform, stream] in self.maps:
                stream.put(transform(message))

        @bus.on(self.key)
        def pipe_to_iterators(message: Message):
            for iter in self.iterators:
                iter.put(message)

    def put(self, message: Message):
        bus.emit(self.key, message)

    def pipe_to(self, listener: callable):
        self.listeners.append(listener)
        return self

    def filter(self, filter: callable):
        stream = Stream()
        self.filters.append([filter, stream])
        return stream

    def map(self, map: callable):
        stream = Stream()
        self.maps.append([map, stream])
        return stream

    def dedupe(self):
        stream = Stream()
        stream.prev_value = None

        @bus.on(self.key)
        def dedupper(value):
            if value != stream.prev_value:
                stream.prev_value = value
                stream.put(value)

        return stream

    def __aiter__(self):
        iterator = StreamIterator(self)
        self.iterators.append(iterator)
        return iterator

    def _remove(self, iterator):
        self.iterators.remove(iterator)


class StreamIterator:
    queue: asyncio.Queue
    parent: Stream

    def __init__(self, stream: Stream) -> None:
        self.parent = stream
        self.queue = asyncio.Queue()

    def put(self, message: Message):
        self.queue.put_nowait(message)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            item = await self.queue.get()
            self.queue.task_done()
            return item
        except:  # asyncio.CancelledError:  # disconnections
            self.parent._remove(self)
