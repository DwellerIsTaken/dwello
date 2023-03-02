import discord
import asqlite
import text_variables as tv
from discord.ui import button, View, Button
from discord.interactions import Interaction
from features.levelling.utils import levelling

class Stats_View(View):

    def __init__(self, user: discord.User, name: str, *, timeout: int = None):
        super().__init__(timeout=timeout)
        self.user = user
        self.name = name
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and interaction.user.id == self.user.id:
            return interaction.user and interaction.user.id == self.user.id

        else:
            missing_permissions_embed = discord.Embed(title = "Permission Denied.", description = f"You can't interact with someone else's buttons.", color = tv.color)
            missing_permissions_embed.set_image(url = '\n https://cdn-images-1.medium.com/max/833/1*kmsuUjqrZUkh_WW-nDFRgQ.gif')
            missing_permissions_embed.set_footer(text=tv.footer)
            await interaction.response.send_message(embed=missing_permissions_embed, ephemeral=True)
            return False
    
    @button(style = discord.ButtonStyle.green, label="Approve", disabled=False, custom_id="approve_button")
    async def approve(self,interaction: Interaction, button: Button) -> None:
        async with asqlite.connect(tv.sql_dir) as connector:
            async with connector.cursor() as cursor:

                    await cursor.execute(f"SELECT counter_category_id FROM main WHERE guild_id = {interaction.guild.id}")
                    category_record = await cursor.fetchone()

                    if category_record[0] is not None:
                        return await interaction.channel.send("Are you serious? Duh. This category already exists! Do. Not. Interfere. Period.")

                    again_embed = discord.Embed(title = "Need counter channels? Use this:", description =  tv.server_statistics_again_embed_description, color = tv.color)
                    again_embed.set_footer(text=f"This bot was programmed by Dweller_Igor©")

                    counter_category = await interaction.guild.create_category(name="📊 Server Counters 📊".upper(), reason=None, position = 0) # position 0 is top [first] position

                    sql = ("UPDATE main SET deny_clicked = ?, counter_category_id = ? WHERE guild_id = ?")
                    val = (False, counter_category.id, interaction.guild.id)
                    await cursor.execute(sql,val)
                    await connector.commit()

                    await interaction.message.edit(embed=again_embed,view = None)
                    await interaction.channel.send(f"The **{counter_category.name}** is successfully created by **{interaction.user}**!")

                    await counter_func(interaction, self.name)
                    await move_channel(interaction, counter_category)

    @button(style = discord.ButtonStyle.red, label="Deny", disabled=False, custom_id="deny_button")
    async def deny(self, interaction: Interaction, button: Button) -> None:
        async with asqlite.connect(tv.sql_dir) as connector:
            async with connector.cursor() as cursor:

                await cursor.execute(f"SELECT deny_clicked FROM main WHERE guild_id = {interaction.guild.id}")
                result = await cursor.fetchone()

                again_embed = discord.Embed(title = "Use this command once again...", description =  tv.server_statistics_deny_again_embed_description, color = tv.color)
                again_embed.set_footer(text=f"This bot was programmed by Dweller_Igor©")

                if result is None:
                    sql = ("INSERT INTO main(guild_id, deny_clicked) VALUES(?,?)")
                    val = (interaction.guild.id, True)
                    await cursor.execute(sql,val)
                    await connector.commit()

                elif result is not None:
                    sql = ("UPDATE main SET deny_clicked = ? WHERE guild_id = ?")
                    val = (True, interaction.guild.id)
                    await cursor.execute(sql,val)
                    await connector.commit()

                await interaction.response.edit_message(embed=again_embed,view = None)
                await counter_func(interaction, self.name)
                await cursor.close()
                await connector.close()

