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
        self.inbox = system.stream.filter(lambda x: x.to is actor)
        self.actor = actor(system, *args, **kwargs)
        self.system = system

        self.inbox.pipe_to(self.handle)

    def handle(self, message: Message):
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

        task.add_done_callback(self.call_after(future))

    def async_wrap(self, method, name):
        async def wrap(*args, **kwargs):
            return method(*args, **kwargs)
        return wrap

    def call_after(self, future: Future):
        def done(task):
            err = task.exception()
            if err != None:
                future.set_exception(err)
                self.system.logger.error(err)
            else:
                future.set_result(task.result())
        return done
