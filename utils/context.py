import asyncio
import contextlib
import io
import logging
import re

import asyncpg
import discord
import typing
import random

from discord import Interaction
from discord.ext import commands
from discord.ext.commands.errors import BadArgument

from typing import Union, Optional, Sequence, Any, TYPE_CHECKING

target_type = Union[discord.Member, discord.User, discord.PartialEmoji, discord.Guild, discord.Invite]

from discord.ext.commands import Bot

def cleanup_code(content):
    """Automatically removes code blocks from the code."""
    # remove ```py\n```
    if content.startswith("```") and content.endswith("```"):
        return "\n".join(content.split("\n")[1:-1])

    # remove `foo`
    return content.strip("` \n")


class ConfirmButton(discord.ui.Button):
    def __init__(self, label: str, emoji: str, button_style: discord.ButtonStyle):
        super().__init__(
            style=button_style,
            label=label,
            emoji=emoji,
        )

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: Confirm = self.view
        view.value = True
        view.stop()


class CancelButton(discord.ui.Button):
    def __init__(self, label: str, emoji: str, button_style: discord.ButtonStyle):
        super().__init__(style=button_style, label=label, emoji=emoji)

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: Confirm = self.view
        view.value = False
        view.stop()


class Confirm(discord.ui.View):
    def __init__(self, buttons: typing.Tuple[typing.Tuple[str]], timeout: int = 30):
        super().__init__(timeout=timeout)
        self.message = None
        self.value = None
        self.ctx: CustomContext = None
        self.add_item(
            ConfirmButton(
                emoji=buttons[0][0],
                label=buttons[0][1],
                button_style=(buttons[0][2] or discord.ButtonStyle.green),
            )
        )
        self.add_item(
            CancelButton(
                emoji=buttons[1][0],
                label=buttons[1][1],
                button_style=(buttons[1][2] or discord.ButtonStyle.red),
            )
        )

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user == self.ctx.author:
            return True
        messages = [
            "Oh no you can't do that! This belongs to **{user}**",
            "This is **{user}**'s confirmation, sorry! 💢",
            "😒 Does this look yours? **No**. This is **{user}**'s confirmation button",
            "HEYYYY!!!!! this is **{user}**'s menu.",
            "Sorry but you can't mess with **{user}**' menu :(",
            "No. just no. This is **{user}**'s menu.",
            "You don't look like {user} do you...",
            "🤨 That's not yours! That's **{user}**'s menu",
            "🧐 Whomst! you're not **{user}**",
            "_out!_ 👋",
        ]
        await interaction.response.send_message(
            random.choice(messages).format(user=self.ctx.author.display_name),
            ephemeral=True,
        )

        return False