async def counter_func(ctx, name: str) -> None:
    async with asqlite.connect(tv.sql_dir) as connector:
            async with connector.cursor() as cursor:

                count = ctx.guild.member_count
                nickname = "All"

                bot_counter = 0
                for member in ctx.guild.members:

                    if member.bot:
                        bot_counter += 1

                member_counter = int(ctx.guild.member_count) - bot_counter

                if name == "members_counter_channel_id":
                    count = member_counter
                    nickname = "Member"

                elif name == "bots_counter_channel_id":
                    count = bot_counter
                    nickname = "Bots"

                try:
                    await levelling.create_user(ctx.author.id, ctx.guild.id)

                except:
                    await levelling.create_user(ctx.user.id, ctx.guild.id)

                await cursor.execute(f"SELECT deny_clicked FROM main WHERE guild_id = {ctx.guild.id}")
                deny_result = await cursor.fetchone()

                await cursor.execute(f"SELECT counter_category_id FROM main WHERE guild_id = {ctx.guild.id}")
                category_record = await cursor.fetchone()

                await cursor.execute(f"SELECT {name} FROM main WHERE guild_id = {ctx.guild.id}")
                all_record = await cursor.fetchone()

                try:
                    counter_category = discord.utils.get(ctx.guild.categories, id = int(category_record[0]))

                except TypeError:
                    counter_category = None

                if deny_result[0] is None and counter_category is None:
                    return await ctx.reply(embed = discord.Embed(title="Do you want to create a category for your counters?",description="If your answer is yes pick the `approve` button, otherwise choose the button called `deny`.", color = tv.color).set_footer(text=tv.footer), view = Stats_View(ctx.author,name))

                elif deny_result[0] is None and counter_category is not None:
                    await cursor.execute("UPDATE main SET deny_clicked = ? WHERE guild_id = ?",(1, ctx.guild.id))

                if all_record[0] is None:
                    counter_channel = await ctx.guild.create_voice_channel(f"📊 {nickname} counter: {count}",reason=None,category=counter_category)
                    await cursor.execute(f"UPDATE main SET {name} = ? WHERE guild_id = ?",(counter_channel.id, ctx.guild.id))

                    try:
                        await ctx.reply(f"The **{counter_channel.name}** is successfully created!", mention_author=False)

                    except AttributeError:
                        await ctx.channel.send(f"The **{counter_channel.name}** is successfully created!")

                elif all_record[0] is not None:
              
                        return await ctx.reply("This counter channel already exists! Please provide another type of counter channel if you need to, otherwise __**please don`t create a counter channel that already exists**__.", mention_author=True)

                await connector.commit()
                await cursor.close()
                await connector.close()

async def create_counter_category(ctx) -> discord.CategoryChannel:
    async with asqlite.connect(tv.sql_dir) as connector:
            async with connector.cursor() as cursor:

                await cursor.execute(f"SELECT counter_category_id FROM main WHERE guild_id = {ctx.guild.id}")
                category_record = await cursor.fetchone()

                if not category_record[0]:
                    counter_category = await ctx.guild.create_category(name="📊 Server Counters 📊".upper(), reason=None, position = 0)
                    await cursor.execute("UPDATE main SET counter_category_id = ? WHERE guild_id = ?",(counter_category.id, ctx.guild.id))
                    await connector.commit()

                    await ctx.reply(f"The **{counter_category.name}** is successfully created by {ctx.author.mention}.", mention_author = False)

                else:
                    return await ctx.reply("Are you serious? Duh. This category already exists! Unless you have a category with a perfectly identical name...")

    return counter_category

async def move_channel(ctx, category: discord.CategoryChannel) -> None:
    async with asqlite.connect(tv.sql_dir) as connector:
            async with connector.cursor() as cursor:

                record_list = []

                await cursor.execute(f"SELECT counter_category_id FROM main WHERE guild_id = {ctx.guild.id}")
                category_record_ = await cursor.fetchone()
                record_list.append(category_record_[0])

                await cursor.execute(f"SELECT all_counter_channel_id FROM main WHERE guild_id = {ctx.guild.id}")
                all_record = await cursor.fetchone()
                record_list.append(all_record[0])

                await cursor.execute(f"SELECT members_counter_channel_id FROM main WHERE guild_id = {ctx.guild.id}")
                members_record = await cursor.fetchone()
                record_list.append(members_record[0])

                await cursor.execute(f"SELECT bots_counter_channel_id FROM main WHERE guild_id = {ctx.guild.id}")
                bots_record = await cursor.fetchone()
                record_list.append(bots_record[0])

                for record in record_list:
                    try:

                        if record is not None:
                            channel_id = discord.utils.get(ctx.guild.channels, id = int(record))
                            await channel_id.move(category=category, beginning=True)

                    except:
                        continue

                await cursor.close()
                await connector.close()

async def add_twitch_chnl(ctx, channel: discord.TextChannel = None) -> None:
        async with asqlite.connect(tv.sql_dir) as connector:
            async with connector.cursor() as cursor:

                await levelling.create_user(ctx.author.id, ctx.guild.id)

                await cursor.execute(f"SELECT twitch_channel_id FROM main WHERE guild_id = {ctx.guild.id}")
                twitch_result = await cursor.fetchone()

                if twitch_result[0] is None and channel is None:
                    chnl = ctx.channel
                    string = f"The channel has been set to {chnl.mention}"

                elif twitch_result[0] is None and channel is not None:
                    chnl = channel
                    string = f"The channel has been set to {chnl.mention}"

                elif twitch_result[0] is not None and channel is None:
                    chnl = ctx.channel
                    string = f"The channel has been updated to {chnl.mention}"

                elif twitch_result[0] is not None and channel is not None:
                    chnl = channel
                    string = f"The channel has been updated to {chnl.mention}"

                if str(twitch_result[0]) == str(chnl.id):
                    return await ctx.reply("The twitch channel has already been set to this channel!", mention_author = True)

                await cursor.execute("UPDATE main SET twitch_channel_id = ? WHERE guild_id = ?",(chnl.id, ctx.guild.id))
                await connector.commit()

                await ctx.reply(embed = discord.Embed(description=string, color = tv.color),mention_author = False)

                await cursor.close()
                await connector.close()