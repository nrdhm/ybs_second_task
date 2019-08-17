from aiohttp import web

routes = web.RouteTableDef()


@routes.post("/imports")
async def import_citizens(request):
    return web.json_response({}, status=201)
