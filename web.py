from aiohttp import web

from utils import Twitch

async def handle_post(request):
    data = await request.json()
    
    return web.json_response({"message": "data received by aiohttp: {}".format(data)})

app = web.Application()
app.router.add_post('/api/post', handle_post)

if __name__ == '__main__':
    web.run_app(app, port=8081)