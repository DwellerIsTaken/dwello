# REDO TO PIL
import discord, asyncpg
import os
from discord.ext import commands
import text_variables
from colorthief import ColorThief
import matplotlib.colors as clr
from utils.levelling import LevellingUtils
from PIL import Image, ImageFont
#from easy_pil import Editor, Canvas, load_image_async, Font
import requests
import io
from cogs.economy.guild_eco import GuildEcoUtils
import text_variables as tv
from typing import Optional, Union, Any
from utils import get_avatar_dominant_color, BaseCog, DwelloContext
from bot import Dwello

class UserInfo(BaseCog):

    def __init__(self, bot: Dwello, *args: Any, **kwargs: Any):
        super().__init__(bot, *args, **kwargs)

    @commands.hybrid_command(name = 'stats', description="Shows personal information and rank statistics",with_app_command=True) 
    async def stats(self, ctx: DwelloContext, member: Optional[Union[discord.Member, discord.User]] = commands.Author) -> Optional[discord.Message]:
        async with ctx.typing(ephemeral=True):
            async with self.pool.acquire() as conn:
                conn: asyncpg.Connection
                async with conn.transaction():
                    
                    if ctx.guild:
                        query = "SELECT xp, messages, level, money, total_xp FROM users WHERE user_id = $1 AND guild_id = $2 AND event_type = $3"
                        warn_query = "SELECT warn_text FROM warnings WHERE user_id = $1 AND guild_id = $2"
                        query_params = [member.id, ctx.guild.id, "bot"]
                        warn_params = [member.id, ctx.guild.id]
                    else:
                        query = "SELECT xp, messages, level, money, total_xp FROM users WHERE user_id = $1 AND guild_id IS NOT NULL AND event_type = $2"
                        warn_query = "SELECT warn_text FROM warnings WHERE user_id = $1 AND guild_id IS NOT NULL"
                        query_params = [member.id, "bot"]
                        warn_params = [member.id]

                    try:
                        row = await conn.fetchrow(query, *query_params)
                        xp, messages, level, money, total_xp = map(int, row)
                        warn_rows = await conn.fetch(warn_query, *warn_params)

                    except TypeError:
                        await self.levelling.create_user(member.id, member.guild.id)
                        row = await conn.fetchrow(query, *query_params)
                        xp, messages, level, money, total_xp = map(int, row)
                        warn_rows = await conn.fetch(warn_query, *warn_params)

                    warnings = sum(1 for row in warn_rows if row["warn_text"])

                    level_formula = int(level * (level * 10))
                    xp_till_next_level = int(level_formula - xp)

                    most_used_color = await get_avatar_dominant_color(member)

                    #embed_hex_code = hex_code.replace('#', '0x')
                    
                    embed = discord.Embed(title="Statistics", color= most_used_color) #discord.Colour.to_rgb(most_used_color)

                    if member == ctx.author:
                        embed.set_author(name = f"Your personal information", icon_url = member.display_avatar)

                    else:
                        name_l = member.name[-1].lower()

                        if "s" == name_l: # GLOBAL 'S FUNCTION
                            embed.set_author(name = f"{member.name}' personal information", icon_url = member.display_avatar)

                        else:
                            embed.set_author(name = f"{member.name}'s personal information", icon_url = member.display_avatar)

                    embed.add_field(name=f"Current level", value=f"`{level}`", inline=True)
                    embed.add_field(name="\u2800\u2800", value="\u2800", inline=True)
                    embed.add_field(name=f"Money", value=f"`{money}`", inline=True)
                    embed.add_field(name=f"Total messages sent", value=f"`{messages}`", inline=True)
                    embed.add_field(name="\u2800\u2800", value="\u2800", inline=True)
                    embed.add_field(name=f"Total xp count", value=f"`{total_xp}`", inline=True)
                    embed.add_field(name=f"Total warnings", value=f"`{warnings}`", inline=True)
                    embed.add_field(name="\u2800\u2800", value="\u2800", inline=True)
                    embed.add_field(name=f"Xp until the next level", value=f"`{xp_till_next_level}`", inline=True)

                    if ctx.guild:
                        name, salary, description = await self.ge.server_job_info(ctx, member)
                        embed.add_field(name=f"Server job", value=f"`{name}`", inline=True)
                        embed.add_field(name="\u2800\u2800", value="\u2800", inline=True)
                        embed.add_field(name=f"Server job salary", value=f"`{salary}`", inline=True)

                    embed.set_thumbnail(url = member.display_avatar)

                    embed.set_footer(text=tv.footer)

            return await ctx.reply(embed=embed, mention_author = False)

    # OPTIMIZE | TO PIL
    '''@commands.hybrid_command(name = 'rank', description="Shows your rank or another member's rank.",with_app_command=True) 
    async def rank(self, ctx: commands.Context, member: Optional[Union[discord.Member, discord.User]] = commands.Author):
        async with ctx.typing():
            async with self.pool.acquire() as conn:
                conn: asyncpg.Connection
                async with conn.transaction():

                    rank = await self.levelling.get_rank(member.id, member.guild.id) # use random: create a file with random number with 9 digits, after the file is used add to a list, so it won't be used again

                    with open("avatar.png", "w") as file:

                        await member.display_avatar.save("avatar.png")

                    #default = 0

                    try:

                        color_thief = ColorThief("avatar.png")
                        dominant_color = color_thief.get_color(quality=1)
                        new_color = map(lambda e: e/255, dominant_color)
                        new_color = tuple(new_color)
                        hex_code = clr.to_hex(new_color)

                    except:

                        hex_code = "#36393e"
                        #default += 1

                    await self.bot.user.display_avatar.save("avatar.png") # saved bot avatar in file, so there won't be any trouble when filling an image with the color

                    with Image.open("avatar.png","r") as image:

                        length = 1000
                        width = 300

                        image = image.resize((length,width))

                        image.paste(("#1e2124"), [0,0,image.size[0],image.size[1]])

                        image.save("avatar.png")

                        query = "SELECT xp, level, total_xp FROM users WHERE user_id = $1 AND guild_id = $2"
                        row = await conn.fetchrow(query, member.id, member.guild.id)

                        xp, level, total_xp = map(int, row)

                        level_formula = int(level*(level * 10))
                        xp_till_next_level = int(level_formula - xp)

                        percentage = (xp / level_formula) * 100

                        background = Editor("avatar.png")
                        profile = await load_image_async(str(member.display_avatar))
                        #default_banner = await load_image_async("https://cdn.discordapp.com/attachments/811285768549957662/996889117298270299/Pixel-Overwatch-Escort-the-Payload-Overwatch_cut.png")

                        profile = Editor(profile).resize((150, 150)).circle_image()
                        #default_banner = Editor(default_banner).resize((1000, 100))

                        truetype_url = 'https://github.com/googlefonts/roboto/blob/main/src/hinted/Roboto-Black.ttf?raw=true'
                        r = requests.get(truetype_url, allow_redirects=True)
                        poppins_big = ImageFont.truetype(io.BytesIO(r.content), size=50)
                        poppins_small = ImageFont.truetype(io.BytesIO(r.content), size=30)

                        square = Canvas((500, 500), "#06FFBF")
                        square = Editor(square)
                        square.rotate(30, expand=True)

                        background.paste(square.image, (600, -250))

                        if member.banner is not None:

                            bnner = member.banner.url
                            bnner = await load_image_async(str(bnner))
                            bnner = Editor(bnner).resize((length,width)) #1000, 100

                            background.paste(bnner.image, (0,0))
                        
                        else:

                            #if default == 1:
                            #background.paste(bnner.image, (0,0))
                            
                            #else:
                            background.rectangle((0,0), width=length, height=100, fill=hex_code)

                        background.ellipse((30,30), width = 165, height = 165, fill = "#1e2124", stroke_width = 10)
                        background.paste(profile.image, (37, 37))
                        background.rectangle((220, 230), width=750, height=40, fill="#545454", radius=20)

                        font_size = 80

                        s = list(member.name)

                        xp_string = f"{xp}"
                        xp_till_next_level_string = f" / {xp_till_next_level} XP"
                        level_string = f"#{level}"
                        rank_string = f"#{int(rank)}"

                        if xp > 999:
                            new_xp = int(xp / 1000)
                            xp_string = f"{new_xp}K"

                        if xp_till_next_level > 999:
                            new_xp_till_next_level = int(xp_till_next_level / 1000)
                            xp_till_next_level_string = f" / {new_xp_till_next_level}K XP"

                        if level > 999:
                            new_level = int(level / 1000)
                            level_string = f"#{new_level}K"

                        if int(rank) > 999:
                            new_rank = int(int(rank) / 1000)
                            rank_string = f"#{new_rank}K"

                        xp_width = poppins_small.getsize(text = xp_string)
                        xp_till_next_level_width = poppins_small.getsize(text = xp_till_next_level_string)
                        discriminator_width = poppins_small.getsize(text = f"  #{member.discriminator}")
                        rank_width = poppins_small.getsize(text = "RANK  ")
                        rank_num_width = poppins_big.getsize(text = rank_string)
                        level_text_width = poppins_small.getsize(text = "LEVEL  ")
                        flat_width = poppins_small.getsize(text = "  |  ")
                        level_width = poppins_big.getsize(text = level_string)

                        dis_width = discriminator_width[0]
                        dis_height = discriminator_width[1]
                        rank_num_width = rank_num_width[0]
                        rank_width = rank_width[0]
                        level_width = level_width[0]
                        level_text_width = level_text_width[0]
                        xp_width = xp_width[0]
                        flat_width = flat_width[0]
                        xp_till_next_level_width = xp_till_next_level_width[0]

                        if len(s) == 0:
                            font_size = font_size
                        
                        else:
                            mult = ((250 - 10 - dis_width) / len(s)) / 100
                            font_size = font_size / (2 - mult)

                        font = ImageFont.truetype(io.BytesIO(r.content), size= int(font_size))

                        user_width = font.getsize(text = f"{member.name}")
                        new_user_width = user_width[0]
                        user_height = font_size

                        background.text((30,245), text = xp_string, font = poppins_small, color = "#cccca2")
                        background.text((( 30 + xp_width),245), text = xp_till_next_level_string, font = poppins_small, color = "#545454")

                        background.text((230, 170), str(member.name), font = font, color="#e6e6b7", align = "left")
                        background.text(((230 + new_user_width), (170 + user_height - dis_height)), f"  #{member.discriminator}", font = poppins_small, color="#545454")

                        stats_width = rank_width + rank_num_width + flat_width + level_text_width + level_width
                        new_width = 970 - int(stats_width)

                        background.text((new_width,120), text = "RANK  ",font = poppins_small, color = "#545454", align = "left") # #cccca2
                        background.text(((new_width + rank_width), 110), text = rank_string,font = poppins_big, color = "#e6e6b7", align = "left") # #cccca2

                        background.text(((new_width + rank_width + rank_num_width), 120), text = "  |  ",font = poppins_small, color = "#545454", align = "left")

                        background.text(((new_width + rank_width + rank_num_width + flat_width), 120), text = "LEVEL ",font = poppins_small, color = "#545454", align = "left")
                        background.text(((new_width + rank_width + rank_num_width + flat_width + level_text_width), 110), text = level_string,font = poppins_big, color = "#e6e6b7", align = "left")

                        #print(member.banner)
                        #print(member.accent_color)

                        if percentage <= 1:
                            pass

                        else:
                            background.bar(
                            (220, 230),
                            max_width = 750,
                            height=40,
                            percentage=percentage,
                            fill="#e6e6b7",
                            radius=20,
                            )
                        
                        file1 = discord.File(fp=background.image_bytes, filename="avatar.png")
                        image.save("avatar.png")

            await ctx.reply(file=file1,mention_author=False)
        return os.remove("avatar.png")'''

    '''@commands.hybrid_command(name = 'leaderboard', description="Shows the level leaderboard.",with_app_command=True) 
    async def leaderboard(self, ctx: commands.Context):
      async with ctx.typing():
        async with asyncpg.create_pool(database=tv.db_name, user=tv.db_username, password=os.getenv('pg_password')) as pool:
            async with pool.acquire() as conn:
                async with conn.transaction():

                    with open("avatar_1.png", "w") as file:

                    #await ctx.message.author.display_avatar.save("avatar_1.png")
                    await self.bot.user.display_avatar.save(file)

                    with Image.open("avatar_1.png","r") as image:

                    # FIX EMOJI FONT

                    truetype_url = 'https://github.com/googlefonts/roboto/blob/main/src/hinted/Roboto-Black.ttf?raw=true'
                    #emoji_font_url = 'https://github.com/adobe-fonts/emojione-color/blob/master/EmojiOneColor.otf'
                    #emoji_big = ImageFont.truetype("EmojiOneColor.ttf", size=50)

                    #u = requests.get(emoji_font_url, allow_redirects=True)
                    r = requests.get(truetype_url, allow_redirects=True)

                    poppins_big = ImageFont.truetype(io.BytesIO(r.content), size=50)
                    poppins_small = ImageFont.truetype(io.BytesIO(r.content), size=30)

                    await cursor.execute("SELECT * FROM main WHERE guild_id = ? ORDER BY total_xp DESC LIMIT 5", (ctx.guild.id))
                    records = await cursor.fetchall()

                    await cursor.execute("SELECT total_xp FROM main WHERE user_id = ? AND guild_id = ?", (ctx.message.author.id, ctx.message.author.guild.id))
                    author_total_xp = await cursor.fetchone()

                    author_total_xp = int(author_total_xp[0])

                    #embed = discord.Embed(title = "Level leaderboard 📈", color = discord.Color.random())

                    # LEADERBOARD TITLE VARIANTS:
                    #title = "**Level leaderboard**".upper()
                    title = "Level leaderboard".upper()
                    #title = "Level leaderboard 📈"
                    #title = "Level leaderboard"             
                    #title = "Level leaderboard 📖".upper()

                    rank = 0
                    item_num = 0

                    member_object_list = []
                    total_xp_list = []
                    name_list = []
                    dis_list = []
                    val_list = []
                    pic_list = []
                    ranking = []

                    start_width = 210
                    avatar_width = 100
                    avatar_lenght = avatar_width

                    for record in records:
                        rank += 1
                        ranking.append(str(f"{rank}."))

                        await cursor.execute(f"SELECT total_xp FROM main WHERE user_id = {record['user_id']} AND guild_id = ?", (ctx.message.author.guild.id))
                        member_total_xp = await cursor.fetchone()

                        total_xp_list.append(int(member_total_xp[0]))

                        member_ = ctx.guild.get_member(record["user_id"])
                        member_object_list.append(member_)

                        profile_pic_1 = await load_image_async(str(member_.display_avatar))
                        profile_pic_1 = Editor(profile_pic_1).resize((avatar_lenght, avatar_width)).circle_image()
                        pic_list.append(profile_pic_1)

                        member_ = str(member_)

                        name_list.append(str(member_[:-5]))
                        val_list.append(member_.upper())
                        dis_list.append(str(member_[-5::]))

                    author_rank = int(await levelling.get_rank(ctx.message.author.id, ctx.message.author.guild.id))
                    #ranking = ["1.","2.","3.","4.","5."]

                    length = 840 #800
                    width = 880
                    title_len = 188.5

                    if author_rank < 6:
                        width = width
                        pass

                    elif author_rank == 6:
                        ranking.append("6.")
                        length = 890
                        width = 1000
                        title_len = 193.5

                        await cursor.execute(f"SELECT total_xp FROM main WHERE user_id = {ctx.message.author.id} AND guild_id = ?", (ctx.message.author.guild.id))
                        member_total_xp = await cursor.fetchone()

                        total_xp_list.append(int(member_total_xp[0]))

                        member_ = ctx.guild.get_member(ctx.message.author.id)
                        member_object_list.append(member_)

                        profile_pic_1 = await load_image_async(str(member_.display_avatar))
                        profile_pic_1 = Editor(profile_pic_1).resize((avatar_lenght, avatar_width)).circle_image()
                        pic_list.append(profile_pic_1)

                        member_ = str(member_)

                        name_list.append(str(member_[:-5]))
                        val_list.append(member_.upper())
                        dis_list.append(str(member_[-5::]))

                    elif author_rank > 6:
                        ranking.append("...")
                        ranking.append(str(author_rank))
                        length = 990
                        width = 1100
                        title_len = 243.5

                        await cursor.execute(f"SELECT total_xp FROM main WHERE user_id = {ctx.message.author.id} AND guild_id = ?", (ctx.message.author.guild.id))
                        member_total_xp = await cursor.fetchone()

                        total_xp_list.append(str("space"))
                        total_xp_list.append(int(member_total_xp[0]))

                        member_ = ctx.guild.get_member(ctx.message.author.id)
                        member_object_list.append(member_)

                        profile_pic_1 = await load_image_async(str(member_.display_avatar))
                        profile_pic_1 = Editor(profile_pic_1).resize((avatar_lenght, avatar_width)).circle_image()
                        pic_list.append(profile_pic_1)

                        member_ = str(member_)

                        #name_list.append(str(member_[:-5]))
                        #val_list.append(member_.upper())
                        #dis_list.append(str(member_[-5::]))

                    image = image.resize((length,width))
                    #try:

                    image.paste(("#24344c"), [0,0,image.size[0],image.size[1]]) # 1e2124

                    #except:
                    #await self.bot.user.display_avatar.save("avatar_1.png")

                    image.save("avatar_1.png")

                    background = Editor("avatar_1.png")

                    #background.text((197.5,30), text = title, font = poppins_big, color = "#babcbc")
                    #background.text((197.5,30), text = title, font = emoji_big, color = "#babcbc")
                    background.text((title_len,30), text = title, font = poppins_big, color = "#babcbc") # cccca2 & 197.5
                    #background.text((148.5,30), text = title, font = emoji_big, color = "#babcbc")

                    for i in ranking:

                        if item_num > 5:
                        break

                        # PRINTING LEADERBOARD POSITION

                        ranking_size = poppins_big.getsize(text = i)
                        ranking_height = ranking_size[1]

                        #nickname_size = poppins_big.getsize(text = name_list[item_num])
                        #nickname_width = nickname_size[0]

                        background.text((148.5, start_width - ranking_height), text = i, font = poppins_big, color = "#babcbc")

                        # IF AUTHOR_RANK IS 6 OR MORE: PASS

                        x_coordinate = 148.5 + ranking_size[0] + 4

                        try:

                        nickname_len = len(name_list[item_num])

                        if nickname_len > 15:
                            a = 0
                            b = 0
                            for w in range(nickname_len - 15):
                            a += 1.4
                            b += 0.85

                            poppins = ImageFont.truetype(io.BytesIO(r.content), size= int(50 - a))
                            background.text((x_coordinate, start_width - ranking_height + b), text = name_list[item_num], font = poppins, color = "#ffdfbe") #fabc74 #fca583

                        else:
                            background.text((x_coordinate, start_width - ranking_height), text = name_list[item_num], font = poppins_big, color = "#ffdfbe") #fabc74 #fca583

                        except:
                        start_width += 100
                        break
                
                        start_width += 150
                        item_num += 1

                    if len(ranking) > 6:
                        #background.text((148.5, start_width - ranking_height), text = "...", font = poppins_big, color = "#babcbc")
                        #start_width += 150
                        background.text((30, start_width - ranking_height), text = f"Your current rank is: {author_rank}", font = poppins_big, color = "#babcbc")
                        #print(start_width,ranking_height)

                    elif len(ranking) == 6:
                        background.text((148.5, start_width - ranking_height), text = ranking[5], font = poppins_big, color = "#babcbc")

                        nickname_len = len(name_list[5])
                        
                        if nickname_len > 15:
                            a = 0
                            b = 0
                            for w in range(nickname_len - 15):
                                a += 1.4
                                b += 0.85

                            poppins = ImageFont.truetype(io.BytesIO(r.content), size= int(50 - a))
                            background.text((x_coordinate, start_width - ranking_height + b), text = name_list[5], font = poppins, color = "#ffdfbe") #fabc74 #fca583

                        else:
                            background.text((x_coordinate, start_width - ranking_height), text = name_list[5], font = poppins_big, color = "#ffdfbe") #fabc74 #fca583

                    start_width = 210
                    count_num = 0
                    item_num = 0
                    font_choice = 0
                    pic_y = 110

                    for y in pic_list:

                        count_num += 1
                        if count_num > 5:
                            break

                        background.paste(y.image, (30, pic_y))

                        poppins = ImageFont.truetype(io.BytesIO(r.content), size = 35)
                        background.text((148.5, pic_y), text = dis_list[item_num], font = poppins, color = "#747484")

                        xp_str = str(total_xp_list[item_num])

                        ranking_size = poppins_big.getsize(text = "1.")
                        ranking_height = ranking_size[1]

                        xp_poppins = ImageFont.truetype(io.BytesIO(r.content), size = 40)

                        if int(total_xp_list[item_num]) > 999:
                        if int(total_xp_list[item_num]) < 10000:

                            xp_str = f"{xp_str[0]}.{xp_str[1]}K"

                        else:
                            pass

                        if int(total_xp_list[item_num]) > 9999:
                        if int(total_xp_list[item_num]) < 100000:

                            xp_str = f"{xp_str[:2]}K"

                        else:
                            pass

                        if int(total_xp_list[item_num]) > 99999:

                        xp_str = f"{xp_str[:3]}K"
                        font_choice += 1

                        if int(total_xp_list[item_num]) < 999:
                        xp_str = f"{xp_str}"

                        if font_choice == 1:
                        font = poppins_small

                        else:
                        font = xp_poppins

                        background.text((651.5 + 10 , start_width - ranking_height + 15), text = "XP " + str(xp_str), font = font, color = "#babcbc")

                        start_width += 150
                        font_choice == 0
                        item_num += 1
                        pic_y += 150

                    if len(dis_list) == 6:
                        poppins = ImageFont.truetype(io.BytesIO(r.content), size = 35)
                        background.text((148.5, pic_y), text = dis_list[5], font = poppins, color = "#747484")

                    else:
                        pass

                    if len(total_xp_list) == 6:

                        item_num = 5

                    elif len(total_xp_list) > 6:

                        item_num = 6

                    try:

                        xp_str = str(total_xp_list[item_num])

                        ranking_size = poppins_big.getsize(text = "1.")
                        ranking_height = ranking_size[1]

                        xp_poppins = ImageFont.truetype(io.BytesIO(r.content), size = 40)

                        if int(total_xp_list[item_num]) > 999:
                            if int(total_xp_list[item_num]) < 10000:

                                xp_str = f"{xp_str[0]}.{xp_str[1]}K"

                            else:
                                pass

                            if int(total_xp_list[item_num]) > 9999:
                                if int(total_xp_list[item_num]) < 100000:

                                    xp_str = f"{xp_str[:2]}K"

                                else:
                                    pass

                                if int(total_xp_list[item_num]) > 99999:

                                    xp_str = f"{xp_str[:3]}K"
                                    font_choice += 1

                                if int(total_xp_list[item_num]) < 999:
                                    xp_str = f"{xp_str}"

                                    if font_choice == 1:
                                        font = poppins_small

                                    else:
                                        font = xp_poppins

                                        start_width += 100

                                        background.text((651.5 + 10 , start_width - ranking_height + 15), text = "XP " + str(xp_str), font = font, color = "#babcbc")

                    except:
                        pass

                    file1 = discord.File(fp=background.image_bytes, filename="avatar_1.png")
                    image.save("avatar_1.png")

                await ctx.reply(file=file1, mention_author=False)
                return os.remove("avatar_1.png")'''
    