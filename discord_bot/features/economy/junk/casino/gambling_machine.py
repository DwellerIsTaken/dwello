from features.economy.bot_comms.utils.currency import *
from discord.ext import commands
import text_variables as tv
import discord
import asqlite
import random

class gambling_machine(commands.Cog, name = "gambling_machine"):

    def __init__(self, bot):
        self.bot = bot
        super().__init__

    @commands.hybrid_command(name = 'jackpot', description="Activates a gambling machine that can earn you some currency.",with_app_command=True) 
    async def jackpot(self, ctx, required_coins: int):
        async with asqlite.connect(tv.sql_dir) as connector:
            async with connector.cursor() as cursor:
                async with ctx.typing():

                    if await balance_check(ctx, required_coins) != True:
                        return

                    await cursor.execute("SELECT money FROM main WHERE user_id = ? AND guild_id = ?", (ctx.message.author.id, ctx.guild.id))
                    money = await cursor.fetchone()
                    money = int(money[0])

                    win_list = ["You won!", "You lost..."]
                    percentage = float(random.random()) * 100
                    leftover_percentage = float(100 - percentage)

                    string = str(random.choices(win_list, weights = [percentage, leftover_percentage], k = 1)[0])

                    amount = 0

                    if "You won!" in string:
                        amount = int(required_coins * 2)

                    else:
                        money -= required_coins
                        await cursor.execute(f"UPDATE main SET money = ? WHERE user_id = ? AND guild_id = ?",(str(money), ctx.message.author.id, ctx.guild.id))
                        await connector.commit()

                    balance = await add_currency(ctx.message.author, amount)
                    balance = str(balance)

                await ctx.reply(embed = discord.Embed(title = string, description =  f"*Your current balance*: {balance}",color = discord.Color.random()), mention_author = False)

                await cursor.close()
                await connector.close()

    '''@jackpot.error
    async def jackpot_error(self,ctx, error):
        if isinstance(error, commands.MissingPermissions):
            missing_permissions_embed = discord.Embed(title = "Permission Denied.", description = f"You (or the bot) don't have permission to use this command. It should have __*{error.missing_permissions}*__ permission(s) to be able to use this command.", color = discord.Color.random())
            missing_permissions_embed.set_image(url = '\n https://cdn-images-1.medium.com/max/833/1*kmsuUjqrZUkh_WW-nDFRgQ.gif')
            missing_permissions_embed.set_footer(text=text_variables.footer)

            if ctx.interaction is None:
                return await ctx.channel.send(embed = missing_permissions_embed)
            
            else:
                return await ctx.interaction.response.send_message(embed = missing_permissions_embed, ephemeral = True)
        
        elif isinstance(error, commands.errors.MissingRequiredArgument):
            return await ctx.reply("The provided argument could not be found or you forgot to provide one.", mention_author = True)

        else:
            raise error'''

async def setup(bot):
  await bot.add_cog(gambling_machine(bot))