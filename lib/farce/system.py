import asyncio
from typing import Any
from .handler import Handler
from .stream import Stream
from .error import FarceError
from .message import Message


class ActorSystem:
    stream: Stream
    registry: dict[type[Any], Handler]

    def __init__(self) -> None:
        self.stream = Stream()
        self.registry = {}

    def spawn(self, actor: type[Any], *args, **kwargs) -> None:
        if not actor in self.registry:
            self.registry[actor] = Handler(self, actor, *args, **kwargs)
        else:
            raise FarceError("Already spawned: %s" % actor.__name__)

    def send(self, subject: str, *args, **kwargs) -> None:
        self.stream.put(Message(subject=subject, args=args,
                        kwargs=kwargs, to=None, future=None))

    def ask(self, actor: type[Any], subject: str, *args, **kwargs) -> asyncio.Future:
        if not actor in self.registry:
            raise FarceError("%s actor was not spawned yet" % actor.__name__)

        # loop = asyncio.get_event_loop()
        # future = loop.create_future()
        future = self._make_future()

        self.stream.put(Message(
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
                to=actor,
                subject=method,
                args=message.args,
                kwargs=message.kwargs,
                future=None
            ))

        self.stream.filter(lambda m: m.subject == subject).pipe_to(handler)

    def _make_future(self):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError as e:
            if str(e).startswith('There is no current event loop in thread'):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            else:
                raise

        return loop.create_future()
