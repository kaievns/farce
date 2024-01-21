import inspect
import asyncio
from typing import Any
from .actor import Actor
from .stream import Stream
from .error import FarceError
from .message import Message


class ActorSystem:
    stream: Stream
    registry: dict[type[Any], Actor]

    def __init__(self) -> None:
        self.stream = Stream()
        self.registry = {}

    def spawn(self, actor: type[Any], *args, **kwargs) -> None:
        if not actor in self.registry:
            self.registry[actor] = Actor(self, actor, *args, **kwargs)
        else:
            raise FarceError("Already spawned: %s" % actor.__name__)

    def send(self, subject: str, *args, **kwargs) -> None:
        self.stream.put(Message(subject=subject, args=args,
                        kwargs=kwargs, caller=None, to=None, future=None))

    def ask(self, actor: type[Any], subject: str, *args, **kwargs) -> asyncio.Future:
        if not actor in self.registry:
            raise FarceError("%s actor was not spawned yet" % actor.__name__)

        future = asyncio.get_event_loop().create_future()
        stack = inspect.stack()
        caller = None
        if "self" in stack[1][0].f_locals:
            caller = stack[1][0].f_locals["self"].__class__

        self.stream.put(Message(
            caller=caller,
            to=actor,
            subject=subject,
            args=args,
            kwargs=kwargs,
            future=future
        ))
        return future

    # essentially a non async alias for ask
    def tell(self, actor: type[Any], subject: str, *args, **kwargs) -> None:
        self.ask(actor, subject, *args, **kwargs)

    def pipe(self, subject: str, actor: type[Any], method: str):
        def handler(message: Message):
            self.stream.put(Message(
                caller=message.caller,
                to=actor,
                subject=method,
                args=message.args,
                kwargs=message.kwargs,
                future=None
            ))

        self.stream.filter(lambda m: m.subject == subject).pipe_to(handler)
