import pytest

from gift_app.models import Citizen


async def test_can_update_citizen(
    http, citizen_maria: Citizen, import_batch_first: int
):
    """Можно обновить инфу о жителе.
    """
    # ARRANGE
    import_id = import_batch_first
    citizen_id = citizen_maria.citizen_id
    data = {
        "name": "Иванова Мария Леонидовна",
        "town": "Москва",
        "street": "Льва Толстого",
        "building": "16к7стр5",
        "apartment": 7,
        "relatives": [1],
    }
    # ACT
    rv = await http.patch(f"/imports/{import_id}/citizens/{citizen_id}", json=data)
    # ASSERT
    assert rv.status == 200, await rv.json()
    jsn = await rv.json()
    assert jsn == {
        "data": {
            "citizen_id": 3,
            "town": "Москва",
            "street": "Льва Толстого",
            "building": "16к7стр5",
            "apartment": 7,
            "name": "Иванова Мария Леонидовна",
            "birth_date": "23.11.1986",
            "gender": "female",
            "relatives": [1],
        }
    }


async def test_cannot_send_invalid_relatives(
    http, citizen_maria: Citizen, import_batch_first: int
):
    """Нельзя отправить айди несуществющих в наборе жителей в качестве родственников.
    """
    # ARRANGE
    import_id = import_batch_first
    citizen_id = citizen_maria.citizen_id
    data = {"relatives": [4]}
    # ACT
    rv = await http.patch(f"/imports/{import_id}/citizens/{citizen_id}", json=data)
    # ASSERT
    assert rv.status == 400, await rv.json()


async def test_relative_clean_bidirectional(
    http, citizen_ivan: Citizen, citizen_sergei: Citizen, import_batch_first: int
):
    """Удаление родственных связей должно быть двусторонним.
    """
    # ARRANGE
    import_id = import_batch_first
    citizen_id = citizen_ivan.citizen_id
    data = {"relatives": []}
    # ACT
    rv = await http.patch(f"/imports/{import_id}/citizens/{citizen_id}", json=data)
    # ASSERT
    assert rv.status == 200, await rv.json()
    jsn = await rv.json()
    assert not jsn["data"]["relatives"]


async def test_maria_can_divorce(
    http,
    import_batch_first,
    married_ivan_and_maria,
    citizen_maria,
    citizen_sergei,
    citizen_ivan,
    storage,
):
    """Чисто гипотетически, Мария может развестись с Иваном.
    """
    # ARRANGE
    import_id = import_batch_first
    data = {"relatives": []}
    # ACT
    rv = await http.patch(
        f"/imports/{import_id}/citizens/{citizen_maria.citizen_id}", json=data
    )
    # ASSERT
    assert rv.status == 200, await rv.json()
    jsn = await rv.json()
    assert jsn == {
        "data": {
            "citizen_id": 3,
            "town": "Москва",
            "street": "Льва Толстого",
            "building": "16к7стр5",
            "apartment": 7,
            "name": "Иванова Мария Леонидовна",
            "birth_date": "23.11.1986",
            "gender": "female",
            "relatives": [],
        }
    }
