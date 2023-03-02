import text_variables as tv
import discord, random

async def member_check(ctx, member, bot):

    string = ctx.command.name
    monologue = random.choice(tv.bot_reply_list)

    try:
        if ctx.interaction.user == member:
            return await ctx.interaction.followup.send(embed = discord.Embed(title="Permission Denied.", description= f"Hi **{ctx.author.name}**! The member you are trying to {string} is **YOU**! So don't be stupid and don't {string} yourself. Call an admin and he will {string} you immidiately.", color=tv.color), ephemeral = True)
            #return await ctx.interaction.response.send_message(embed = discord.Embed(title="Permission Denied.", description= f"Hi **{ctx.author.name}**! The member you are trying to {string} is **YOU**! So don't be stupid and don't {string} yourself. Call an admin and he will {string} you immidiately.", color=discord.Colour.random()), ephemeral = True)

        else:
            pass

    except:
        if ctx.message.author == member:
            return await ctx.reply(embed = discord.Embed(title="Permission Denied.", description= f"Hi **{ctx.author.name}**! The member you are trying to {string} is **YOU**! So don't be stupid and don't {string} yourself. Call an admin and he will {string} you immidiately.", color=tv.color), mention_author = True)

        else:
            pass

    if member.id == bot.user.id:

        if ctx.interaction is None:
            return await ctx.reply(embed= discord.Embed(title="Permission Denied.", description=str(monologue), color=tv.color), mention_author = True)

        else:
            return await ctx.interaction.followup.send(embed= discord.Embed(title="Permission Denied.", description = str(monologue), color=tv.color), ephemeral = True)
            #return await ctx.interaction.response.send_message(embed= discord.Embed(title="Permission Denied.", description = str(monologue), color=discord.Colour.random()), ephemeral = True)

    else:
        pass

    if member.guild_permissions.administrator:

        if ctx.interaction is None:
            return await ctx.reply(f"You can't {string} an admin.", mention_author = True)

        else:
            return await ctx.interaction.followup.send(f"You can't {string} an admin.", ephemeral = True)
            #return await ctx.interaction.response.send_message(f"You can't {string} an admin.", ephemeral = True)

    else:
        pass

    return True