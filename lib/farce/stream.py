import asyncio
from .message import Message


class Stream:
    def __init__(self) -> None:
        self.iterators = []
        self.filters = []

    def put(self, message: Message):
        for iter in self.iterators:
            iter.put(message)

        for [filter, stream] in self.filters:
            if filter(message):
                stream.put(message)

    def filter(self, filter: callable):
        stream = Stream()
        self.filters.append([filter, stream])
        return stream

    def __aiter__(self):
        iterator = StreamIterator(self)
        self.iterators.append(iterator)
        return iterator

    def remove(self, iterator):
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
            self.parent.remove(self)
