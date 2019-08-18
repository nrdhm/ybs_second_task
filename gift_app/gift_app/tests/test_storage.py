import datetime as dt
from typing import List, Tuple

import pytest

from gift_app.models import Citizen, Gender, ImportMessage
from gift_app.storage import Storage


@pytest.fixture
async def storage(loop, config, test_db):
    x = Storage(config)
    await x.initialize()
    return x


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
def brother_citizens(citizen_ivan, citizen_sergei):
    citizen_ivan.relatives = [citizen_sergei]
    citizen_sergei.relatives = [citizen_ivan]
    return [citizen_ivan, citizen_sergei]


async def test_can_save_citizen(storage: Storage, citizen_ivan: Citizen):
    import_id = 1
    ok = await storage.save_citizen(import_id, citizen_ivan)
    assert ok
    saved_citizen = await storage.retrieve_citizen(import_id, citizen_ivan.citizen_id)
    assert saved_citizen == citizen_ivan


async def test_can_import_citizens(storage: Storage, brother_citizens: List[Citizen]):
    import_message = ImportMessage(citizens=brother_citizens)
    import_id = await storage.import_citizens(import_message)
    assert import_id > 0


@pytest.fixture
async def imported_brothers(storage, brother_citizens):
    import_message = ImportMessage(citizens=brother_citizens)
    import_id = await storage.import_citizens(import_message)
    return import_id


async def test_can_retrieve_relatives(
    storage: Storage, imported_brothers: int, brother_citizens: List[Citizen]
):
    one, two = brother_citizens
    relatives = await storage.retrieve_citizen_relatives(
        imported_brothers, one.citizen_id
    )
    assert len(relatives) == 1, relatives
    relative = relatives[0]
    assert two.citizen_id == relative.citizen_id
