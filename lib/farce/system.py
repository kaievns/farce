from typing import Any
from .message import Message


class ActorSystem:
    def spawn(self, actor: type[Any], *args, **kwargs):
        pass

    def send(self, subject: str, *args):
        print(subject, args)
        pass

    def ask(self):
        pass

    def tell(self):
        pass
