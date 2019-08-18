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
@click.option('--config', type=click.File('r'))
def init_db(config):
    storage = _get_storage()
    if config:
        storage.config.read_from_file(config)
    async def go():
        await storage.initialize()
        await storage_module.create_tables(storage.engine)
    asyncio.run(go())


@cli.command()
@click.option('--config', type=click.File('r'))
def drop_db(config):
    storage = _get_storage()
    if config:
        storage.config.read_from_file(config)
    async def go():
        await storage.initialize()
        await storage_module.drop_tables(storage.engine)
    asyncio.run(go())


def _get_storage() -> Storage:
    injector = Injector(modules=[ApplicationModule])
    storage = injector.get(Storage)
    click.echo(storage.config)
    return storage


if __name__ == '__main__':
    cli()
