import time
import uuid
from .logging import logger


class RequestTrackingMiddleware:
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # 生成唯一请求ID
            request_id = str(uuid.uuid4())
            start_time = time.time()
            
            # 获取基本请求信息
            method = scope.get("method", "UNKNOWN")
            path = scope.get("path", "unknown")
            client_info = scope.get("client", ("unknown", 0))
            client_ip = client_info[0] if client_info else "unknown"
            
            # 记录请求开始
            logger.info(
                f"Request started: {method} {path}",
                request_id=request_id,
                path=path,
                method=method,
                client_ip=client_ip
            )
            
            # 将request_id添加到scope中，以便在路由中使用
            scope["request_id"] = request_id
            
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    # 记录响应状态
                    status_code = message["status"]
                    duration = time.time() - start_time
                    
                    logger.info(
                        f"Request completed: {method} {path} - Status: {status_code}",
                        request_id=request_id,
                        path=path,
                        status=status_code,
                        duration=f"{duration:.3f}s"
                    )
                
                await send(message)
            
            try:
                await self.app(scope, receive, send_wrapper)
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Request failed: {method} {path} - Error: {str(e)}",
                    request_id=request_id,
                    path=path,
                    error_type=type(e).__name__,
                    duration=f"{duration:.3f}s"
                )
                raise
        else:
            await self.app(scope, receive, send) 