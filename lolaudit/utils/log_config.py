import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Deque
from collections import deque

PROJECT_ROOT = "LolAudit"
PACKAGE_NAME = "lolaudit"
CURRENT_LOG_PATH: Path | None = None
LOG_BUFFER_MAX_LINES = 5000
LOG_BUFFER: Deque[str] = deque(maxlen=LOG_BUFFER_MAX_LINES)


class MemoryLogHandler(logging.Handler):
    def emit(self, record) -> None:
        try:
            msg = self.format(record)
            LOG_BUFFER.append(msg)
        except Exception:
            self.handleError(record)


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
        for line in traceback.format_stack():
            stack.append(line)
            if PROJECT_ROOT in line and "logger." not in line:
                continue
            elif PROJECT_ROOT not in line:
                break
        filtered = [s for s in stack if "logging" not in s]
        return "".join(filtered)

    def __add_space(self, text: str, num_spaces: int) -> str:
        spaces = " " * num_spaces
        return spaces + text.replace("\n", "\n" + spaces)


def setup_logging() -> None:
    global CURRENT_LOG_PATH
    formatter = TraceStyleFormatter()

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    memory_handler = MemoryLogHandler()
    memory_handler.setFormatter(formatter)

    file_handler = None
    if not getattr(sys, "frozen", False):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_dir = Path("log")
        log_dir.mkdir(exist_ok=True)
        CURRENT_LOG_PATH = log_dir / f"{timestamp}.log"
        file_handler = logging.FileHandler(CURRENT_LOG_PATH, encoding="utf-8")
        file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(memory_handler)

    logger = logging.getLogger(PACKAGE_NAME)
    logger.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    logger.addHandler(memory_handler)
    file_handler and logger.addHandler(
        file_handler
    )  # pyright: ignore[reportUnusedExpression]
    logger.propagate = False

    web_socket_logger = logging.getLogger("websocket")
    web_socket_logger.setLevel(logging.CRITICAL)
    web_socket_logger.propagate = False


def get_current_log_path() -> Path | None:
    if CURRENT_LOG_PATH and CURRENT_LOG_PATH.exists():
        return CURRENT_LOG_PATH
    log_dir = Path("log")
    if not log_dir.exists():
        return None
    log_files = sorted(
        log_dir.glob("*.log"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return log_files[0] if log_files else None


def dump_log_buffer(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for line in LOG_BUFFER:
            f.write(line)
