import asyncio
from concurrent.futures import Future
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
            args = message.body.args
            kwargs = message.body.kwargs
            future = message.body.future
            method = getattr(self.actor, name)
            original = getattr(method, "original", method)

            if asyncio.iscoroutinefunction(original):
                coro = method(*args, **kwargs)
            else:
                coro = asyncio.to_thread(method, *args, **kwargs)

            def done(task):
                err = task.exception()
                res = None if err else task.result()
                self._done(future, err, res)

            loop = future.get_loop()

            try:
                current_loop = asyncio.get_event_loop()
            except:
                current_loop = None

            if loop == current_loop:
                task = loop.create_task(coro)
            else:
                task = asyncio.run_coroutine_threadsafe(coro, loop)

            task.add_done_callback(done)

        except Exception as err:
            self._done(future, err)

    def _done(self, future: Future, err: Exception = None, result: any = None):
        if err != None:
            future.set_exception(err)
            self.system.logger.error(err)
        else:
            future.set_result(result)
