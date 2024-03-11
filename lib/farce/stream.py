import copy
import random
import asyncio
from event_bus import EventBus
from .message import Message

bus = EventBus()


class Stream:
    def __init__(self) -> None:
        self.iterators = []
        self.key = f"stream:{random.random()}"

        @bus.on(self.key)
        def _pipe_to_iterators(message: Message):
            for iter in self.iterators:
                iter.put(message)

    def put(self, message: Message):
        bus.emit(self.key, message)

    def pipe_to(self, listener: callable):
        # if asyncio.iscoroutinefunction(listener):
        #     @bus.on(self.key)
        #     def handler(message):
        #         try:
        #             loop = asyncio.get_event_loop()
        #         except:
        #             loop = asyncio.new_event_loop()
        #             asyncio.set_event_loop(loop)
        #         asyncio.create_task(listener(message))
        # else:
        @bus.on(self.key)
        def handler(message):
            listener(message)

        return self

    def filter(self, filter: callable):
        stream = Stream()

        @bus.on(self.key)
        def filterer(message):
            if filter(message):
                stream.put(message)

        return stream

    def map(self, map: callable):
        stream = Stream()

        @bus.on(self.key)
        def mapper(message):
            stream.put(map(message))

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

    async def __anext__(self):
        try:
            item = await self.queue.get()
            self.queue.task_done()
            return item
        except:  # asyncio.CancelledError:  # disconnections
            self.parent._remove(self)
