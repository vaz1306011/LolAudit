import logging
import traceback


class TraceStyleFormatter(logging.Formatter):
    def format(self, record):
        level = f"[{record.levelname}]"
        time = self.formatTime(record, "%Y-%m-%d %H:%M:%S")

        header = f"{level} - {time}:"
        message = record.getMessage()

        if record.levelno >= logging.ERROR or record.levelno == logging.DEBUG:
            stack = "".join(traceback.format_stack()[:-1])
            return f"{header}\n{stack}    {message}\n"
        else:
            location = f"{record.pathname}:{record.lineno}"
            return f"{header} {location}\n  {message}\n"


def setup_logging(level: int = logging.INFO) -> None:
    formatter = TraceStyleFormatter()

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)
    root_logger.addHandler(handler)

    logger = logging.getLogger("lolaudit")
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.propagate = False
