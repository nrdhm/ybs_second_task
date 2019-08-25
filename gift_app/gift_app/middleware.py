import logging
import inspect

from aiohttp import web
from marshmallow import ValidationError

from .errors import InvalidUsage


def create_error_middleware(logger: logging.Logger):
    @web.middleware
    async def error_middleware(request: web.Request, handler):
        try:
            response = await handler(request)
            return response
        except ValidationError as exc:
            return web.json_response({"error": exc.normalized_messages()}, status=400)
        except InvalidUsage as exc:
            return web.json_response({"error": exc.message}, status=exc.status_code)
        except web.HTTPError as exc:
            return web.json_response({"error": exc.reason}, status=exc.status_code)
        except Exception as exc:
            logger.info("error headers start")
            logger.info(request.headers)
            logger.info("error headers end")

            logger.info("error content start")
            logger.info(await request.read())
            logger.info("error content end")

            logger.info("error locals start")
            vars = inspect.trace()[-1][0].f_locals
            logger.info(vars)
            logger.info("error locals end")

            logger.exception(exc)

            return web.json_response(
                {"error": "Server got itself in trouble"}, status=500
            )

    return error_middleware
