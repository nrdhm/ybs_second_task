import asyncio
import datetime as dt
import logging
from contextlib import asynccontextmanager
from unittest.mock import MagicMock

import asyncpg.connection
import asyncpgsa
import pytest
from injector import Binder

from gift_app.config import Config
from gift_app.main import init_func
from gift_app.models import Citizen, Gender
from gift_app.storage import Storage, create_tables


@pytest.fixture(scope="session")
def config():
    db_config = {"name": "test_db", "username": "postgres", "password": None}
    config = Config({"db": db_config})
    return config


@pytest.fixture(scope="session")
def test_db(config):
    """Подготовка тестовой БД.
    """

    async def go():
        pool = await asyncpgsa.create_pool(dsn=db_url(config, "postgres"))
        async with pool.acquire() as conn:  # type: asyncpg.connection.Connection
            # скидываем левые соединения к тестовой базе данных
            await conn.execute(
                """SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = 'test_db'"""
            )
            await conn.execute("DROP DATABASE IF EXISTS test_db")
            await conn.execute("CREATE DATABASE test_db")
        await pool.close()

        pool = await asyncpgsa.create_pool(dsn=db_url(config, "test_db"))
        async with pool.acquire() as conn:  # type: asyncpg.connection.Connection
            await create_tables(conn)

    asyncio.run(go())


@pytest.fixture
async def storage(loop, config, test_db, logger):
    """Замоканное хранилище, не сохраняющее данные между тестами.
    """
    x = Storage(config, logger)
    await x.initialize()
    async with x.pool.acquire() as conn:
        tx = conn.transaction()
        await tx.start()
        try:

            @asynccontextmanager
            async def transaction_mock(*x):
                yield conn

            @asynccontextmanager
            async def acquire_mock(*x):
                yield conn

            async def initialize_mock(*x):
                return

            x.initialize = MagicMock(x.initialize, side_effect=initialize_mock)
            x._pool = MagicMock(x._pool)
            x._pool.transaction.side_effect = transaction_mock
            x._pool.acquire.side_effect = acquire_mock

            yield x
        finally:
            await tx.rollback()


@pytest.fixture
async def app(loop, test_db, config, storage):
    def configuraiton(binder: Binder):
        binder.bind(Config, config)
        binder.bind(Storage, storage)

    app = await init_func([], extra_modules=[configuraiton])
    return app


@pytest.fixture
async def http(loop, aiohttp_client, app):
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
def logger():
    return logging.getLogger(__package__)


@pytest.fixture
def citizen_ivan_sample():
    d = {
        "citizen_id": 1,
        "town": "Москва",
        "street": "Льва Толстого",
        "building": "16к7стр5",
        "apartment": 7,
        "name": "Иванов Иван Иванович",
        "birth_date": "26.12.1986",
        "gender": "male",
        "relatives": [2],  # id родственников
    }
    return d


@pytest.fixture
def citizen_sergei_sample():
    return {
        "citizen_id": 2,
        "town": "Москва",
        "street": "Льва Толстого",
        "building": "16к7стр5",
        "apartment": 7,
        "name": "Иванов Сергей Иванович",
        "birth_date": "01.04.1997",
        "gender": "male",
        "relatives": [1],
    }


@pytest.fixture
def citizen_maria_sample():
    return {
        "citizen_id": 3,
        "town": "Керчь",
        "street": "Иосифа Бродского",
        "building": "2",
        "apartment": 11,
        "name": "Романова Мария Леонидовна",
        "birth_date": "23.11.1986",
        "gender": "female",
        "relatives": [],
    }


@pytest.fixture
def citizen_ivan():
    x = Citizen(
        citizen_id=1,
        town="Москва",
        street="Льва Толстого",
        building="16к7стр5",
        apartment=7,
        name="Иванов Иван Иванович",
        birth_date=dt.date(1986, 12, 26),
        gender=Gender.male,
        relatives=[],
    )
    return x


@pytest.fixture
def citizen_sergei():
    x = Citizen(
        citizen_id=2,
        town="Москва",
        street="Льва Толстого",
        building="16к7стр5",
        apartment=7,
        name="Иванов Сергей Иванович",
        birth_date=dt.date(1997, 4, 1),
        gender=Gender.male,
        relatives=[],
    )
    return x


@pytest.fixture
def citizen_maria():
    x = Citizen(
        citizen_id=3,
        town="Керчь",
        street="Иосифа Бродского",
        building="2",
        apartment=11,
        name="Романова Мария Леонидовна",
        birth_date=dt.date(1986, 11, 23),
        gender=Gender.female,
        relatives=[],
    )
    return x


@pytest.fixture
async def first_citizens(citizen_ivan, citizen_sergei, citizen_maria):
    citizen_ivan.relatives = [citizen_sergei.citizen_id]
    citizen_sergei.relatives = [citizen_ivan.citizen_id]
    return [citizen_ivan, citizen_sergei, citizen_maria]


@pytest.fixture
async def import_batch_first(storage, first_citizens):
    import_id = await storage.import_citizens(first_citizens)
    return import_id


@pytest.fixture
async def second_citizens(citizen_ivan, citizen_sergei, citizen_maria):
    """У Марии из этого набора день рождения в апреле.
    """
    citizen_maria.birth_date = citizen_maria.birth_date.replace(month=4)
    citizen_maria.relatives = [citizen_ivan.citizen_id]
    citizen_ivan.relatives = [citizen_sergei.citizen_id, citizen_maria.citizen_id]
    citizen_sergei.relatives = [citizen_ivan.citizen_id]
    return [citizen_ivan, citizen_sergei, citizen_maria]


@pytest.fixture
async def import_batch_second(storage, second_citizens):
    import_id = await storage.import_citizens(second_citizens)
    return import_id


@pytest.fixture
async def married_ivan_and_maria(
    import_batch_first, citizen_ivan, citizen_maria, citizen_sergei, storage: Storage
):
    import_id = import_batch_first
    update = {
        "name": "Иванова Мария Леонидовна",
        "town": "Москва",
        "street": "Льва Толстого",
        "building": "16к7стр5",
        "apartment": 7,
        "relatives": [1],
    }
    await storage.update_citizen(import_id, citizen_maria.citizen_id, update)
    citizen_ivan = await storage.retrieve_citizen(import_id, citizen_ivan.citizen_id)
    citizen_maria = await storage.retrieve_citizen(import_id, citizen_maria.citizen_id)
    citizen_sergei = await storage.retrieve_citizen(
        import_id, citizen_sergei.citizen_id
    )
    # ASSERT
    # Иван и Мария теперь родня.
    assert citizen_ivan.citizen_id in citizen_maria.relatives
    assert citizen_maria.citizen_id in citizen_ivan.relatives
    # Сергей и Иван также все еще братья.
    assert citizen_sergei.citizen_id in citizen_ivan.relatives
    assert citizen_ivan.citizen_id in citizen_sergei.relatives
