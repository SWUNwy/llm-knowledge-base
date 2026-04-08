"""重试工具模块

提供指数退避重试功能
"""

import asyncio
import functools
import logging
import random
from typing import Any, Callable, Tuple, Type

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """指数退避重试装饰器

    在遇到指定异常时自动重试，使用指数退避策略增加重试间隔。

    Args:
        max_retries: 最大重试次数，默认3次
        base_delay: 基础延迟时间（秒），默认1.0秒
        max_delay: 最大延迟时间（秒），默认30.0秒
        exponential_base: 指数基数，默认2.0
        exceptions: 需要重试的异常类型元组，默认所有异常

    Returns:
        装饰器函数

    Example:
        @retry_with_backoff(max_retries=3, base_delay=1.0)
        async def fetch_data():
            # 可能失败的操作
            pass
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Exception | None = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        # 计算延迟时间（指数退避 + 随机抖动）
                        delay = min(
                            base_delay * (exponential_base**attempt)
                            + random.uniform(0, 0.1 * base_delay),
                            max_delay,
                        )
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.2f} seconds..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_retries + 1} attempts failed for {func.__name__}"
                        )

            # 所有重试都失败了，抛出最后一个异常
            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected state in retry logic")

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Exception | None = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        # 计算延迟时间（指数退避 + 随机抖动）
                        delay = min(
                            base_delay * (exponential_base**attempt)
                            + random.uniform(0, 0.1 * base_delay),
                            max_delay,
                        )
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.2f} seconds..."
                        )
                        import time

                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_retries + 1} attempts failed for {func.__name__}"
                        )

            # 所有重试都失败了，抛出最后一个异常
            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected state in retry logic")

        # 根据函数类型选择包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
