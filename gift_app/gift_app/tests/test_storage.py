from gift_app.storage import Storage


async def test_maria_can_divorce(
    import_batch_first,
    married_ivan_and_maria,
    citizen_maria,
    citizen_sergei,
    citizen_ivan,
    storage: Storage,
):
    """Чисто гипотетически, Мария может развестись с Иваном.
    """
    # ARRANGE
    import_id = import_batch_first
    update = {"relatives": []}
    # ACT
    await storage.update_citizen(import_id, citizen_maria.citizen_id, update)
    # ASSERT
    # Обновляем данные. У нас не ОРМ, все ручками.
    citizen_ivan = await storage.retrieve_citizen(import_id, citizen_ivan.citizen_id)
    citizen_maria = await storage.retrieve_citizen(import_id, citizen_maria.citizen_id)
    citizen_sergei = await storage.retrieve_citizen(
        import_id, citizen_sergei.citizen_id
    )
    # Мария больше не родня Ивану.
    assert citizen_maria.citizen_id not in citizen_ivan.relatives
    assert citizen_ivan.citizen_id not in citizen_maria.relatives
    # Сергей не одобряет развод, но с Иваном они все еще братья не смотря на разногласия.
    assert citizen_sergei.citizen_id in citizen_ivan.relatives
    assert citizen_ivan.citizen_id in citizen_sergei.relatives


async def test_ivan_can_be_relative_to_himself(storage: Storage, citizen_ivan):
    """Иван может быть родственником самому себе.
    """
    # ARRANGE
    citizen_ivan.relatives = [citizen_ivan.citizen_id]
    # ACT
    import_id = await storage.import_citizens([citizen_ivan])
    # ASSERT
    citizen_ivan = await storage.retrieve_citizen(import_id, citizen_ivan.citizen_id)
    assert citizen_ivan.relatives == [citizen_ivan.citizen_id]


async def test_update_does_not_affect_others_imports(
    storage: Storage, import_batch_first, import_batch_second, citizen_maria
):
    """Обновление жителя из одного импорта не трогает жителей другого импорта.
    """
    # ARRANGE
    update = {"name": "Нейроманова Мария Леонидовна"}
    # ACT
    await storage.update_citizen(import_batch_first, citizen_maria.citizen_id, update)
    # ASSERT
    citizen_maria_first = await storage.retrieve_citizen(
        import_batch_first, citizen_maria.citizen_id
    )
    citizen_maria_second = await storage.retrieve_citizen(
        import_batch_second, citizen_maria.citizen_id
    )
    assert citizen_maria_first.name.startswith("Нейроманова")
    assert citizen_maria_second.name.startswith("Романова")
