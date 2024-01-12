from typing import Any
from .inbox import Inbox


class Actor:
    inbox: Inbox
    handler: type[Any]

    def __init__(self, handler: type[Any], *args, **kwargs) -> None:
        self.handler = handler
