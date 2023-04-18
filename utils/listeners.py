from __future__ import annotations

#from .levelling import LevellingUtils as levelling
from discord.ext import commands
import text_variables as tv
import asyncpg, discord, os

from typing import Optional, Literal
from string import Template

from .other import exe_sql

class ListenersFunctions:
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def bot_join(self, guild: discord.Guild) -> None:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():

                counter_names = ['all', 'member', 'bot', 'category']
                event_types = ['welcome', 'leave', 'twitch']
                #counter_names = [counter if counter is not None else 'Not Specified' for counter in counter_names]
                await conn.executemany("INSERT INTO server_data(guild_id, counter_name, event_type) VALUES($1, $2, $3)", [(guild.id, 'Disabled', event) for event in event_types])
                return await conn.executemany("INSERT INTO server_data(guild_id, counter_name, event_type) VALUES($1, $2, $3)", [(guild.id, counter, 'counter') for counter in counter_names])
                # ADD SOME WELCOME MESSAGE FROM BOT OR SMTH

    async def join_leave_event(self, member: discord.Member, name: Literal["welcome", "leave"]) -> Optional[discord.Message]:
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():

                await exe_sql(self.bot, member.guild)

                # adjust counters too in this event

                result = await conn.fetchrow("SELECT channel_id FROM server_data WHERE guild_id = $1 AND event_type = $2", member.guild.id, name)

                if (result[0] if result else None) is None:   
                    return

                send_channel = discord.utils.get(member.guild.channels, id=int(result[0]))

                guild = member.guild

                second_result = await conn.fetchrow("SELECT message_text FROM server_data WHERE guild_id = $1 AND event_type = $2", guild.id, name)

                if str(name) == 'welcome':
                    member_welcome_embed = discord.Embed(title = "You have successfully joined the guild!", description = f"```Guild joined: {guild.name}\nMember joined: {member}\nGuild id: {guild.id}\nMember id: {member.id}```", color = discord.Color.random())
                    member_welcome_embed.set_thumbnail(url=guild.icon.url if guild.icon is not None else self.bot.user.display_avatar.url)
                    member_welcome_embed.set_author(name=member.name, icon_url=member.display_avatar.url if member.display_avatar is not None else self.bot.user.display_avatar.url)
                    member_welcome_embed.set_footer(text=tv.footer)
                    member_welcome_embed.timestamp = discord.utils.utcnow()

                    try:
                        await member.send(embed=member_welcome_embed)

                    except discord.HTTPException as e:
                        print(e)

                    if second_result[0] is None:
                        _message = f"You are the __*{len(list(member.guild.members))}th*__ user on this server. \nI hope that you will enjoy your time on this server. Have a good day!"

                    _title = f"Welcome to {member.guild.name}!"

                elif str(name) == 'leave':
                    if second_result[0] is None:
                        _message = "If you left, you had a reason to do so. Farewell, dweller!"

                    _title = f"Goodbye {member}!"

                if second_result[0] is not None:
                    _message = Template(second_result[0]).safe_substitute(members=len(list(member.guild.members)),mention=member.mention,user=member.name,guild=member.guild.name,space="\n")

                _embed = discord.Embed(title = _title, description =  _message, color = discord.Color.random())
                _embed.set_thumbnail(url= member.display_avatar.url if member.display_avatar is not None else self.bot.user.display_avatar.url)
                _embed.set_author(name= member.name, icon_url= member.display_avatar.url if member.display_avatar is not None else self.bot.user.display_avatar.url)
                _embed.set_footer(text=tv.footer)
                _embed.timestamp = discord.utils.utcnow()

        return await send_channel.send(embed=_embed)