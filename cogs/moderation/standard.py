import discord

from discord.app_commands import Choice
from discord.ext import commands

from typing import Optional, Union, Any
from typing_extensions import Self

import constants as cs
from utils import BaseCog, member_check, HandleHTTPException
from bot import Dwello, DwelloContext

class StandardModeration(BaseCog):

    def __init__(self: Self, bot: Dwello, *args: Any, **kwargs: Any):
        super().__init__(bot, *args, **kwargs)

    @commands.hybrid_command(name='ban', help="Bans users with bad behaviour.", with_app_command = True)
    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.has_guild_permissions(ban_members=True)
    @commands.guild_only()
    async def ban(self: Self, ctx: DwelloContext, member: discord.Member, *, reason: Optional[str] = None) -> Optional[discord.Message]:
        async with ctx.typing(ephemeral=True):

            if await member_check(ctx, member, self.bot) is not True: # redo member_check later (?)
                return

            if not reason:
                reason = "Not specified"

            embed: discord.Embed = discord.Embed(
                title="Permanently banned", 
                description=
                    f"Greetings! \nYou have been banned from **{ctx.channel.guild.name}**. "
                    "You must have done something wrong or it's just an administrator whom is playing with his toys. "
                    f"In any way, it's an embezzlement kerfuffle out here.\n \n Reason: **{reason}**", 
                color=cs.RANDOM_COLOR,
            )

            embed.set_image(url = "https://media1.tenor.com/images/05186cf068c1d8e4b6e6d81025602215/tenor.gif?itemid=14108167")
            embed.set_footer(text=cs.FOOTER)
            embed.timestamp = discord.utils.utcnow()
            
            async with HandleHTTPException(ctx, title=f'Failed to ban {member}'):
                await member.ban(reason=reason)

            try:        
                await member.send(embed=embed)

            except discord.HTTPException as e:
                print(e)

            embed: discord.Embed = discord.Embed(
                title="User banned!", 
                description=f"*Banned by:* {ctx.author.mention}\n"
                            f"\n**{member}** has been succesfully banned from this server! \nReason: `{reason}`",
                color=cs.WARNING_COLOR,
            )

            return await ctx.channel.send(embed=embed)
        
    # has_permissions
    # has_guild_permissions
    # bot_has_permissions
    # bot_has_guild_permissions

    # guild.bans (?) <- unban cmd
    # REDO

    @commands.hybrid_command(name='unban', help="Unbans users for good behaviour.", with_app_command = True)
    @commands.bot_has_permissions(send_messages=True, view_audit_log=True, ban_members=True)
    @commands.has_guild_permissions(ban_members=True)
    @commands.guild_only()
    async def unban(self: Self, ctx: DwelloContext, member_object: str) -> Union[discord.Message, discord.InteractionMessage, None]:
        async with ctx.typing(ephemeral=True):

            member = discord.Object(id=member_object) # member_object type str?

            try:
                async with HandleHTTPException(ctx, title=f'Failed to unban {member}'):
                    await ctx.guild.unban(member)

                return await ctx.reply(embed=discord.Embed(description="The provided member is un-banned.", color=cs.RANDOM_COLOR), permission_cmd=True)

            except commands.UserNotFound:
                return await ctx.reply("The provided member doesn't exist or isn't banned.", user_mistake=True)

    @unban.autocomplete('member_object')
    async def autocomplete_callback(self: Self, interaction: discord.Interaction, current: str):

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

    @commands.hybrid_command(name='kick', help="Kick a member for bad behaviour.", aliases=["rename"], with_app_command = True)
    @commands.bot_has_permissions(send_messages=True, kick_members=True)
    @commands.has_permissions(kick_members=True)
    @commands.guild_only()
    async def kick(self: Self, ctx: DwelloContext, member: discord.Member, *, reason: Optional[str] = None) -> Optional[discord.Message]:
        async with ctx.typing(ephemeral=True):

            if await member_check(ctx, member, self.bot) != True:
                return

            if not reason:
                reason = "Not specified"

            embed: discord.Embed = discord.Embed(
                title= "User kicked!", 
                description=f"*Kicked by:* {ctx.author.mention}\n"
                            f"\n**{member}** has been succesfully kicked from this server! \nReason: `{reason}`",
                color=cs.WARNING_COLOR,
            )

            async with HandleHTTPException(ctx, title=f'Failed to kick {member}'):
                await member.kick(reason=reason)

            return await ctx.channel.send(embed=embed)

    @commands.hybrid_command(name='nick', help="Changes the nickname of a provided member.", with_app_command = True)
    @commands.bot_has_guild_permissions(manage_nicknames=True)
    @commands.has_guild_permissions(manage_nicknames=True)
    @commands.guild_only()
    async def nick(self: Self, ctx: DwelloContext, member: discord.Member, *, nickname: Optional[str] = None) -> Optional[discord.Message]:
        async with ctx.typing(ephemeral=True):

            if not nickname and not member.nick:
                return await ctx.reply(f"**{member}** has no nickname to remove.", user_mistake=True)

            elif nickname and len(nickname) > 32:
                return await ctx.reply(f"Nickname is too long! ({len(nickname)}/32)", user_mistake=True)
            
            message = "Changed nickname of **{user}** to **{nick}**.' if nickname else 'Removed nickname of **{user}**."
            embed: discord.Embed = discord.Embed(
                title="Member renamed",
                description= message.format(user=member, nick=nickname), 
                color=cs.WARNING_COLOR,
            )
            
            async with HandleHTTPException(ctx, title=f'Failed to set nickname for {member}.'):
                await member.edit(nick=nickname)

            return await ctx.channel.send(embed=embed)

        #async with HandleHTTPException(ctx, title=f'Failed to set nickname for {member}.'):
            #await member.edit(nick=nickname)

        #message = 'Changed nickname of **{user}** to **{nick}**.' if nickname else 'Removed nickname of **{user}**.'
        #return await ctx.send(message.format(user=mdr(member), nick=mdr(nickname)))