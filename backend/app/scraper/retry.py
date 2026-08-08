import time
import logging
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)

def retry(max_retries: int = 3, base_delay: int = 5, exceptions: tuple = (Exception,)):
    """
    Retry decorator with exponential back-off.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries == max_retries:
                        logger.error(
                            f"Max retries ({max_retries}) reached for {func.__name__}. Error: {e}",
                            extra={"extra_info": {"function": func.__name__, "error": str(e)}}
                        )
                        raise
                    
                    delay = base_delay * (2 ** (retries - 1))
                    logger.warning(
                        f"Attempt {retries}/{max_retries} failed for {func.__name__}: {e}. Retrying in {delay}s...",
                        extra={"extra_info": {"function": func.__name__, "error": str(e), "retry": retries}}
                    )
                    time.sleep(delay)
        return wrapper
    return decorator
