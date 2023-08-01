from __future__ import annotations

import discord
from discord.app_commands import TranslationContext, TranslationContextLocation, Translator, locale_str


# just copy danny's
# TRANSLATOR
class NewTranslator(Translator):
    """
    Custom translator class inherrited from :class:`discord.Translator`.
    """

    async def translate(self, string: locale_str, locale: discord.Locale, context: TranslationContext):  # noqa: E501
        print(
            f"STRING: {string}",
            f"STRING_MSG: {string.message}",
            f"LOCALE: {locale}",
            f"CONTEXT: {context}",
            f"LOCATION: {context.location}",
            f"DATA: {context.data}",
        )
        """# check if locale is the lang we want
    # using dutch as an example
    if locale is not discord.Locale.nl:
      # its not nl -> return None
      return None

    # check if the command description is being translated
    if context.location is app_commands.TranslationContextLocation.command_description:
      print(context.data) # will the command instance (app_commands.Command)
      # check original description
      if string.message == "english":
        # return translated description
        return "engels"

    # no translation string for a command or anything? return None"""

        if locale is not discord.Locale.dutch:
            # its not nl -> return None
            return None

        # check if the command description is being translated
        if context.location is TranslationContextLocation.command_description:
            print(context.data)  # will the command instance (app_commands.Command)
            # check original description
            print(f"DESC: {string.message}")
            if string.message == "english":
                # return translated description
                return "engels"
        return None
