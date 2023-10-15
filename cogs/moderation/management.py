from __future__ import annotations

from typing import Any

import discord
from discord.ext import commands

from core import BaseCog, Context, Dwello, Embed

# manage messages, roles, members...


class Management(BaseCog):
    def __init__(self, bot: Dwello, *args: Any, **kwargs: Any) -> None:
        super().__init__(bot, *args, **kwargs)

    @commands.hybrid_command(
        name="clear",
        brief="Purges messages.",
        description="Purges messages.",
        aliases=["purge", "cleanup", "delete"],
    )
    @commands.check_any(
        commands.bot_has_permissions(manage_messages=True),
        commands.has_permissions(manage_messages=True),
    )
    async def clear(self, ctx: Context, limit: int = 5, member: discord.Member | None = None) -> discord.Message | None:
        async with ctx.typing(ephemeral=True):
            msg = []

            if member is None:
                await ctx.channel.purge(limit=limit + 1)
                # print(f"{limit}" + " messages deleted by {0}".format(ctx.message.author))

                return await ctx.send(f"Purged {limit} messages", delete_after=3)

            async for m in ctx.channel.history():
                if len(msg) == limit:
                    break

                if m.author == member:
                    msg.append(m)

            await ctx.channel.delete_messages(msg)
            return await ctx.send(f"Purged {limit} messages of {member.mention}", delete_after=3)
        
    @commands.command(name="role", brief="Adds roles to a member.")
    @commands.check_any(
        commands.bot_has_permissions(manage_roles=True),
        commands.has_guild_permissions(manage_roles=True),
    )
    async def role(self, ctx: Context, member: discord.Member, *roles: discord.Role) -> discord.Message | None: # dont work
        await member.add_roles(*roles)
        return await ctx.reply(
            embed=Embed(
                description=f"Added roles {', '.join(r.mention for r in roles)} to {member.mention}",
            ),
        )
    
    @commands.command(name="unrole", brief="Removes member's roles.")
    @commands.check_any(
        commands.bot_has_permissions(manage_roles=True),
        commands.has_guild_permissions(manage_roles=True),
    )
    async def unrole(self, ctx: Context, member: discord.Member, *roles: discord.Role) -> discord.Message | None:
        await member.remove_roles(*roles)
        return await ctx.reply(
            embed=Embed(
                description=f"Removed roles {', '.join(r.mention for r in roles)} from {member.mention}",
            ),
        )
