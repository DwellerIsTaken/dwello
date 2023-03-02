secret = "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"

from discord.ext import commands
import asqlite, discord, os
import openai, requests

class ChatBot(commands.Cog, name = "ChatBot"):

    def __init__(self, bot):
        self.bot = bot
        super().__init__()



async def setup(bot):
  await bot.add_cog(ChatBot(bot))