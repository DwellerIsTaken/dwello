from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict, NamedTuple

import discord
import constants as cs

from discord.app_commands import TranslationContext, TranslationContextLocation, Translator, locale_str

if TYPE_CHECKING:
    from aiohttp import ClientSession


class TranslateError(Exception):
    def __init__(self, status_code: int, text: str) -> None:
        self.status_code: int = status_code
        self.text: str = text
        super().__init__(f'Google responded with HTTP Status Code {status_code}')


class TranslatedSentence(TypedDict):
    trans: str
    orig: str


class TranslateResult(NamedTuple):
    original: str
    translated: str
    source_language: str
    target_language: str

    @property
    def text(self) -> str:
        return self.translated


async def translate(text: str, *, src: str = 'auto', dest: str = 'en', session: ClientSession) -> TranslateResult:
    # This was discovered by the people here:
    # https://github.com/ssut/py-googletrans/issues/268
    query = {
        'dj': '1',
        'dt': ['sp', 't', 'ld', 'bd'],
        'client': 'dict-chrome-ex',
        # Source Language
        'sl': src,
        # Target Language
        'tl': dest,
        # Query
        'q': text,
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'  # noqa: E501
    }

    target_language = cs.LANGUAGES.get(dest, 'Unknown')

    async with session.get('https://clients5.google.com/translate_a/single', params=query, headers=headers) as resp:
        match resp.status:
            case 200:
                pass
            case _:
                text = await resp.text()
                raise TranslateError(resp.status, text)
            #429: ratelimit
            
        data = await resp.json()
        src = data.get('src', 'Unknown')
        source_language = cs.LANGUAGES.get(src, src)
        sentences: list[TranslatedSentence] = data.get('sentences', [])
        if len(sentences) == 0:
            raise RuntimeError('Google translate returned no information')

        original = ''.join(sentence.get('orig', '') for sentence in sentences)
        translated = ''.join(sentence.get('trans', '') for sentence in sentences)

        return TranslateResult(
            original=original,
            translated=translated,
            source_language=source_language,
            target_language=target_language,
        )
    

translated_command_descriptions = {}
class NewTranslator(Translator):
    """
    Custom translator class inherrited from :class:`discord.Translator`.
    """
    def __init__(self, session: ClientSession) -> None:
        super().__init__()

        self.session = session

    async def translate(self, string: locale_str, locale: discord.Locale, context: TranslationContext):  # noqa: E501
        '''print(
            f"STRING: {string}",
            f"STRING_MSG: {string.message}",
            f"LOCALE: {locale}",
            f"CONTEXT: {context}",
            f"LOCATION: {context.location}",
            f"DATA: {context.data}",
        )'''
        #print(locale, string.message)
        """
        check if locale is the lang we want
        using dutch as an example
        if locale is not discord.Locale.nl:
        its not nl -> return None
        return None

        check if the command description is being translated
        if context.location is app_commands.TranslationContextLocation.command_description:
        print(context.data) # will the command instance (app_commands.Command)
        check original description
        if string.message == "english":
            # return translated description
            return "engels"

        no translation string for a command or anything? return None

        if locale is not discord.Locale.dutch:
        its not nl -> return None

        """
        """if context.location is TranslationContextLocation.command_name:
            translated_command_descriptions[string.message] = {}"""
            
        # check if the command description is being translated
        if context.location is TranslationContextLocation.command_description:
            """locale_str = str(locale)
            _dest = locale_str[:2] if locale_str not in {"zh-CN", "zh-TW"} else locale_str
            translated: TranslateResult = await translate(string.message, dest=_dest, src='en', session=self.session)
            print(locale, translated.text)
            return translated.text"""
        return None
