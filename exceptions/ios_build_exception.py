from sublime import error_message
from logging import exception


class IosBuildException(Exception):
    """Exception raised for errors in the input.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class UnknownException(IosBuildException): ...

def present_error(title: str, error: IosBuildException):
    exception(f"{title}: {error.message}")
    error_message(f"{title}\n{error.message}")

def present_unknown_error(title: str, error: Exception):
    exception(f"{title}: {error}")
    error_message(f"{title}\n{error}")
