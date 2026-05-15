import logging
import time

logger = logging.getLogger("api.requests")


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.perf_counter()
        response = self.get_response(request)
        duration_ms = (time.perf_counter() - start) * 1000
        user_id = getattr(getattr(request, "user", None), "pk", None)
        logger.info(
            "%s %s %s %.1fms user=%s",
            request.method,
            request.path,
            response.status_code,
            duration_ms,
            user_id or "anon",
        )
        return response
