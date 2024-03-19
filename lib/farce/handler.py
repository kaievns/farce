import asyncio
from concurrent.futures import Future
from typing import Any, Generator
from .stream import Stream
from .message import Message


def tick(callable):
    if isinstance(callable, Generator):
        try:
            next(callable)
        except StopIteration:
            pass


class Handler:
    inbox: Stream
    actor: any
    system: any

    def __init__(self, system: any, actor: type[Any], *args, **kwargs) -> None:
        self.inbox = asyncio.Queue()
        self.actor = actor(system, *args, **kwargs)
        self.system = system

        system.stream.filter(lambda x: x.to is actor).pipe_to(
            lambda m: self.inbox.put_nowait(m))

        asyncio.create_task(self.listen())

    async def listen(self):
        while True:
            message = await self.inbox.get()

            try:
                self.handle(message)
            except Exception as err:
                self.system.logger.error(err)

    def handle(self, message: Message):
        middleware = self.actor.on_message(message)
        tick(middleware)

        # since the original System#ask sent a message in a thread
        # we're already in an off-loop thread and can call blocking
        # methods as is. and then report them as a threadsafe coroutine
        name = message.subject
        args = message.body.args
        kwargs = message.body.kwargs
        future = message.body.future
        method = getattr(self.actor, name)
        original = getattr(method, "original", method)

        if not asyncio.iscoroutinefunction(original):
            method = self.async_wrap(method, name)

        coro = method(*args, **kwargs)
        task = asyncio.run_coroutine_threadsafe(coro, future.get_loop())

        task.add_done_callback(self.call_after(future, middleware))

        return future

    def async_wrap(self, method, name):
        async def wrap(*args, **kwargs):
            return method(*args, **kwargs)
        return wrap

    def call_after(self, future: Future, middleware: callable):
        def done(task):
            tick(middleware)  # triggering the middleware

            err = task.exception()
            if err != None:
                future.set_exception(err)
                self.system.logger.error(err)
            else:
                future.set_result(task.result())
        return done
