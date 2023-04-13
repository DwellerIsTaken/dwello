'''import discord
import traceback
import text_variables
from discord.ext import commands

class on_command_error():

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):

        #if str(ctx.command.name).startswith('help'):
            #return await ctx.channel.send("Did you mean `$info`?")

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
            trace = ''.join(traceback.format_exception(error.__class__, error, error.__traceback__))
            embed = discord.Embed(title='Error Occurred', description=f'```py\n{trace}\n{error}```', color=discord.Color.red())
            await ctx.send(embed=embed)
            raise error'''