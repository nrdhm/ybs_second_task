async def test_birthdays_example_ok(http, import_batch_first, married_ivan_and_maria):
    """Пример списка жителей с количеством подарков из задания.
    """
    # ACT
    rv = await http.get(f"/imports/{import_batch_first}/citizens/birthdays")
    # ARRANGE
    assert rv.status == 200, await rv.json()
    jsn = await rv.json()
    assert jsn == {
        "data": {
            "1": [],
            "2": [],
            "3": [],
            "4": [{"citizen_id": 1, "presents": 1}],
            "5": [],
            "6": [],
            "7": [],
            "8": [],
            "9": [],
            "10": [],
            "11": [{"citizen_id": 1, "presents": 1}],
            "12": [{"citizen_id": 2, "presents": 1}, {"citizen_id": 3, "presents": 1}],
        }
    }


async def test_birthdays_multiple_presents(http, import_batch_second):
    """Теперь Ивану нужно дарить два подарка в апреле.
    """
    # ACT
    rv = await http.get(f"/imports/{import_batch_second}/citizens/birthdays")
    # ARRANGE
    assert rv.status == 200, await rv.json()
    jsn = await rv.json()
    assert jsn == {
        "data": {
            "1": [],
            "2": [],
            "3": [],
            "4": [{"citizen_id": 1, "presents": 2}],
            "5": [],
            "6": [],
            "7": [],
            "8": [],
            "9": [],
            "10": [],
            "11": [],
            "12": [{"citizen_id": 2, "presents": 1}, {"citizen_id": 3, "presents": 1}],
        }
    }
