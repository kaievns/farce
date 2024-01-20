import pytest
import asyncio
from .. import ActorSystem


@pytest.mark.asyncio
async def test_spawn():
    class Handler:
        def __init__(self, *args, **kwargs) -> None:
            self.args = args
            self.kwargs = kwargs

    system = ActorSystem()
    actor = system.spawn(Handler, 1, 2, 3, a=4, b=5)

    assert isinstance(actor.handler, Handler)
    assert actor.handler.args == (1, 2, 3)
    assert actor.handler.kwargs == {'a': 4, 'b': 5}


# @pytest.mark.asyncio
# async def test_ask():
#     class Handler:
#         def name(self, *args, **kwargs):
#             return "My name is %s %s" % (args, kwargs)

#     system = ActorSystem()
#     system.spawn(Handler)

#     await asyncio.sleep(0.01)

#     result = await system.ask(Handler, "name", 1, 2, a=3)
#     # await asyncio.sleep(0.2)

#     assert result == "My name is (1, 2) {'a': 3}"
