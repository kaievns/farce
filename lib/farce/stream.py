import random
import asyncio
from event_bus import EventBus
from .message import Message

bus = EventBus()


class Stream:
    def __init__(self) -> None:
        self.listeners = []
        self.iterators = []
        self.mappings = []
        self.filters = []

        self.key = f"stream:{random.random()}"

        self._listen()

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
        self.mappings.append([map, stream])
        return stream

    def __aiter__(self):
        iterator = StreamIterator(self)
        self.iterators.append(iterator)
        return iterator

    def _remove(self, iterator):
        self.iterators.remove(iterator)

    def _listen(self):
        @bus.on(self.key)
        def _pipe_to_listeners(message: Message):
            for listener in self.listeners:
                res = listener(message)
                if asyncio.iscoroutine(res):
                    asyncio.create_task(res)

        @bus.on(self.key)
        def _pipe_to_iterators(message: Message):
            for iter in self.iterators:
                iter.put(message)

        @bus.on(self.key)
        def _pipe_to_mappings(message: Message):
            for [mapping, stream] in self.mappings:
                stream.put(mapping(message))

        @bus.on(self.key)
        def _pipe_downstream(message: Message):
            for [filter, stream] in self.filters:
                if filter(message):
                    stream.put(message)


class StreamIterator:
    queue: asyncio.Queue
    parent: Stream

    def __init__(self, stream: Stream) -> None:
        self.parent = stream
        self.queue = asyncio.Queue()

    def put(self, message: Message):
        self.queue.put_nowait(message)

    async def __anext__(self):
        try:
            item = await self.queue.get()
            self.queue.task_done()
            return item
        except:  # asyncio.CancelledError:  # disconnections
            self.parent._remove(self)
