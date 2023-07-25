import random

import discord
from discord.ext import commands

import constants as cs

# REMOVE THIS FILE prbpl
# remove debugging dir


async def member_check(ctx: commands.Context, member: discord.Member, bot: commands.Bot) -> bool:
    string = ctx.command.name
    monologue = random.choice(cs.bot_reply_list)

    if ctx.author == member:
        embed: discord.Embed = discord.Embed(
            title="Permission Denied.",
            description=f"Hi **{ctx.author.name}**! The member you are trying to {string} is **YOU**! "
            f"So don't be stupid and don't {string} yourself. Call an admin and he will {string} you immidiately.",
        )
        await ctx.reply(embed=embed, ephemeral=True)
        return False

    elif member.id == bot.user.id:
        await ctx.reply(
            embed=discord.Embed(
                title="Permission Denied.",
                description=str(monologue),
            ),
            ephemeral=True,
        )
        return False

    if member.top_role > ctx.author.top_role:
        await ctx.reply(
            f"You can't {string} a member who has a higher role than you!",
            ephemeral=True,
        )
        return False

    return True


async def interaction_check(interaction: discord.Interaction, author: discord.User) -> bool:
    if interaction.user.id == author.id:
        return True

    missing_permissions_embed = discord.Embed(
        title="Permission Denied.",
        description="You can't interact with someone else's buttons.",
        color=discord.Color.random(),
    )
    missing_permissions_embed.set_image(url="\n https://cdn-images-1.medium.com/max/833/1*kmsuUjqrZUkh_WW-nDFRgQ.gif")
    missing_permissions_embed.set_footer(text=cs.FOOTER)
    return await interaction.response.send_message(embed=missing_permissions_embed, ephemeral=True)  # bruh
