from discord.app_commands import Choice
from discord.ext import commands
from contextlib import suppress
import text_variables as tv
import discord

from utils import member_check, HandleHTTPException
from typing import Optional, Union

class StandardModeration(commands.Cog):

    def __init__(self, bot: commands.Bot):
        super().__init__
        self.bot = bot

    @commands.hybrid_command(name='ban', help="Bans users with bad behaviour. | Moderation", with_app_command = True)
    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.has_guild_permissions(ban_members=True)
    @commands.guild_only()
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: Optional[str] = None) -> Optional[discord.Message]:
        async with ctx.typing():

            if await member_check(ctx, member, self.bot) is not True:
                return

            if reason is None:
                reason = "Not specified"

            member_embed=discord.Embed(title="Permanently banned", description=f"Greetings! \nYou have been banned from **{ctx.channel.guild.name}**. You must have done something wrong or it's just an administrator whom is playing with his toys. In any way, it's an embezzlement kerfuffle out here.\n \n Reason: **{reason}**", color=tv.color)
            member_embed.set_image(url = "https://media1.tenor.com/images/05186cf068c1d8e4b6e6d81025602215/tenor.gif?itemid=14108167")
            member_embed.set_footer(text=tv.footer)
            member_embed.timestamp = discord.utils.utcnow()
            
            async with HandleHTTPException(ctx, title=f'Failed to ban {member}'):
                await member.ban(reason=reason)

            async with suppress(discord.HTTPException): await member.send(embed=member_embed)

            guild_embed = discord.Embed(title="User banned!", description=f'*Banned by:* {ctx.author.mention} \n \n**{member}** has been succesfully banned from this server! \nReason: `{reason}`',color=tv.warn_color)

            return await ctx.send(embed=guild_embed)
        
    # has_permissions
    # has_guild_permissions
    # bot_has_permissions
    # bot_has_guild_permissions

    # guild.bans (?)

    @commands.hybrid_command(name='unban', help="Unbans users for good behaviour. | Moderation", with_app_command = True)
    @commands.bot_has_permissions(send_messages=True, view_audit_log=True, ban_members=True)
    @commands.has_guild_permissions(ban_members=True)
    @commands.guild_only()
    async def unban(self, ctx: commands.Context, member_object: str) -> Union[discord.Message, discord.InteractionMessage, None]:
        async with ctx.typing():

            member = discord.Object(id=member_object)

            try:
                async with HandleHTTPException(ctx, title=f'Failed to unban {member}'):
                    await ctx.guild.unban(member)
                return await ctx.reply("The provided member is un-banned.", ephemeral = True)

            except commands.UserNotFound:
                return await ctx.reply("The provided member doesn't exist or isn't banned.", ephemeral = True)

    @unban.autocomplete('member_object')
    async def autocomplete_callback(self, interaction: discord.Interaction, current: str):

        item = len(current)
        choices = []

        async for entry in interaction.guild.bans(limit=None):
            if current:
                pass

            if current.startswith(str(entry.user.name).lower()[:int(item)]):
                choices.append(Choice(name = str(entry.user.name), value = str(entry.user.id)))
                pass
                
            elif current.startswith(str(entry.user.id)[:int(item)]):
                choices.append(Choice(name = str(entry.user.name), value = str(entry.user.id)))
                pass

        if len(choices) > 5:
            return choices[:5]

        return choices

    @commands.hybrid_command(name='kick', help="Kick a member for bad behaviour. | Moderation", with_app_command = True)
    @commands.bot_has_permissions(send_messages=True, kick_members=True)
    @commands.has_permissions(kick_members=True)
    @commands.guild_only()
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: Optional[str] = None) -> Optional[discord.Message]:
        async with ctx.typing():

            if await member_check(ctx, member, self.bot) != True:
                return

            if reason is None:
                reason = "Not specified"

            embed = discord.Embed(title="User kicked!", description=f'*Kicked by:* {ctx.author.mention} \n \n**{member}** has been succesfully kicked from this server! \nReason: `{reason}`',color=tv.warn_color)

            async with HandleHTTPException(ctx, title=f'Failed to kick {member}'):
                await member.kick(reason=reason)
            return await ctx.send(embed=embed)

    @commands.hybrid_command(name='nick', help="Changes the nickname of a provided member. | Moderation", with_app_command = True)
    @commands.bot_has_guild_permissions(manage_nicknames=True)
    @commands.has_guild_permissions(manage_nicknames=True)
    @commands.guild_only()
    async def nick(self, ctx: commands.Context, member: discord.Member, *, nickname: Optional[str] = None) -> Optional[discord.Message]:
        async with ctx.typing():

            if nickname is None and not member.nick:
                return await ctx.reply(f"**{member}** has no nickname to remove.", ephemeral = True)

            elif nickname is not None and len(nickname) > 32:
                return await ctx.reply(f"Nickname is too long! ({len(nickname)}/32)", ephemeral = True)
            
            message = 'Changed nickname of **{user}** to **{nick}**.' if nickname else 'Removed nickname of **{user}**.'
            embed = discord.Embed(title="Member renamed", description= message.format(user = member, nick = nickname), color=tv.warn_color)
            
            async with HandleHTTPException(ctx, title=f'Failed to set nickname for {member}.'):
                await member.edit(nick=nickname)
            return await ctx.send(embed=embed)

        #async with HandleHTTPException(ctx, title=f'Failed to set nickname for {member}.'):
            #await member.edit(nick=nickname)

        #message = 'Changed nickname of **{user}** to **{nick}**.' if nickname else 'Removed nickname of **{user}**.'
        #return await ctx.send(message.format(user=mdr(member), nick=mdr(nickname)))