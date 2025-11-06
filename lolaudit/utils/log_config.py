import logging
import traceback


class TraceStyleFormatter(logging.Formatter):
    def format(self, record) -> str:
        level = f"[{record.levelname}]"
        time = self.formatTime(record, "%Y-%m-%d %H:%M:%S")

        header = f"{level} - {time}:"
        message = record.getMessage()

        if record.levelno >= logging.ERROR or record.levelno == logging.DEBUG:
            stack = self.__filter_stack()
            return f"{header}\n{stack}{message}\n"
        else:
            location = f"File: {record.pathname}:{record.lineno}"
            return f"{header}\n{self.__add_space(location, 2)}\n{self.__add_space(message, 4)}\n"

    def __filter_stack(self) -> str:
        stack = []
        project_root = "LolAudit"
        for line in traceback.format_stack():
            stack.append(line)
            if project_root in line and "logger." not in line:
                continue
            elif project_root not in line:
                break
        filtered = [s for s in stack if "logging" not in s]
        return "".join(filtered)

    def __add_space(self, text: str, num_spaces: int) -> str:
        spaces = " " * num_spaces
        return spaces + text.replace("\n", "\n" + spaces)


def setup_logging() -> None:
    formatter = TraceStyleFormatter()

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler("lolaudit.log", encoding="utf-8")
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)
    root_logger.addHandler(console_handler)

    logger = logging.getLogger("lolaudit")
    logger.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.propagate = False

    web_socket_logger = logging.getLogger("websocket")
    web_socket_logger.setLevel(logging.CRITICAL)
    web_socket_logger.propagate = False
