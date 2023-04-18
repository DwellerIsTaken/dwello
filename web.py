from aiohttp import web

async def handle_post(request):
    print("It works!", request)
    return web.Response(text="Hello from aiohttp!")

app = web.Application()
app.router.add_post('/aiohttp', handle_post)  # Add a route for handling post requests

web.run_app(app, host='0.0.0.0', port=8080)