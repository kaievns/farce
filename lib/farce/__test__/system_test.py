import pytest
import asyncio
from .. import ActorSystem


class Actor:
    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs

    def name(self, *args, **kwargs):
        return "My name is %s %s" % (args, kwargs)

    def fail(self, *args):
        raise ValueError("fail", *args)

    async def async_task(self, *args, **kwargs):
        await asyncio.sleep(0.01)
        return f"async task {args}, {kwargs}"

    async def async_fail(self, *args):
        await asyncio.sleep(0.01)
        raise ValueError("async fail", *args)


@pytest.mark.asyncio
async def test_spawn():
    system = ActorSystem()
    system.spawn(Actor, 1, 2, 3, a=4, b=5)
    handler = system.registry[Actor]

    assert isinstance(handler.actor, Actor)
    assert handler.actor.args == (system, 1, 2, 3)
    assert handler.actor.kwargs == {'a': 4, 'b': 5}


@pytest.mark.asyncio
async def test_ask():
    system = ActorSystem()
    system.spawn(Actor)

    result = await system.ask(Actor, "name", 1, 2, a=3)

    assert result == "My name is (1, 2) {'a': 3}"


@pytest.mark.asyncio
async def test_ask_error():
    system = ActorSystem()
    system.spawn(Actor)

    try:
        await system.ask(Actor, "fail", 1, 2, 3)
        assert False, "supposed to fail"
    except ValueError as err:
        assert f"{err}" == f"{ValueError('fail', 1, 2, 3)}"


@pytest.mark.asyncio
async def test_no_method_error():
    system = ActorSystem()
    system.spawn(Actor)

    try:
        await system.ask(Actor, "non_existing", 1, 2, 3)
        assert False, "supposed to fail"
    except AttributeError as err:
        assert f"{err}" == "'Actor' object has no attribute 'non_existing'"


@pytest.mark.asyncio
async def test_async_handlers():
    system = ActorSystem()
    system.spawn(Actor)

    result = await system.ask(Actor, "async_task", 1, 2, 3, a=4, b=5)

    assert result == "async task (1, 2, 3), {'a': 4, 'b': 5}"

    try:
        await system.ask(Actor, "async_fail", 'a', 'b')
        assert False, "supposed to fail"
    except ValueError as err:
        assert f"{err}" == "('async fail', 'a', 'b')"


@pytest.mark.asyncio
async def test_pipe():
    calls = []

    class Actor:
        def __init__(self, system: ActorSystem) -> None:
            pass

        def test(self, *args, **kwargs):
            calls.append([args, kwargs])

    system = ActorSystem()
    system.spawn(Actor)

    system.pipe("ping", Actor, "test")

    system.send("ping", 1, 2, a=3)
    system.send("pong", 2, 3, b=4)
    system.send("ping", 3, 4, c=5)
    system.send("test", 4, 5, d=6)

    await asyncio.sleep(0.02)

    assert calls == [[(1, 2), {'a': 3}], [(3, 4), {'c': 5}]]


@pytest.mark.asyncio
async def test_interactions():
    class ActorA:
        def __init__(self, system: ActorSystem) -> None:
            self.system = system

        async def test(self):
            res = await self.system.ask(ActorB, "test")
            return f"A > {res}"

    class ActorB:
        def __init__(self, system: ActorSystem) -> None:
            self.system = system

        async def test(self):
            res = await self.system.ask(ActorC, "test")
            return f"B > {res}"

    class ActorC:
        def __init__(self, system: ActorSystem) -> None:
            self.system = system

        def test(self):
            return "C"

    system = ActorSystem()
    system.spawn(ActorA)
    system.spawn(ActorB)
    system.spawn(ActorC)

    res = await system.ask(ActorA, "test")

    assert res == "A > B > C"