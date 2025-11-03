import logging

logger = logging.getLogger(__name__)

class DebugAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log incoming request details
        logger.debug("=== Incoming Request ===")
        logger.debug(f"Path: {request.path}")
        logger.debug(f"Method: {request.method}")
        logger.debug("Headers:")
        for header, value in request.headers.items():
            if header.lower() in ['authorization', 'cookie']:
                logger.debug(f"  {header}: {value}")
        
        logger.debug("Cookies:")
        for cookie, value in request.COOKIES.items():
            if 'token' in cookie.lower():
                logger.debug(f"  {cookie}: {'Present' if value else 'Missing'}")

        response = self.get_response(request)
        return response