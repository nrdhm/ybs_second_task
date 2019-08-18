from aiohttp import web
from injector import Injector

from .providers import ApplicationModule


async def init_func(argv=[], extra_modules=[]):
    injector = Injector(modules=[ApplicationModule, *extra_modules])
    app = injector.get(web.Application)
    return app
