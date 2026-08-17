"""Cross-cutting decorators used across the scheduler.

log_execution wraps a function to log its start, finish, duration,
and outcome -- used to wrap Executor.run so every job execution
attempt is logged consistently without Executor.run itself containing
any logging code.
"""

import functools
import logging
import time
from typing import Any, Callable, TypeVar

logger = logging.getLogger("job_scheduler")
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

F = TypeVar("F", bound=Callable[..., Any])


def log_execution(func: F) -> F:

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        logger.info("Starting %s", func.__qualname__)
        try:
            result = func(*args, **kwargs)
        except Exception:
            elapsed = time.perf_counter() - start
            logger.warning("%s raised after %.3fs", func.__qualname__, elapsed)
            raise
        else:
            elapsed = time.perf_counter() - start
            logger.info("Finished %s in %.3fs", func.__qualname__, elapsed)
            return result

    return wrapper  # type: ignore[return-value]