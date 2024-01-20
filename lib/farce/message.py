from asyncio import Future
from typing import Any, NamedTuple, Optional


class Message(NamedTuple):
    caller: Optional[type[Any]]  # actor handler class
    to: Optional[type[Any]]  # actor handler class
    subject: str
    args: any
    kwargs: any
    future: Optional[Future]
