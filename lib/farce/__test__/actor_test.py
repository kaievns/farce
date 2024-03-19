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


@pytest.mark.asyncio
async def test_middleware():
    system = ActorSystem()

    class GeneratorThing(Actor):
        calls = []

        def on_start(self):
            self.calls.append("started")

        def on_message(self, _message):
            self.calls.append("before handler")
            yield 1
            self.calls.append("after handler")

        def handler(self, *args):
            self.calls.append(f"the handler {args}")

        async def get_calls(self):
            await asyncio.sleep(0.1)
            self.calls.append("getting the calls")
            return self.calls

    system.spawn(GeneratorThing)

    await GeneratorThing.handler(system, 1, 2, 3)

    calls = await GeneratorThing.get_calls(system)

    assert calls == [
        'started',
        'before handler',
        'the handler (1, 2, 3)',
        'after handler',
        'before handler',
        'getting the calls',
        'after handler'
    ]

    class NonGenerator(Actor):
        calls = []

        def on_message(self, message):
            self.calls.append("before handler")

        def handler(self):
            self.calls.append("handler")

        def get_calls(self):
            return self.calls

    system.spawn(NonGenerator)

    await NonGenerator.handler(system)
    calls = await NonGenerator.get_calls(system)

    assert calls == ['before handler', 'handler', 'before handler']
