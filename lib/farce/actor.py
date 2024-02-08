from .system import ActorSystem


class Actor:
    def __init__(self, system: ActorSystem) -> None:
        self.system = system
