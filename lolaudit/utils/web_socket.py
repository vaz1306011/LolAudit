from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar


def format_url(url: str) -> str:
    return "OnJsonApiEvent_" + url.strip("/").replace("/", "_")


F = TypeVar("F", bound=Callable[..., Any])


def subscribe(url: str) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(self, *args: Any, **kwargs: Any) -> Any:
            if not args:
                return

            if args[0] != format_url(url):
                return

            return func(self, *args[1:], **kwargs)

        return wrapper  # type: ignore

    return decorator
