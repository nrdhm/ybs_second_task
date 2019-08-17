import logging
from aiohttp import web
from .schemas import ImportsSchema, CitizenSchema

routes = web.RouteTableDef()


@routes.post("/imports")
async def import_citizens(request):
    jsn = await request.json()

    schema = ImportsSchema()
    import_message = schema.load(jsn)

    schema = CitizenSchema(many=True)
    citizens = schema.dump(import_message.citizens)

    return web.json_response(citizens, status=201)
