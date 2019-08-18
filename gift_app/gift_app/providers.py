import argparse
import logging
import sys

from aiohttp import web
from injector import Module, provider, singleton

from .config import Config
from .middleware import error_middleware
from .storage import Storage
from .views import ImportsView


class ApplicationModule(Module):
    @singleton
    @provider
    def provide_config(self) -> Config:
        config = Config()
        parser = argparse.ArgumentParser()
        parser.add_argument("--config", type=open)
        args = parser.parse_args(sys.argv[2:])
        if args.config:
            config.read_from_file(args.config)
        return config

    @singleton
    @provider
    def provide_logger(self) -> logging.Logger:
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__package__)
        return logger

    @singleton
    @provider
    def provide_storage(self, config: Config) -> Storage:
        storage = Storage(config)
        return storage

    @singleton
    @provider
    def provide_app(
        self, config: Config, storage: Storage, imports_views: ImportsView
    ) -> web.Application:
        app = web.Application(middlewares=[error_middleware])
        app.router.add_routes([web.post("/imports", imports_views.import_citizens)])

        async def init_storage(app):
            await storage.initialize()

        app.on_startup.append(init_storage)
        return app
