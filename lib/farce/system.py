import asyncio
from typing import Any
from .handler import Handler
from .stream import Stream
from .error import FarceError
from .logger import Logger
from .message import Message, MethodCall


class ActorSystem:
    logger: Logger
    stream: Stream
    registry: dict[type[Any], Handler]
    loop: asyncio.AbstractEventLoop

    def __init__(self) -> None:
        self.logger = Logger()
        self.stream = Stream()
        self.registry = {}

        self.loop = asyncio.get_event_loop()

    def spawn(self, actor: type[Any], *args, **kwargs) -> None:
        if not actor in self.registry:
            self.registry[actor] = Handler(self, actor, *args, **kwargs)
        else:
            raise FarceError("Already spawned: %s" % actor.__name__)

    def send(self, subject: str, body: any) -> None:
        self.stream.put(Message(to=None, subject=subject, body=body))

    def ask(self, actor: type[Any], method: str, *args, **kwargs) -> asyncio.Future:
        if not actor in self.registry:
            raise FarceError("%s actor was not spawned yet" % actor.__name__)

        future = self.loop.create_future()

        self.stream.put(Message(
            to=actor,
            subject=method,
            body=MethodCall(
                args=args,
                kwargs=kwargs,
                future=future
            )
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
                body=MethodCall(
                    args=[message.body],
                    kwargs={},
                    future=self.loop.create_future()
                )
            ))

        self.stream.filter(lambda m: m.subject == subject).pipe_to(handler)
