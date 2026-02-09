import time
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs request method, path, status code, and execution time
    """

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        response = await call_next(request)

        process_time = (time.time() - start_time) * 1000

        print(
            f"[{request.method}] {request.url.path} "
            f"→ {response.status_code} "
            f"({process_time:.2f} ms)"
        )

        return response
