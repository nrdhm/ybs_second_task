import logging
from aiohttp import web
from injector import inject

from .schemas import ImportsSchema, CitizenUpdateSchema, CitizenSchema
from .storage import Storage
from .decorators import expect_json_body


@inject
class ImportsView:
    def __init__(self, storage: Storage, logger: logging.Logger):
        self.storage = storage
        self.logger = logger

    @expect_json_body
    async def import_citizens(self, request):
        jsn = await request.json()

        schema = ImportsSchema()
        import_message = schema.load(jsn)

        import_id = await self.storage.import_citizens(import_message.citizens)

        result = {"data": {"import_id": import_id}}
        return web.json_response(result, status=201)

    @expect_json_body
    async def update_citizen(self, request: web.Request):
        import_id = int(request.match_info["import_id"])
        citizen_id = int(request.match_info["citizen_id"])
        jsn = await request.json()

        schema = CitizenUpdateSchema()
        citizen_update = schema.load(jsn)

        await self.storage.retrieve_citizen(import_id, citizen_id)

        citizen = await self.storage.update_citizen(
            import_id, citizen_id, citizen_update
        )
        schema = CitizenSchema()
        result = {"data": schema.dump(citizen)}
        return web.json_response(result, status=200)

    async def list_citizens(self, request: web.Request):
        import_id = int(request.match_info["import_id"])
        citizens = await self.storage.list_citizens(import_id)
        schema = CitizenSchema(many=True)
        result = {"data": schema.dump(citizens)}
        return web.json_response(result, status=200)
