from __future__ import annotations

import sys
import traceback
from typing import TYPE_CHECKING, Optional

import discord
from discord.ext import commands

import constants as cs

if TYPE_CHECKING:
    from core import Bot, Context


async def setup(bot: Bot):
    await bot.add_cog(CommandErrorHandler(bot))


# rename to error.py
class CommandErrorHandler(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: Context, error: Exception) -> Optional[discord.Message]:
        """The event triggered when an error is raised while invoking a command.
        Parameters
        ------------
        ctx: commands.Context
            The context used for command invocation.
        error: commands.CommandError
            The Exception raised.
        """

        perm_url = "https://discordpy.readthedocs.io/en/stable/api.html#discord.Permissions"

        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, "on_error"):
            return

        if cog := ctx.cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return

        ignored = (commands.CommandNotFound,)  # make that a check or no ?

        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, "original", error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, ignored):
            return

        # switch to reply
        if isinstance(error, commands.errors.MissingRequiredArgument):
            return await ctx.reply(error, user_mistake=True)

        if isinstance(error, commands.DisabledCommand):
            await ctx.send(f"{ctx.command} has been disabled.")

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                await ctx.author.send(f"{ctx.command} can not be used in Private Messages.")
            except discord.HTTPException:  # handle exception http
                pass

        elif isinstance(error, commands.errors.MemberNotFound):
            return await ctx.reply(error, user_mistake=True)

        elif isinstance(error, commands.BadArgument):
            "Use later."

        elif isinstance(error, commands.errors.CheckFailure):
            pass  # type: ignore

        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(f"You are on cooldown. Try again in {error.retry_after:.2f}s")

        elif isinstance(error, commands.MissingPermissions):
            description = (
                "You don't have permission to use this command.\n"
                "You should have the following permission(s) to use this command:\n"
            )
            for perm in error.missing_permissions:
                description += f"\n• [`{perm}`]({perm_url}.{perm})"

            embed: discord.Embed = discord.Embed(
                title="Permission Denied.",
                description=description,
                color=cs.WARNING_COLOR,
            )
            embed.set_image(url="https://media.tenor.com/bIJa2uRURiQAAAAd/lord-of-the-rings-you-shall-not-pass.gif")
            return await ctx.reply(embed=embed, user_mistake=True)

        elif isinstance(error, commands.BotMissingPermissions):
            description = (
                f"{self.bot.user.name} doesn't have the necessary permissions to use this command.\n"
                "It should have the following permission(s) to use this command:\n"
            )
            for perm in error.missing_permissions:
                description += f"\n• [`{perm}`]({perm_url}.{perm})"

            embed: discord.Embed = discord.Embed(
                title="Permission Denied.",
                description=description,
                color=cs.WARNING_COLOR,
            )
            return await ctx.reply(embed=embed, user_mistake=True)

        else:
            # All other Errors not returned come here. And we can just print the default TraceBack.
            # print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            # traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

            guild: str = f"Guild ID: {ctx.guild.id}\n" if ctx.guild else ""
            # self.bot.logger.error("An error occurred", exc_info=error) report error to special log TODO
            embed: discord.Embed = discord.Embed(
                title=f"Ignoring exception in {ctx.command}:",
                description=f"```py\n{error}```\nThe developers have receieved this error and will fix it.",
                color=0xF02E2E,
            )
            embed.set_author(name=f"{ctx.author.name}", icon_url=ctx.author.display_avatar)
            embed.add_field(
                name="Information",
                value=f"Error Name: {type(error).__name__}\nError Type: {type(error)}\nMessage: {ctx.message.content}\n{guild}Channel ID: {ctx.channel.id}",
            )

            """await ctx.channel.send(
                f"This error came from {ctx.author} using {ctx.command} in {ctx.guild}.",
                embed=embed,
            )"""
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
            return await ctx.reply(embed=embed)

    """Below is an example of a Local Error Handler for our command do_repeat"""

    # move to another channel
    @commands.command(name="repeat", aliases=["mimic", "copy"])
    async def do_repeat(self, ctx: Context, *, inp: str):
        """A simple command which repeats your input!
        Parameters
        ------------
        inp: str
            The input you wish to repeat.
        """
        return await ctx.send(inp)

    @do_repeat.error
    async def do_repeat_handler(self, ctx: Context, error: Exception):
        """A local Error Handler for our command do_repeat.
        This will only listen for errors in do_repeat.
        The global on_command_error will still be invoked after.
        """

        # Check if our required argument inp is missing.
        if isinstance(error, commands.MissingRequiredArgument) and error.param.name == "inp":
            await ctx.send("You forgot to give me input to repeat!")
