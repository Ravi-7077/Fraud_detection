import time
import functools
from typing import Callable, TypeVar, Any

from fraud_detection.config import load_config

T = TypeVar('T')

def circuit_breaker(max_retries: int | None = None):
    """Simple circuit breaker decorator.

    Retries the wrapped function up to ``max_retries`` times (default from config).
    If all attempts fail, raises a RuntimeError.
    """
    config = load_config()
    default_retries = config.get('circuit_breaker', {}).get('max_retries', 3)
    effective_retries = max_retries if max_retries is not None else default_retries

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            attempts = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    attempts += 1
                    if attempts > effective_retries:
                        raise RuntimeError(f"Circuit breaker: {func.__name__} failed after {effective_retries} retries") from exc
                    time.sleep(0.1)  # brief back‑off
        return wrapper
    return decorator
