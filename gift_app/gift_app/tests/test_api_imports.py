import datetime as dt
import pytest


@pytest.fixture
def imports_sample(citizen_ivan_sample, citizen_sergei_sample, citizen_maria_sample):
    d = {"citizens": [citizen_ivan_sample, citizen_sergei_sample, citizen_maria_sample]}
    return d


async def test_can_import_the_sample(http, imports_sample):
    """Пример импорта из задания работает нормально.
    """
    rv = await http.post("/imports", json=imports_sample)
    assert rv.status == 201, await rv.text()
    jsn = await rv.json()
    import_id = jsn["data"]["import_id"]
    assert import_id > 0


async def test_ivan_can_be_relative_to_himself(http, citizen_ivan_sample):
    """Житель может быть родственником сам себе.
    """
    # ARRANGE
    citizen_ivan_sample["relatives"][:] = [citizen_ivan_sample["citizen_id"]]
    data = {"citizens": [citizen_ivan_sample]}
    # ACT
    rv = await http.post("/imports", json=data)
    # ASSERT
    assert rv.status == 201, await rv.text()


async def test_cannot_have_a_missing_relative(http, citizen_ivan_sample):
    """У жителя не может быть родственника, которого нет в наборе.
    """
    # ARRANGE
    citizen_ivan_sample["relatives"][:] = [88]
    data = {"citizens": [citizen_ivan_sample]}
    # ACT
    rv = await http.post("/imports", json=data)
    # ASSERT
    assert rv.status == 400, await rv.text()
    jsn = await rv.json()
    assert "не найден родственник #88" in str(jsn["error"])


async def test_cannot_have_imagined_relative(
    http, citizen_ivan_sample, citizen_sergei_sample
):
    """Родственные связи должны быть двухсторонними.
    """
    # ARRANGE
    citizen_ivan_sample["relatives"][:] = [citizen_sergei_sample["citizen_id"]]
    citizen_sergei_sample["relatives"][:] = []
    data = {"citizens": [citizen_ivan_sample, citizen_sergei_sample]}
    # ACT
    rv = await http.post("/imports", json=data)
    # ASSERT
    assert rv.status == 400, await rv.text()
    jsn = await rv.json()
    assert "не признает" in str(jsn["error"])


async def test_cannot_have_invalid_gender(http, citizen_ivan_sample):
    """Нельзя указать неверный пол.
    """
    # ARRANGE
    citizen_ivan_sample["gender"] = "helicopter"
    data = {"citizens": [citizen_ivan_sample]}
    # ACT
    rv = await http.post("/imports", json=data)
    # ASSERT
    assert rv.status == 400, await rv.text()
    jsn = await rv.json()
    assert "gender" in str(jsn["error"])


async def test_cannot_have_invalid_birth_date(http, citizen_ivan_sample):
    """Нельзя указать неверную дату рождения.
    """
    # ARRANGE
    citizen_ivan_sample["birth_date"] = "29.02.2019"
    data = {"citizens": [citizen_ivan_sample]}
    # ACT
    rv = await http.post("/imports", json=data)
    # ASSERT
    assert rv.status == 400, await rv.text()
    jsn = await rv.json()
    assert "birth_date" in str(jsn["error"])


async def test_cannot_have_duplicated_relatives(
    http, citizen_ivan_sample, citizen_sergei_sample
):
    """Родственники одного жителя не могут повторятся.
    """
    # ARRANGE
    citizen_ivan_sample["relatives"].extend(citizen_ivan_sample["relatives"])
    data = {"citizens": [citizen_ivan_sample, citizen_sergei_sample]}
    # ACT
    rv = await http.post("/imports", json=data)
    # ASSERT
    assert rv.status == 400, await rv.text()
    jsn = await rv.json()
    assert "повторяются родственники" in str(jsn["error"])


async def test_cannot_have_duplicated_citizens(
    http, citizen_ivan_sample, citizen_sergei_sample
):
    """У каждого жителя одного набора должен быть уникальный citizen_id.
    """
    # ARRANGE
    citizen_ivan_sample["citizen_id"] = 1
    citizen_sergei_sample["citizen_id"] = 1
    data = {"citizens": [citizen_ivan_sample, citizen_sergei_sample]}
    # ACT
    rv = await http.post("/imports", json=data)
    # ASSERT
    assert rv.status == 400, await rv.text()
    jsn = await rv.json()
    assert "citizen_id жителей не могут повторяться" in str(jsn["error"])


async def test_cannot_have_negative_citizen_id(
    http, citizen_ivan_sample, citizen_sergei_sample
):
    """citizen_id должен быть неотрицателен.
    """
    # ARRANGE
    citizen_ivan_sample["citizen_id"] = -1
    citizen_sergei_sample["relatives"] = [-1]
    data = {"citizens": [citizen_ivan_sample, citizen_sergei_sample]}
    # ACT
    rv = await http.post("/imports", json=data)
    # ASSERT
    assert rv.status == 400, await rv.text()
    jsn = await rv.json()
    assert "citizen_id" in str(jsn["error"])


async def test_cannot_have_birth_date_in_future(
    http, citizen_ivan_sample, citizen_sergei_sample
):
    """Дата рождение не может быть в будущем.
    """
    # ARRANGE
    citizen_ivan_sample["birth_date"] = (
        dt.date.today() + dt.timedelta(days=1)
    ).strftime("%d.%m.%Y")
    data = {"citizens": [citizen_ivan_sample, citizen_sergei_sample]}
    # ACT
    rv = await http.post("/imports", json=data)
    # ASSERT
    assert rv.status == 400, await rv.text()
    jsn = await rv.json()
    assert "birth_date" in str(jsn["error"])
