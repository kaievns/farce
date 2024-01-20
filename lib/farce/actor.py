import asyncio
from typing import Any
from .stream import Stream
from .message import Message


class Actor:
    inbox: Stream
    handler: any
    system: any

    def __init__(self, system: any, handler: type[Any], *args, **kwargs) -> None:
        self.inbox = system.stream.filter(lambda x: x.to == handler)
        self.handler = handler(*args, **kwargs)
        self.system = system

        asyncio.create_task(self.start())

    async def start(self):
        async for message in self.inbox:
            await self.handle(message)

    async def handle(self, message: Message):
        try:
            name = message.subject
            args = message.args
            kwargs = message.kwargs
            method = getattr(self.handler, name)

            print(name, args, kwargs, method)

            result = await asyncio.create_task(method(*args, **kwargs))

            print(result)

            if hasattr(message, "future") and message.future != None:
                message.future.set_result(result)
        except Exception as err:
            if hasattr(message, "future") and message.future != None:
                message.future.set_exception(err)
