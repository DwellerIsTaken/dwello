from aiohttp import web

class AiohttpWeb:

    def __init__(self, bot):
        self.bot = bot
        self.app: web.Application = web.Application()
        self.app.router.add_post('/api/post', self.handle_post)

    async def handle_post(self, request):
        print(request)
        data = await request.json()
        print(data)

        await self.bot.twitch.twitch_to_discord(data)
        return web.json_response({"message": "data received by aiohttp: {}".format(data)})

    async def run(self, port: int = 8081):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, "localhost", port)

        try:
            await self.bot.loop.create_task(site.start())
            await self.bot.loop.create_task(self.bot.wait_until_ready())
            print(f"Web server running on http://localhost:{port}")
            
        except Exception as e:
            print(f"Failed to start web server: {e}")