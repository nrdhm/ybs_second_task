import json
from aiohttp import web
from functools import wraps


def expect_json_body(view_function):
    """Декоратор для валидации входных данных на соответствие json формату.
    """
    @wraps(view_function)
    async def view_function_wrapper(self, request: web.Request):
        try:
            # aiohttp обещает возвращать те же данные при повторных
            # вызовах web.Request.json()
            # https://docs.aiohttp.org/en/stable/web_reference.html#aiohttp.web.BaseRequest.json
            await request.json()
            return await view_function(self, request)
        except json.decoder.JSONDecodeError as exc:
            self.logger.exception(exc)
            return web.json_response(
                {"error": "Expecting a valid json body. Try again."}, status=400
            )

    return view_function_wrapper
