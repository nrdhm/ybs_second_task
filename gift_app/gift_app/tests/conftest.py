import aiopg.sa
import pytest

from gift_app.config import Config
from gift_app.main import init_func
from gift_app.storage import create_tables


@pytest.fixture
def config():
    db_config = {"name": "test_db", "username": "postgres", "password": None}
    config = Config({"db": db_config})
    return config


@pytest.fixture
async def http(loop, aiohttp_client, config):
    app = await init_func([], config=config)
    return await aiohttp_client(app)


def db_url(config, db_name):
    DSN = "postgresql://{username}:{password}@{host}/{db_name}"
    url = DSN.format(
        username=config.db.username,
        password=config.db.password,
        host=config.db.host,
        db_name=db_name,
    )
    return url


@pytest.fixture
async def test_db(loop, config):
    async with aiopg.sa.create_engine(db_url(config, "postgres")) as engine:
        async with engine.acquire() as conn:
            # скидываем левые соединения к тестовой базе данных
            await conn.execute(
                """SELECT pg_terminate_backend(pg_stat_activity.pid)
                   FROM pg_stat_activity
                   WHERE pg_stat_activity.datname = 'test_db'"""
            )
            await conn.execute("DROP DATABASE IF EXISTS test_db")
            await conn.execute("CREATE DATABASE test_db")

        async with aiopg.sa.create_engine(db_url(config, "test_db")) as test_engine:
            await create_tables(test_engine)
            yield test_engine
