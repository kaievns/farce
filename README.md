# Farce

An actor system implementation on top of
[asyncio](https://docs.python.org/3/library/asyncio.html) co-routines. The basic
point is to decouple IO heavy operations under more manageable actor pattern
abstractions. It automatically takes care of multi-threading, asyncio reactor
event loop stitching, as well as message bus systems decoupling mechanism.

## Usage example

```py
from farce import Actor, ActorSystem

class Thing(Actor):
    def hello(self, one, two=2, three=3):
        return [self, one, two, three]

    async def asyncy(self, *args):
        await asyncio.sleep(0.01)
        call = ["asyncy", *args]
        self.calls.append(call)
        return call

system = ActorSystem()
system.spawn(Thing)

result = await Thing.hello(system, 1, 2)

assert isinstance(result[0], Thing)
assert result[1:] == [1, 2, 3]
```

## Copyright & License

All code in this repository is released under the terms of the MIT license

Copyright (C) 2024 Kai Evans
