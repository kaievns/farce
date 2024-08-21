from asyncio import Future
from typing import Any, NamedTuple, Optional, Union


class MethodCall(NamedTuple):
    args: any
    kwargs: any
    future: Future


class Message(NamedTuple):
    to: Optional[type[Any]]  # actor handler class
    subject: str
    body: Union[MethodCall, any]
