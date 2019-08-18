from aiohttp import web
from injector import inject

from .schemas import ImportsSchema
from .storage import Storage


@inject
class ImportsView:
    def __init__(self, storage: Storage):
        self.storage = storage

    async def import_citizens(self, request):
        jsn = await request.json()

        schema = ImportsSchema()
        import_message = schema.load(jsn)

        import_id = await self.storage.import_citizens(import_message)

        result = {"data": {"import_id": import_id}}
        return web.json_response(result, status=201)
