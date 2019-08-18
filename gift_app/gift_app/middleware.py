from aiohttp import web
from marshmallow import ValidationError

from .errors import InvalidUsage


@web.middleware
async def error_middleware(request, handler):
    try:
        response = await handler(request)
        return response
    except ValidationError as exc:
        return web.json_response({"error": exc.normalized_messages()}, status=400)
    except InvalidUsage as exc:
        return web.json_response({"error": exc.message}, status=exc.status_code)
