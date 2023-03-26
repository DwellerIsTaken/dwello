import random
import discord
from discord.ext import commands
from discord.app_commands import Choice

class roulettes(commands.Cog, name = "roulettes"):

    def __init__(self, bot):
        self.bot = bot
        super().__init__

    @commands.hybrid_group(invoke_without_command=True,with_app_command=True)
    async def roulette(self,ctx):

        embed = discord.Embed(title = "Roulettes", description = "[Here you can read about how to play a casino roulette.](https://smartcasinoguide.com/how-does-roulette-work-rules-and-systems/#:~:text=Roulette%20rules%20are%20simple.%20A%20croupier%20spins%20the,particular%20number%20are%20possible%20and%20on%20combinations%20too.)")
        embed.set_image(url = "https://www.fruityking.co.uk/wp-content/uploads/2019/06/roulette-illustration.png")
        await ctx.reply(embed=embed,mention_author = False) # LOCAL IMG MUST HAVE

    @roulette.command(alias = ["russian"])
    async def russian(self, ctx):
        #russian roulette
        pass

    @roulette.command(name = "casino")
    @discord.app_commands.choices(period = [Choice(name="even", value="seconds"),Choice(name="odd", value="seconds"),Choice(name="black", value="seconds"),
    Choice(name="red", value="seconds"),Choice(name="high", value="seconds"),Choice(name="low", value="seconds"),Choice(name="1st 12", value="seconds"),
    Choice(name="2nd 12", value="seconds"), Choice(name="3rd 12", value="seconds"), Choice(name="lowest column (1-34)", value="seconds"),
    Choice(name="middle column (2-35)", value="seconds"), Choice(name="highest column (3-36)", value="seconds")])
    async def casino(self, ctx, period: Choice[str]):
        #russian roulette
        pass

async def setup(bot):
  await bot.add_cog(roulettes(bot))