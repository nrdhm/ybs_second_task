import logging

from aiohttp import web
from injector import inject

from .decorators import expect_json_body, json_response
from .schemas import CitizenSchema, CitizenUpdateSchema, ImportsSchema
from .storage import Storage


@inject
class ImportsView:
    def __init__(self, storage: Storage, logger: logging.Logger):
        self.storage = storage
        self.logger = logger

    @expect_json_body
    @json_response(status=201)
    async def import_citizens(self, request):
        jsn = await request.json()

        schema = ImportsSchema()
        import_message = schema.load(jsn)

        import_id = await self.storage.import_citizens(import_message.citizens)

        result = {"data": {"import_id": import_id}}
        return result

    @expect_json_body
    @json_response
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
        return result

    @json_response
    async def list_citizens(self, request: web.Request):
        import_id = int(request.match_info["import_id"])
        citizens = await self.storage.list_citizens(import_id)
        schema = CitizenSchema(many=True)
        result = {"data": schema.dump(citizens)}
        return result

    @json_response
    async def list_birthdays(self, request: web.Request):
        import_id = int(request.match_info["import_id"])
        report = await self.storage.birthdays_report(import_id)
        result = {"data": report}
        return result
