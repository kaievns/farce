import pytest
import asyncio
from .. import ActorSystem


class Handler:
    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs

    def name(self, *args, **kwargs):
        return "My name is %s %s" % (args, kwargs)

    def fail(self, *args):
        raise ValueError("fail", *args)


@pytest.mark.asyncio
async def test_spawn():
    system = ActorSystem()
    actor = system.spawn(Handler, 1, 2, 3, a=4, b=5)

    assert isinstance(actor.handler, Handler)
    assert actor.handler.args == (1, 2, 3)
    assert actor.handler.kwargs == {'a': 4, 'b': 5}


@pytest.mark.asyncio
async def test_ask():
    system = ActorSystem()
    system.spawn(Handler)

    result = await system.ask(Handler, "name", 1, 2, a=3)

    assert result == "My name is (1, 2) {'a': 3}"


@pytest.mark.asyncio
async def test_ask_error():
    system = ActorSystem()
    system.spawn(Handler)

    try:
        await system.ask(Handler, "fail", 1, 2, 3)
        assert False, "supposed to fail"
    except ValueError as err:
        assert f"{err}" == f"{ValueError('fail', 1, 2, 3)}"


@pytest.mark.asyncio
async def test_no_method_error():
    system = ActorSystem()
    system.spawn(Handler)

    try:
        await system.ask(Handler, "non_existing", 1, 2, 3)
        assert False, "supposed to fail"
    except AttributeError as err:
        assert f"{err}" == "'Handler' object has no attribute 'non_existing'"
