import pytest


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
def imports_sample(citizen_ivan_sample, citizen_sergei_sample, citizen_maria_sample):
    d = {"citizens": [citizen_ivan_sample, citizen_sergei_sample, citizen_maria_sample]}
    return d


async def test_can_import_the_sample(http, imports_sample):
    rv = await http.post("/imports", json=imports_sample)
    assert rv.status == 201, await rv.text()
    jsn = await rv.json()
    import_id = jsn["data"]["import_id"]
    assert import_id > 0


async def test_ivan_can_be_relative_to_himself(http, citizen_ivan_sample):
    # ARRANGE
    citizen_ivan_sample["relatives"][:] = [citizen_ivan_sample["citizen_id"]]
    data = {"citizens": [citizen_ivan_sample]}
    # ACT
    rv = await http.post("/imports", json=data)
    # ASSERT
    assert rv.status == 201, await rv.text()


async def test_cannot_have_a_missing_relative(http, citizen_ivan_sample):
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
    # ARRANGE
    citizen_ivan_sample["relatives"][:] = [citizen_sergei_sample["citizen_id"]]
    citizen_sergei_sample["relatives"][:] = []
    data = {"citizens": [citizen_ivan_sample, citizen_sergei_sample]}
    # ACT
    rv = await http.post("/imports", json=data)
    # ASSERT
    assert rv.status == 400, await rv.text()
    jsn = await rv.json()
    assert "не признал" in str(jsn["error"])
