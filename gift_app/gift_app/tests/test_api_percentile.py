async def test_percentile_example_ok(http, import_batch_first):
    """Пример статистики по городам из задания работает как надо.
    """
    # ACT
    rv = await http.get(f"/imports/{import_batch_first}/towns/stat/percentile/age")
    # ASSERT
    assert rv.status == 200, await rv.json()
    jsn = await rv.json()
    assert jsn == {
        "data": [
            {"town": "Керчь", "p50": 32.0, "p75": 32.0, "p99": 32.0},
            {"town": "Москва", "p50": 27.0, "p75": 29.5, "p99": 31.9},
        ]
    }
