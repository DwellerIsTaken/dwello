import text_variables as tv
from string import Template
import asqlite, discord
import typing

async def join_leave_event(bot: discord.Client, member: discord.Member, name: typing.Literal['welcome', 'leave']) -> None:
    async with asqlite.connect(tv.sql_dir) as connector:
        async with connector.cursor() as cursor:

            if name != 'welcome' and name != 'leave':
                raise TypeError

            await cursor.execute("SELECT channel_id FROM server_data WHERE guild_id = ? AND event_type = ?",(member.guild.id, name))
            result = await cursor.fetchone()

            if (result[0] if result else None) is None:   
                return

            send_channel = discord.utils.get(member.guild.channels, id=int(result[0]))

            #members = len(list(member.guild.members))
            #mention = member.mention
            #user = member.name
            guild = member.guild

            await cursor.execute("SELECT message_text FROM server_data WHERE guild_id = ? AND event_type = ?",(guild.id, name))
            second_result = await cursor.fetchone()

            if str(name) == 'welcome':
                member_welcome_embed = discord.Embed(title = "You have successfully joined the guild!", description = f"```Guild joined: {guild.name}\nMember joined: {member}\nGuild id: {guild.id}\nMember id: {member.id}```", color = discord.Color.random())
                member_welcome_embed.set_thumbnail(url=guild.icon.url if guild.icon is not None else bot.user.display_avatar.url)
                member_welcome_embed.set_author(name=member.name, icon_url=member.display_avatar.url if member.display_avatar is not None else bot.user.display_avatar.url)
                member_welcome_embed.set_footer(text=tv.footer)
                member_welcome_embed.timestamp = discord.utils.utcnow()

                try:
                    await member.send(embed=member_welcome_embed)

                except discord.Forbidden or discord.HTTPException:
                    pass

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
            _embed.set_thumbnail(url= member.display_avatar.url if member.display_avatar is not None else bot.user.display_avatar.url)
            _embed.set_author(name= member.name, icon_url= member.display_avatar.url if member.display_avatar is not None else bot.user.display_avatar.url)
            _embed.set_footer(text=tv.footer)
            _embed.timestamp = discord.utils.utcnow()

            await send_channel.send(embed=_embed)

async def msg(ctx, name: typing.Literal['welcome', 'leave'], text: str) -> None:
    async with asqlite.connect(tv.sql_dir) as connector:
        async with connector.cursor() as cursor:

            if name != 'welcome' and name != 'leave':
                raise TypeError

            await cursor.execute("SELECT channel_id FROM server_data WHERE guild_id = ? AND event_type = ?", (ctx.guild.id, name))
            record = await cursor.fetchone()

            if (record[0] if record else None) is None:
                return await ctx.reply(f"Please use `${name} channel` first.")

            if text is None:
                return await ctx.reply(f"Please enter the {name} message, if you want to be able to use this command properly!")

            await cursor.execute("SELECT message_text FROM server_data WHERE guild_id = ? AND event_type = ?", (ctx.guild.id, name))
            result = await cursor.fetchone()

            if result is None:
                await cursor.execute("INSERT INTO server_data (guild_id, message_text, event_type) VALUES(?,?,?)",(ctx.guild.id, text, name))
                await ctx.reply(f"The {name} message has been set to: ```{text}```",mention_author=False)

            elif result is not None:
                await cursor.execute("UPDATE server_data SET message_text = ? WHERE guild_id = ? AND event_type = ?", (text, ctx.guild.id, name))
                await ctx.reply(f"The {name} message has been updated to: ```{text}```",mention_author=False)

            await connector.commit()

async def chnl(ctx, name: typing.Literal['welcome', 'leave'], channel: str = None) -> None:
    async with asqlite.connect(tv.sql_dir) as connector:
        async with connector.cursor() as cursor:

            if name != 'welcome' and name != 'leave':
                raise TypeError

            await cursor.execute("SELECT channel_id FROM server_data WHERE guild_id = ? AND event_type = ?", (ctx.guild.id, name))
            result = await cursor.fetchone()

            if channel is None:
                channel = ctx.channel
            
            if result is None:
                await cursor.execute("INSERT INTO server_data (guild_id, channel_id, event_type) VALUES(?,?,?)",(ctx.guild.id, channel.id, name))
                return await ctx.reply(f"The {name} channel has been set to {channel.mention}.",mention_author=False)

            elif result is not None:
                if str(result[0]) == str(channel.id):
                    return await ctx.reply(f"The leave channel has already been set to this channel!")
                
                else:
                    await cursor.execute("UPDATE server_data SET channel_id = ? WHERE guild_id = ? AND event_type = ?",(channel.id, ctx.guild.id, name))
                    return await ctx.reply(f"The {name} channel has been updated to {channel.mention}.",mention_author=False)

            await connector.commit()

async def displ(ctx, name: typing.Literal['welcome', 'leave']) -> None:
    async with asqlite.connect(tv.sql_dir) as connector:
        async with connector.cursor() as cursor:

            if name != 'welcome' and name != 'leave':
                raise TypeError

            await cursor.execute("SELECT message_text FROM server_data WHERE guild_id = ? AND event_type = ?",(ctx.guild.id, name))
            result = await cursor.fetchone()

            if (result[0] if result else None) is None:
                return await ctx.reply(f"The {name} message isn't yet set. Consider using `${name} message`.")

            await ctx.reply(f"The {name} message is:```{result[0]}```", mention_author=False)

async def chnl_displ(ctx, name: typing.Literal['welcome', 'leave']) -> None:
    async with asqlite.connect(tv.sql_dir) as connector:
        async with connector.cursor() as cursor:

            if name != 'welcome' and name != 'leave':
                raise TypeError

            await cursor.execute("SELECT channel_id FROM server_data WHERE guild_id = ? AND event_type = ?", (ctx.guild.id, name))
            result = await cursor.fetchone()

            if (result[0] if result else None) is None:
                return await ctx.reply(f"The {name} channel isn't yet set. Consider using `${name} channel`.")

            #channel = discord.Object(int(result[0]))
            channel = ctx.guild.get_channel(int(result[0]))

            await ctx.reply(f"The {name} channel is currently set to {channel.mention}", mention_author=False)

async def rmv(ctx, name: typing.Literal['welcome', 'leave']) -> None:
    async with asqlite.connect(tv.sql_dir) as connector:
        async with connector.cursor() as cursor:

            if name != 'welcome' and name != 'leave':
                raise TypeError

            await cursor.execute("UPDATE server_data SET channel_id = NULL WHERE guild_id = ? AND event_type = ?",(ctx.guild.id, name))
            await ctx.reply(f"The {name} channel has been removed.",mention_author=False)
            await connector.commit()