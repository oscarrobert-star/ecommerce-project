import logging

logger = logging.getLogger(__name__)

class DebugAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log minimal request details without sensitive headers/cookies
        
        # logger.debug("=== Incoming Request ===")
        # logger.debug(f"Path: {request.path}")
        # logger.debug(f"Method: {request.method}")
        
        # --- Logging sensitive headers is now skipped ---
        # for header, value in request.headers.items():
        #     if header.lower() in ['authorization', 'cookie']:
        #         # We skip logging the value for sensitive headers
        #         logger.debug(f"  {header}: {'[REDACTED]'}")
        #     else:
        #         logger.debug(f"  {header}: {value}")
        
        response = self.get_response(request)
        return response