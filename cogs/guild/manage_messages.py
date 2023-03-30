from discord.ext import commands
import text_variables as tv
import discord

from typing import Optional

class Messages(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(name='clear', help="Purges messages.", with_app_command=True)
    @commands.bot_has_permissions(manage_messages=True)
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx: commands.Context, limit: int = None, member: discord.Member = None) -> Optional[discord.Message]:

        msg = []

        if limit is not None:
            pass

        else:
            return await ctx.reply("Please pass in an integer as limit!")

        if member is None:

            await ctx.channel.purge(limit = limit + 1)
            print(f"{limit}" + " messages deleted by {0}".format(ctx.message.author))
            
            return await ctx.send(f"Purged {limit} messages", delete_after=3)

        async for m in ctx.channel.history():

            if len(msg) == limit:
                break

            if m.author == member:
                msg.append(m)

        await ctx.channel.delete_messages(msg)
        return await ctx.send(f"Purged {limit} messages of {member.mention}", delete_after=3)