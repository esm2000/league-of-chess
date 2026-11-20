"""Logging configuration for the League of Chess backend."""

import logging
import threading
from contextlib import contextmanager

logging.basicConfig(
    format="%(asctime)s %(message)s", datefmt="%m/%d/%Y | %I:%M:%S%p | " + ":"
)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


_suppression = threading.local()


class _ThreadSuppressionFilter(logging.Filter):
    """Drops records logged by a thread that is inside suppress_logging()."""

    def filter(self, record: logging.LogRecord) -> bool:
        return not getattr(_suppression, "active", False)


logger.addFilter(_ThreadSuppressionFilter())


@contextmanager
def suppress_logging():
    """Silence this thread's logging, for code that runs the pipeline speculatively.

    The CPU search simulates thousands of moves, many of them illegal on purpose;
    without this the pipeline's per-move debug and error lines flood the log.
    """
    previous = getattr(_suppression, "active", False)
    _suppression.active = True
    try:
        yield
    finally:
        _suppression.active = previous
