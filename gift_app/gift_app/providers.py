import logging
import logging.config

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
        return config

    @singleton
    @provider
    def provide_logger(self) -> logging.Logger:
        logging.config.dictConfig(
            {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "default": {
                        "format": "[%(asctime)s][%(levelname)s] %(name)s %(filename)s:%(funcName)s:%(lineno)d | %(message)s"
                    }
                },
                "handlers": {
                    "main": {"class": "logging.StreamHandler", "formatter": "default"}
                },
                "root": {"level": "INFO", "handlers": ["main"]},
            }
        )
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
        self,
        config: Config,
        storage: Storage,
        logger: logging.Logger,
        imports_views: ImportsView,
    ) -> web.Application:
        logger.info(config)
        app = web.Application(
            middlewares=[create_error_middleware(logger)], logger=logger
        )
        app.router.add_routes(
            [
                web.post("/imports", imports_views.import_citizens),
                web.get(
                    "/imports/{import_id:\d+}/citizens", imports_views.list_citizens
                ),
                web.patch(
                    "/imports/{import_id:\d+}/citizens/{citizen_id:\d+}",
                    imports_views.update_citizen,
                ),
                web.get(
                    "/imports/{import_id:\d+}/citizens/birthdays",
                    imports_views.list_birthdays,
                ),
                web.get(
                    "/imports/{import_id:\d+}/towns/stat/percentile/age",
                    imports_views.retrieve_age_stats,
                ),
                web.get("/version", imports_views.retrieve_version),
            ]
        )

        async def init_storage(app):
            await storage.initialize()

        app.on_startup.append(init_storage)
        return app
