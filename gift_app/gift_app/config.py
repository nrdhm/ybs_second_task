import os
import yaml
from dataclasses import dataclass
from typing import TextIO
from functools import reduce


@dataclass
class DbConfig:
    name: str
    password: str
    username: str
    host: str


class Config:
    """Конфиг приложения.

    Может прочитать конфиг из yaml файла или переменных окружения.
    Переменные окружения перезаписывают все остальные.
    """

    db: DbConfig

    def __init__(self, overrides=None):
        self._default_config_vars = _DEFAULT_CONFIG_VARS
        self._file_config_vars = {}
        self._env_config_vars = self._read_env()
        self._overrides = overrides or {}

        self._update()

    def read_from_file(self, file: TextIO) -> "Config":
        self._file_config_vars = yaml.safe_load(file)
        self._update()
        return self

    def _update(self):
        config_vars = merge_dicts(
            self._default_config_vars,
            self._file_config_vars,
            self._env_config_vars,
            self._overrides,
        )
        self.db = DbConfig(**config_vars["db"])

    def _read_env(self) -> dict:
        env_vars = {
            k.lstrip("GIFT_APP_"): v
            for k, v in os.environ.items()
            if k.startswith("GIFT_APP_")
        }
        config_vars = {
            "db": {
                k.lstrip("DB_"): v for k, v in env_vars.items() if k.startswith("DB")
            }
        }
        return config_vars


_DEFAULT_CONFIG_VARS = {
    "db": {
        "name": "postgres",
        "password": "postgres",
        "username": "postgres",
        "host": "localhost,",
    }
}


missing = object()


def merge_dicts(*dicts):
    def merge(a: dict, b: dict) -> dict:
        m = {}
        for key in a.keys() | b.keys():
            a_val = a.get(key, missing)
            b_val = b.get(key, missing)
            # Хотя бы одно из них должно присутствовать.
            assert not (a_val is missing and b_val is missing)
            if isinstance(b_val, dict) or isinstance(a_val, dict):
                if b_val is missing:
                    b_val = {}
                if a_val is missing:
                    a_val = {}
                m[key] = merge(a_val, b_val)
                continue
            m[key] = b_val if b_val is not missing else a_val
        return m

    d = reduce(merge, dicts, {})
    return d
