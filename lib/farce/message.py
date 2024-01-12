from typing import Any, Optional


class Message:
    sender: Optional[Any]
    to: Optional[Any]
    subject: str
    message: any
