from typing import Any
from .stream import Stream


class Actor:
    inbox: Stream
    handler: any
    system: any

    def __init__(self, system: type[Any], handler: type[Any], *args, **kwargs) -> None:
        self.inbox = system.steam.filter(lambda x: x.to == handler)
        self.handler = handler(*args, **kwargs)
        self.system = system

        self.start()

    async def start():
        async for message in self.inbox:
            print("Handling %s" % message)
