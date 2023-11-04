import logging
import sys


def get_logger(name, level=logging.DEBUG):
    """Setup a logger."""
    logger = logging.getLogger(name)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    formatter = logging.Formatter(
        "[%(asctime)s][%(basename)s|%(lineno)s %(funcName)20s]"
        "[%(levelname)s]: %(message)s",
        "%H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
