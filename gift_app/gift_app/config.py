from dataclasses import dataclass, field

from environs import Env

from .utils import merge_dicts


@dataclass
class DbConfig:
    name: str
    username: str
    host: str
    port: int
    password: str = field(repr=False)


class Config:
    """Конфиг приложения.
    """

    db: DbConfig

    def __init__(self, overrides=None):
        self._env_config_vars = self._read_env()
        self._overrides = overrides or {}
        self._update()

    def __repr__(self):
        return f"<Config db={self.db!r}>"

    def _update(self):
        config_vars = merge_dicts(self._env_config_vars, self._overrides)
        self.db = DbConfig(**config_vars["db"])

    def _read_env(self) -> dict:
        env = Env()
        env.read_env()
        with env.prefixed("GIFT_APP_"):
            with env.prefixed("DB_"):
                config_vars = {
                    "db": {
                        "name": env("NAME"),
                        "host": env("HOST"),
                        "username": env("USERNAME"),
                        "password": env("PASSWORD", None),
                        "port": env.int("PORT", 5432),
                    }
                }
                return config_vars
