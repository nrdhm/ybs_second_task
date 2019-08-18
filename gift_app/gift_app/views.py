import logging
from injector import inject
from aiohttp import web
from .schemas import ImportsSchema, CitizenSchema
from .storage import Storage


@inject
class ImportsView:
    def __init__(self, storage: Storage):
        self.storage = storage

    async def import_citizens(self, request):
        jsn = await request.json()

        schema = ImportsSchema()
        import_message = schema.load(jsn)

        schema = CitizenSchema(many=True)
        citizens = schema.dump(import_message.citizens)

        return web.json_response(citizens, status=201)
