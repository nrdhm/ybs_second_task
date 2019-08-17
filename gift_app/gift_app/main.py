import argparse

from aiohttp import web

from .views import routes
from .config import Config

parser = argparse.ArgumentParser()
parser.add_argument("--config", type=open)


async def init_func(argv, config=None):
    if not config:
        args = parser.parse_args(argv)
        config = Config()
        if args.config:
            config.read_from_file(args.config)

    app = web.Application()
    app["config"] = config
    app.add_routes(routes)
    return app
