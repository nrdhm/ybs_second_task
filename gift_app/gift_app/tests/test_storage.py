from gift_app.storage import Storage


async def test_maria_can_divorce(
    http,
    imported_first_citizens,
    married_ivan_and_maria,
    citizen_maria,
    citizen_sergei,
    citizen_ivan,
    storage: Storage,
):
    """Чисто гипотетически, Мария может развестись с Иваном.
    """
    # ARRANGE
    import_id = imported_first_citizens
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
    # Сергей не одобряет развод, но с Иваном они все еще браться не смотря на разногласия.
    assert citizen_sergei.citizen_id in citizen_ivan.relatives
    assert citizen_ivan.citizen_id in citizen_sergei.relatives
