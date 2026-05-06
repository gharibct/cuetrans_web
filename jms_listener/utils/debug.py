import inspect
import logging
from pathlib import Path


def debug_print(*values, sep: str = " ", level: int = logging.INFO) -> None:
    frame = inspect.currentframe()
    caller = frame.f_back if frame else None
    location = "unknown"
    logger_name = __name__

    if caller:
        module = inspect.getmodule(caller)
        logger_name = module.__name__ if module else logger_name
        location = f"{Path(caller.f_code.co_filename).name}:{caller.f_lineno}"

    message = sep.join(str(value) for value in values)
    logging.getLogger(logger_name).log(level, "%s - %s", location, message)
