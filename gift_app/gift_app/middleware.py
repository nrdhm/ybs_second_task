import logging
from aiohttp import web
from marshmallow import ValidationError

from .errors import InvalidUsage


def create_error_middleware(logger: logging.Logger):
    @web.middleware
    async def error_middleware(request, handler):
        try:
            response = await handler(request)
            return response
        except ValidationError as exc:
            return web.json_response({"error": exc.normalized_messages()}, status=400)
        except InvalidUsage as exc:
            return web.json_response({"error": exc.message}, status=exc.status_code)
        except Exception as exc:
            logger.exception(exc)
            return web.json_response({"error": "Server got itself in trouble"}, status=500)

    return error_middleware
