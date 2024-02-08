import asyncio
from typing import Any
from .stream import Stream
from .message import Message


class Handler:
    inbox: Stream
    actor: any
    system: any

    def __init__(self, system: any, actor: type[Any], *args, **kwargs) -> None:
        self.inbox = system.stream.filter(lambda x: x.to == actor)
        self.actor = actor(system, *args, **kwargs)
        self.system = system

        self.inbox.pipe_to(self.handle)

    async def start(self):
        async for message in self.inbox:
            await self.handle(message)

    def handle(self, message: Message):
        try:
            name = message.subject
            args = message.args
            kwargs = message.kwargs
            method = getattr(self.actor, name)

            coro = None
            if asyncio.iscoroutinefunction(method):
                coro = method(*args, **kwargs)
            else:
                coro = asyncio.to_thread(method, *args, **kwargs)

            def done(task):
                err = task.exception()
                res = None if err else task.result()
                self._done(message, err, res)

            asyncio.create_task(coro).add_done_callback(done)

        except Exception as err:
            self._done(message, err)

    def _done(self, message: Message, err: Exception = None, result: any = None):
        if hasattr(message, "future") and message.future != None:
            if err != None:
                message.future.set_exception(err)
            else:
                message.future.set_result(result)
