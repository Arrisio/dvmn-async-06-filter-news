import json
import os
from dataclasses import asdict

from aiohttp import web
from settings import MAX_URL_PER_REQUEST

from main import process_articles_from_urls

routes = web.RouteTableDef()


@routes.get("/")
async def get_articles_scores(request):
    try:
        urls = request.query["urls"].split(",")
    except KeyError:
        raise web.HTTPUnprocessableEntity(text='{"error": "required URLs parameter"}', content_type="application/json")

    if len(urls) > MAX_URL_PER_REQUEST:
        response_text = json.dumps({"error": f"too many urls in request, should be {MAX_URL_PER_REQUEST} or less"})
        raise web.HTTPBadRequest(
            text=response_text, content_type="application/json"
            #  json={"error": f"too many urls in request, should be {MAX_URL_PER_REQUEST} or less"}
        )

    return web.json_response(
        [asdict(score) for score in await process_articles_from_urls(urls)], content_type="application/json"
    )


def main():
    app = web.Application()
    app.add_routes(routes)
    web.run_app(app)


if __name__ == "__main__":
    main()
