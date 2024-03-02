from .system import ActorSystem


class Meta(type):
    """
    this thing here basically wraps all o/g actor methods so that they could be
    called as static methods from the outside
    """
    def __new__(cls, name, bases, attrs, **kwargs):
        klass = None

        def create_wrapper(name, original):
            def wrapper(self, *args, **kwargs):
                if isinstance(self, ActorSystem):
                    return self.ask(klass, name, *args, **kwargs)
                else:
                    return original(self, *args, **kwargs)

            setattr(wrapper, "original", original)

            return wrapper

        for name in attrs:
            if not name.startswith("_") and callable(attrs[name]):
                attrs[name] = create_wrapper(name, attrs[name])

        klass = super(Meta, cls).__new__(cls, name, bases, attrs, **kwargs)

        return klass


class Actor(metaclass=Meta):
    def __init__(self, system: ActorSystem) -> None:
        self.system = system
