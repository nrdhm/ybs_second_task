import asyncio

import click
from injector import Injector

import gift_app.storage as storage_module
from gift_app.providers import ApplicationModule
from gift_app.storage import Storage


@click.group()
def cli():
    pass


@cli.command()
def init_db():
    storage = _get_storage()

    async def go():
        await storage.initialize()
        async with storage.pool.acquire() as conn:
            await storage_module.create_tables(conn)

    asyncio.run(go())


@cli.command()
def drop_db():
    async def go():
        storage = _get_storage()
        await storage.initialize()
        async with storage.pool.acquire() as conn:
            await storage_module.drop_tables(conn)

    asyncio.run(go())


def _get_storage() -> Storage:
    injector = Injector(modules=[ApplicationModule])
    storage = injector.get(Storage)
    click.echo(storage.config)
    return storage


if __name__ == "__main__":
    cli()
