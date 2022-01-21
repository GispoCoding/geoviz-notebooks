import logging
import sys
from pathlib import Path

LOG_PATH = Path(__file__).parent.resolve().joinpath("logs")
if not LOG_PATH.exists():
    LOG_PATH.mkdir(parents=True, exist_ok=True)
LOG_LEVEL = logging.INFO
LOG_FORMAT = logging.Formatter("%(asctime)s %(name)s %(levelname)-8s %(message)s",
                               "%Y-%m-%d %H:%M:%S")


def create_logger(slug: str) -> logging.Logger:
    """Creates and returns a new logger."""
    logger = logging.getLogger(slug)

    # Return logger if already created
    if logger.handlers:
        return logger

    logger.setLevel(LOG_LEVEL)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(LOG_FORMAT)
    stream_handler.setLevel(LOG_LEVEL)
    logger.addHandler(stream_handler)

    log_file_path = LOG_PATH.joinpath(f"{slug}.log")
    file_handler = logging.FileHandler(str(log_file_path))
    file_handler.setFormatter(LOG_FORMAT)
    file_handler.setLevel(LOG_LEVEL)
    logger.addHandler(file_handler)

    return logger
