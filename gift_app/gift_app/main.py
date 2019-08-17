import argparse
import logging

from aiohttp import web

from .views import routes
from .config import Config
from .storage import Storage

parser = argparse.ArgumentParser()
parser.add_argument("--config", type=open)


async def init_func(argv, config=None):
    if not config:
        args = parser.parse_args(argv)
        config = Config()
        if args.config:
            config.read_from_file(args.config)

    logging.basicConfig(level=logging.INFO)

    logging.info(config)

    storage = Storage(config)
    await storage.initialize()

    app = web.Application()
    app["config"] = config
    app["storage"] = storage
    app.add_routes(routes)
    return app
