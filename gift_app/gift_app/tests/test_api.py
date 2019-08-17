import pytest
from gift_app.config import Config
from gift_app.main import init_func


@pytest.fixture
def imports_sample():
    d = {
        'citizens': [
            {
                'citizen_id': 1,
                'town': 'Москва',
                'street': 'Льва Толстого',
                'building': '16к7стр5',
                'apartment': 7,
                'name': 'Иванов Иван Иванович',
                'birth_date': '26.12.1986',
                'gender': 'male',
                'relatives': [2],  # id родственников
            },
            {
                'citizen_id': 2,
                'town': 'Москва',
                'street': 'Льва Толстого',
                'building': '16к7стр5',
                'apartment': 7,
                'name': 'Иванов Сергей Иванович',
                'birth_date': '01.04.1997',
                'gender': 'male',
                'relatives': [1],
            },
            {
                'citizen_id': 3,
                'town': 'Керчь',
                'street': 'Иосифа Бродского',
                'building': '2',
                'apartment': 11,
                'name': 'Романова Мария Леонидовна',
                'birth_date': '23.11.1986',
                'gender': 'female',
                'relatives': [],
            },
        ]
    }
    return d


@pytest.fixture
def config():
    db_config = {'name': 'test_db', 'username': 'postgres', 'password': None}
    config = Config({'db': db_config})
    return config


@pytest.fixture
async def http(loop, aiohttp_client, config):
    app = await init_func([], config=config)
    return await aiohttp_client(app)


async def test_foo(http, imports_sample):
    rv = await http.post('/imports', json=imports_sample)
    assert rv.status == 201, await rv.json()
    jsn = await rv.json()
    import_id = jsn['data']['import_id']
    assert import_id > 0
