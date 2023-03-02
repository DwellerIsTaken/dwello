from discord.ext import commands
import text_variables as tv
import discord

class clear_command(commands.Cog, name = "clear_command"):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name='clear', help="Purges messages.",with_app_command=True)
    @commands.has_permissions(manage_messages=True)
    async def clear(self,ctx, limit: int = None, member: discord.Member = None):

        if ctx.message.author.guild_permissions.manage_messages:

            msg = []

            '''try:
                limit = int(limit)

            except:
                return await ctx.reply("Please pass in an integer as limit!")'''

            if limit is not None:
                pass

            else:
                return await ctx.reply("Please pass in an integer as limit!")

            if member is None:

                await ctx.channel.purge(limit = limit + 1) # +1 is added to purge the command message `$clear`
                print(f"{limit}" + " messages deleted by {0}".format(ctx.message.author))
                
                return await ctx.send(f"Purged {limit} messages", delete_after=3)
            
            else:
                pass

            async for m in ctx.channel.history():

                if len(msg) == limit:
                    break

                if m.author == member:
                    msg.append(m)

            await ctx.channel.delete_messages(msg)
            await ctx.send(f"Purged {limit} messages of {member.mention}", delete_after=3)

        else:
            missing_permissions_embed = discord.Embed(title = "Permission Denied.", description = "You don't have permission to use this command. You should have `manage_messages` permission to be able to use this command.", color = tv.warn_color)
            missing_permissions_embed.set_image(url = '\n https://cdn-images-1.medium.com/max/833/1*kmsuUjqrZUkh_WW-nDFRgQ.gif')
            missing_permissions_embed.set_footer(text=f"This bot was programmed by Dweller_Igor©")
            return await ctx.channel.send(embed = missing_permissions_embed)

    @clear.error
    async def clear_error(self,ctx, error):
        if isinstance(error, commands.MissingPermissions):
            missing_permissions_embed = discord.Embed(title = "Permission Denied.", description = f"You (or the bot) don't have permission to use this command. It should have __*{error.missing_permissions}*__ permission(s) to be able to use this command.", color = tv.warn_color)
            missing_permissions_embed.set_image(url = '\n https://cdn-images-1.medium.com/max/833/1*kmsuUjqrZUkh_WW-nDFRgQ.gif')
            missing_permissions_embed.set_footer(text=tv.footer)

            if ctx.interaction is None:
                return await ctx.channel.send(embed = missing_permissions_embed)
            
            else:
                return await ctx.interaction.response.send_message(embed = missing_permissions_embed, ephemeral = True)
        else:
            raise error

async def setup(bot):
  await bot.add_cog(clear_command(bot))