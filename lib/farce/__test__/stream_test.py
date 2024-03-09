import pytest
import asyncio
from ..stream import Stream


class Mocky:
    def __init__(self) -> None:
        self.calls = []
        self.tasks = []

    def reset(self):
        self.calls.clear()

    def stop(self):
        for task in self.tasks:
            task.cancel()

    def listen(self, stream: Stream):
        self.tasks.append(asyncio.create_task(self._listen(stream)))

    async def _listen(self, stream: Stream):
        async for message in stream:
            self.calls.append(message)


@pytest.mark.asyncio
async def test_pipes():
    calls = []

    stream = Stream()

    stream.pipe_to(lambda m: calls.append(m))
    stream.pipe_to(lambda m: calls.append(m))
    stream.pipe_to(lambda m: calls.append(m))

    stream.put("hello")
    stream.put("there")

    await asyncio.sleep(0.01)

    assert calls == ['hello', 'hello', 'hello', 'there', 'there', 'there']

    calls.clear()

    stream.put("hello")
    await asyncio.sleep(0.01)
    stream.put("there")

    await asyncio.sleep(0.01)

    assert calls == ['hello', 'hello', 'hello', 'there', 'there', 'there']


# @pytest.mark.asyncio
# async def test_async_pipes():
#     calls = []

#     async def async_receiver(m):
#         await asyncio.sleep(0)
#         calls.append(m)

#     stream = Stream()

#     stream.pipe_to(lambda m: calls.append(m))
#     stream.pipe_to(lambda m: calls.append(m))
#     stream.pipe_to(async_receiver)

#     stream.put("hello")
#     stream.put("there")

#     await asyncio.sleep(0.01)

#     # two sync calls followed by an async call
#     assert calls == ['hello', 'hello', 'there', 'there', 'hello', 'there']

#     calls.clear()

#     stream.put("hello")
#     await asyncio.sleep(0.01)
#     stream.put("there")

#     await asyncio.sleep(0.01)

#     print(calls)

#     # the async calls land at the end of each batch
#     assert calls == ['hello', 'hello', 'hello', 'there', 'there', 'there']


@pytest.mark.asyncio
async def test_iterator():
    mock = Mocky()

    stream = Stream()

    mock.listen(stream)
    mock.listen(stream)
    mock.listen(stream)

    await asyncio.sleep(0.001)

    stream.put("hello")
    stream.put("there")

    await asyncio.sleep(0.02)

    assert mock.calls == ['hello', 'there', 'hello', 'there', 'hello', 'there']

    mock.reset()

    stream.put("hello")
    await asyncio.sleep(0.01)
    stream.put("there")

    await asyncio.sleep(0.02)

    assert mock.calls == ['hello', 'hello', 'hello', 'there', 'there', 'there']


@pytest.mark.asyncio
async def test_filter():
    calls = []
    pings = []
    pongs = []

    stream = Stream()

    stream.pipe_to(lambda m: calls.append(m))
    stream.filter(lambda x: x == "ping").pipe_to(lambda m: pings.append(m))
    stream.filter(lambda x: x == "pong").pipe_to(lambda m: pongs.append(m))

    stream.put("ping")
    stream.put("pong")
    stream.put("ping")
    stream.put("pong")

    await asyncio.sleep(0.02)

    assert calls == ["ping", "pong", "ping", "pong"]
    assert pings == ["ping", "ping"]
    assert pongs == ["pong", "pong"]


@pytest.mark.asyncio
async def test_another_filter():
    calls = []

    stream = Stream()

    stream.map(lambda x: f"{x}ed").pipe_to(lambda m: calls.append(m))

    stream.put("ping")
    stream.put("pong")
    stream.put("ping")
    stream.put("pong")

    await asyncio.sleep(0.02)

    print(calls)

    assert calls == ["pinged", "ponged", "pinged", "ponged"]
