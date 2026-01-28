import logging
import time
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('http')


class RequestResponseLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log detailed HTTP request and response information.
    Helps debug issues like URLconf errors and template rendering problems.
    """

    def process_request(self, request):
        """Log incoming request details."""
        request._start_time = time.time()

        logger.info(
            f"Request started: {request.method} {request.path} | "
            f"User: {request.user if hasattr(request, 'user') else 'Anonymous'} | "
            f"IP: {self.get_client_ip(request)}"
        )

        # Log query parameters if present
        if request.GET:
            logger.debug(f"Query params: {dict(request.GET)}")

        return None

    def process_response(self, request, response):
        """Log response details including timing."""
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            logger.info(
                f"Request completed: {request.method} {request.path} | "
                f"Status: {response.status_code} | "
                f"Duration: {duration:.3f}s"
            )

        return response

    def process_exception(self, request, exception):
        """Log exceptions that occur during request processing."""
        logger.error(
            f"Request exception: {request.method} {request.path} | "
            f"User: {request.user if hasattr(request, 'user') else 'Anonymous'} | "
            f"Exception: {type(exception).__name__}: {str(exception)}",
            exc_info=True
        )
        return None

    @staticmethod
    def get_client_ip(request):
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
