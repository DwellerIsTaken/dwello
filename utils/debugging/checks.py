import discord, random
import text_variables as tv
from typing import Union
from discord.ext import commands

async def member_check(ctx: commands.Context, member: discord.Member, bot: commands.Bot) -> Union[discord.Message, bool]:

    string = ctx.command.name
    monologue = random.choice(tv.bot_reply_list)

    if ctx.author == member:
        return await ctx.reply(embed = discord.Embed(title="Permission Denied.", description= f"Hi **{ctx.author.name}**! The member you are trying to {string} is **YOU**! So don't be stupid and don't {string} yourself. Call an admin and he will {string} you immidiately.", color=tv.color), ephemeral = True)

    elif member.id == bot.user.id:
        return await ctx.reply(embed= discord.Embed(title="Permission Denied.", description=str(monologue), color=tv.color), ephemeral = True)

    if member.top_role > ctx.author.top_role:
        return await ctx.reply(f"You can't {string} a member who has a higher role than you!", ephemeral = True)

    return True

async def interaction_check(interaction: discord.Interaction, author: discord.User) -> bool:
    if interaction.user.id == author.id:
        return True

    else:
        missing_permissions_embed = discord.Embed(title = "Permission Denied.", description = f"You can't interact with someone else's buttons.", color = discord.Color.random())
        missing_permissions_embed.set_image(url = '\n https://cdn-images-1.medium.com/max/833/1*kmsuUjqrZUkh_WW-nDFRgQ.gif')
        missing_permissions_embed.set_footer(text=tv.footer)
        return await interaction.response.send_message(embed=missing_permissions_embed, ephemeral=True)