async def test_can_list_citizens(http, import_batch_first, married_ivan_and_maria):
    """Можно получить список жителей.
    """
    # ARRANGE
    import_id = import_batch_first
    # ACT
    rv = await http.get(f"/imports/{import_id}/citizens")
    # ASSERT
    assert rv.status == 200, await rv.json()
    jsn = await rv.json()
    assert jsn == {
        "data": [
            {
                "citizen_id": 1,
                "town": "Москва",
                "street": "Льва Толстого",
                "building": "16к7стр5",
                "apartment": 7,
                "name": "Иванов Иван Иванович",
                "birth_date": "26.12.1986",
                "gender": "male",
                "relatives": [2, 3],
            },
            {
                "citizen_id": 2,
                "town": "Москва",
                "street": "Льва Толстого",
                "building": "16к7стр5",
                "apartment": 7,
                "name": "Иванов Сергей Иванович",
                "birth_date": "01.04.1997",
                "gender": "male",
                "relatives": [1],
            },
            {
                "citizen_id": 3,
                "town": "Москва",
                "street": "Льва Толстого",
                "building": "16к7стр5",
                "apartment": 7,
                "name": "Иванова Мария Леонидовна",
                "birth_date": "23.11.1986",
                "gender": "female",
                "relatives": [1],
            },
        ]
    }


async def test_cannot_list_unknown_import(
    http, import_batch_first, married_ivan_and_maria
):
    """Можно получить список жителей.
    """
    # ARRANGE
    import_id = 111
    # ACT
    rv = await http.get(f"/imports/{import_id}/citizens")
    # ASSERT
    assert rv.status == 404, await rv.json()
