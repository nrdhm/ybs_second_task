import argparse
import logging
import sys

from aiohttp import web
from injector import Module, provider, singleton

from .config import Config
from .middleware import create_error_middleware
from .storage import Storage
from .views import ImportsView


class ApplicationModule(Module):
    @singleton
    @provider
    def provide_config(self, logger: logging.Logger) -> Config:
        config = Config()
        parser = argparse.ArgumentParser()
        parser.add_argument("--config", type=open)
        args, _ = parser.parse_known_args(sys.argv)
        if args.config:
            config.read_from_file(args.config)
        logger.info(config)
        return config

    @singleton
    @provider
    def provide_logger(self) -> logging.Logger:
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__package__)
        return logger

    @singleton
    @provider
    def provide_storage(self, config: Config, logger: logging.Logger) -> Storage:
        storage = Storage(config, logger)
        return storage

    @singleton
    @provider
    def provide_app(
        self, config: Config, storage: Storage, logger: logging.Logger, imports_views: ImportsView,
    ) -> web.Application:
        app = web.Application(middlewares=[create_error_middleware(logger)])
        app.router.add_routes([web.post("/imports", imports_views.import_citizens)])

        async def init_storage(app):
            await storage.initialize()

        app.on_startup.append(init_storage)
        return app
