import pytest
import asyncio
from ..actor import Actor
from ..system import ActorSystem


@pytest.mark.asyncio
async def test_actor():
    system = ActorSystem()

    calls = []

    class Thing(Actor):
        def hello(self, one, two=2, three=3):
            return [self, one, two, three]

        async def asyncy(self, *args):
            await asyncio.sleep(0.01)
            call = ["asyncy", *args]
            calls.append(call)
            return call

    system.spawn(Thing)

    result = await Thing.hello(system, 1, 2)

    assert isinstance(result[0], Thing)
    assert result[1:] == [1, 2, 3]

    result = await Thing.hello(system, 2, 3, 4)

    assert isinstance(result[0], Thing)
    assert result[1:] == [2, 3, 4]

    result = await Thing.asyncy(system, 3, 4, 5)

    assert result == ["asyncy", 3, 4, 5]

    calls.clear()

    Thing.asyncy(system, 1, 2, 3)

    await asyncio.sleep(0.1)

    assert calls == [["asyncy", 1, 2, 3]]
