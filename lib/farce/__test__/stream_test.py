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
    calls = Mocky()
    pings = Mocky()
    pongs = Mocky()

    stream = Stream()

    calls.listen(stream)

    pings.listen(stream.filter(lambda x: x == "ping"))
    pongs.listen(stream.filter(lambda x: x == "pong"))

    await asyncio.sleep(0.002)

    stream.put("ping")
    stream.put("pong")
    stream.put("ping")
    stream.put("pong")

    await asyncio.sleep(0.02)

    assert calls.calls == ["ping", "pong", "ping", "pong"]
    assert pings.calls == ["ping", "ping"]
    assert pongs.calls == ["pong", "pong"]
