import time
import functools
import traceback
from ..core.logging import logger


def monitor_performance(operation_name):
    """性能监控装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            # 更智能地获取request_id
            request_id = kwargs.get('request_id', 'unknown')
            if request_id == 'unknown' and len(args) > 0:
                # 尝试从参数中找到request_id
                for arg in args:
                    if isinstance(arg, str) and len(arg) == 36 and '-' in arg:
                        request_id = arg
                        break
            
            logger.debug(
                f"开始 {operation_name}",
                request_id=request_id
            )
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(
                    f"{operation_name} 完成",
                    request_id=request_id,
                    耗时=f"{duration:.3f}s"
                )
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                logger.error(
                    f"{operation_name} 失败: {str(e)}",
                    request_id=request_id,
                    error_type=type(e).__name__,
                    耗时=f"{duration:.3f}s",
                    stack_trace=traceback.format_exc()
                )
                raise
        return wrapper
    return decorator


def monitor_async_performance(operation_name):
    """异步性能监控装饰器"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            # 更智能地获取request_id
            request_id = kwargs.get('request_id', 'unknown')
            if request_id == 'unknown' and len(args) > 0:
                # 尝试从参数中找到request_id
                for arg in args:
                    if isinstance(arg, str) and len(arg) == 36 and '-' in arg:
                        request_id = arg
                        break
            
            logger.debug(
                f"开始 {operation_name}",
                request_id=request_id
            )
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(
                    f"{operation_name} 完成",
                    request_id=request_id,
                    耗时=f"{duration:.3f}s"
                )
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                logger.error(
                    f"{operation_name} 失败: {str(e)}",
                    request_id=request_id,
                    error_type=type(e).__name__,
                    耗时=f"{duration:.3f}s",
                    stack_trace=traceback.format_exc()
                )
                raise
        return wrapper
    return decorator 