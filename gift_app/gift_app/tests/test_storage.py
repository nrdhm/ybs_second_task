import pytest
import datetime as dt
from gift_app.storage import Storage
from gift_app.models import Citizen, Gender


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


async def test_can_save_citizen(storage: Storage, citizen_ivan: Citizen):
    import_id = 1
    ok = await storage.save_citizen(import_id, citizen_ivan)
    assert ok
    saved_citizen = await storage.retrieve_citizen(import_id, citizen_ivan.citizen_id)
    assert saved_citizen == citizen_ivan