class CustomContext(commands.Context):
    bot: Bot
    guild: discord.Guild
    me: discord.Member

    @property
    def clean_prefix(self) -> str:
        """Prefix with escaped MarkDown"""
        return super().clean_prefix.replace("@", "(at)")

    async def send(
        self,
        content: Optional[str] = None,
        *,
        embed: Optional[discord.Embed] = None,
        embeds: Optional[Sequence[discord.Embed]] = None,
        file: Optional[discord.file.File] = None,
        files: Optional[Sequence[discord.file.File]] = None,
        reference: Optional[Union[discord.Message, discord.MessageReference, discord.PartialMessage]] = None,
        mention_author: Optional[bool] = None,
        **kwargs,
    ) -> discord.Message:

        if reminders is True:
            reminders = random.randint(0, 200) == 100

        if embed and embeds:
            raise BadArgument("cannot pass both embed and embeds parameter to send()")

        if content or embed:
            test_string = re.sub(
                "[^A-Za-z0-9._-]+",
                "",
                (str(content) or "") + str((embed.to_dict() if embed else "")),
            )
            if self.bot.http.token in test_string.replace("\u200b", "").replace(" ", ""):
                raise commands.BadArgument("Could not send message as it contained the bot's token!")

        if embed:
            colors = {embed.color} - {discord.Color.default(), None}
            embed.colour = next(iter(colors), self.color)

        embeds = [embed] if embed else (embeds or [])

        return await super().send(
            content=content,
            embed=embed,
            embeds=embeds,
            file=file,
            files=files,
            reference=reference,
            mention_author=mention_author,
            **kwargs
        )
    
        '''except discord.HTTPException:
            return await super().send(content=content, embeds=embeds, reference=None, mention_author=mention_author, file=file, **kwargs)
        '''
    async def reply(self, content: Optional[str] = None, mention_reference_author: Optional[bool] = True, **kwargs: Any) -> discord.Message:

        message_: discord.Message = self.message
        reference_: discord.MessageReference = self.message.reference
        if reference_ and mention_reference_author is True:
            message_ = reference_.resolved
            mention = True if message_.author in self.message.mentions else False

        if not self.interaction:
            return await self.send(content, reference=self.message, mention_author=mention, **kwargs)
        else:
            return await self.send(content, mention_author=mention, **kwargs)

    async def confirm(
        self,
        message: str = "Do you want to confirm?",
        buttons: typing.Optional[typing.Tuple[typing.Union[discord.PartialEmoji, str], str, discord.ButtonStyle]] = None,
        timeout: int = 30,
        delete_after_confirm: bool = False,
        delete_after_timeout: bool = False,
        delete_after_cancel: typing.Optional[bool] = None,
        return_message: bool = False,
    ) -> typing.Union[bool, typing.Tuple[bool, discord.Message]]:
        """A confirmation menu."""

        delete_after_cancel = delete_after_cancel if delete_after_cancel is not None else delete_after_confirm

        view = Confirm(
            buttons=buttons
            or (
                (None, "Confirm", discord.ButtonStyle.green),
                (None, "Cancel", discord.ButtonStyle.red),
            ),  # type: ignore
            timeout=timeout,
        )
        view.ctx = self
        message = await self.send(message, view=view)
        await view.wait()
        if False in (delete_after_cancel, delete_after_confirm, delete_after_timeout):
            view._children = [view.children[0]]
            for c in view.children:
                c.disabled = True
                if view.value is False:
                    c.label = "Cancelled!"
                    c.emoji = None
                    c.style = discord.ButtonStyle.red
                elif view.value is True:
                    c.label = "Confirmed!"
                    c.emoji = None
                    c.style = discord.ButtonStyle.green
                else:
                    c.label = "Timed out!"
                    c.emoji = "⏰"
                    c.style = discord.ButtonStyle.gray
        view.stop()
        if view.value is None:
            try:
                if return_message is False:
                    (await message.edit(view=view)) if delete_after_timeout is False else (await message.delete())
            except (discord.Forbidden, discord.HTTPException):
                pass
            return (None, message) if delete_after_timeout is False and return_message is True else None

        elif view.value:
            try:
                if return_message is False:
                    (await message.edit(view=view)) if delete_after_confirm is False else (await message.delete())
            except (discord.Forbidden, discord.HTTPException):
                pass
            return (True, message) if delete_after_confirm is False and return_message is True else True

        else:
            try:
                if return_message is False:
                    (await message.edit(view=view)) if delete_after_cancel is False else (await message.delete())
            except (discord.Forbidden, discord.HTTPException):
                pass

            return (False, message) if delete_after_cancel is False and return_message is True else False

    '''@property
    def color(self):
        """Returns DuckBot's color, or the author's color. Falls back to blurple"""
        return (
            self.me.color
            if self.me.color not in (discord.Color.default(), None, None)
            else self.author.color
            if self.author.color not in (discord.Color.default(), None, None)
            else discord.Color.blurple()
        )'''

    '''@property
    def colour(self):
        """Returns DuckBot's color, or the author's color. Falls back to blurple"""
        return self.color'''

    async def trigger_typing(self) -> None:
        try:
            await super().typing()
        except (discord.Forbidden, discord.HTTPException):
            pass

    @property
    def reference(self) -> typing.Optional[discord.Message]:
        message = getattr(self.message.reference, "resolved", None)
        return isinstance(message, discord.Message) and message or None

    @property
    def referenced_user(self) -> typing.Optional[discord.abc.User]:
        return getattr(self.reference, "author", None)

    '''@property
    def db(self) -> asyncpg.Pool:
        return self.bot.db'''

    '''async def prompt(
        self,
        message,
        *,
        timeout: int = 60,
        delete_after: Union[bool, None] = False,
        return_message: bool = False,
    ):
        """Prompts the user for text input."""
        bot_message = await self.send(**{"content" if not isinstance(message, discord.Embed) else "embed": message})
        usermessage = None
        try:
            usermessage = await self.bot.wait_for(
                "message",
                check=lambda m: m.author == self.author and m.channel == self.channel,
                timeout=timeout,
            )
            message = usermessage
        except asyncio.TimeoutError:
            raise commands.BadArgument("Prompt timed out.")
        except Exception as e:
            logging.error(f"Failed to prompt user for input", exc_info=e)
            message = None
        else:
            if message and message.content.lower() == "cancel":
                raise commands.BadArgument("✅ Cancelled!")

            if message and not return_message:
                return message.content
            else:
                return message
        finally:
            if delete_after is None:
                to_do = []
                if isinstance(usermessage, discord.Message):
                    if delete_after:
                        to_do.append(bot_message.delete())
                        if message and self.channel.permissions_for(self.me).manage_messages:
                            to_do.append(usermessage.delete())
                        else:
                            to_do.append(usermessage.add_reaction(random.choice(self.bot.constants.DONE)))
                    else:
                        to_do.append(usermessage.add_reaction(random.choice(self.bot.constants.DONE)))

                    [self.bot.loop.create_task(to_do_item) for to_do_item in to_do]'''