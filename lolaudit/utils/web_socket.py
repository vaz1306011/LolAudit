from functools import wraps


def subscribe(url: str):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not args:
                return

            if args[0] != format_url(url):
                return

            return func(self, *args[1:], **kwargs)

        return wrapper

    return decorator


def format_url(url: str) -> str:
    return "OnJsonApiEvent_" + url.strip("/").replace("/", "_")
