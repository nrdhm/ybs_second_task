from aiohttp import web
from injector import inject

from .schemas import ImportsSchema, CitizenUpdateSchema, CitizenSchema
from .storage import Storage


@inject
class ImportsView:
    def __init__(self, storage: Storage):
        self.storage = storage

    async def import_citizens(self, request):
        jsn = await request.json()

        schema = ImportsSchema()
        import_message = schema.load(jsn)

        import_id = await self.storage.import_citizens(import_message.citizens)

        result = {"data": {"import_id": import_id}}
        return web.json_response(result, status=201)

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
