import discord

# __EMBED_ATTRIBUTES__
# __COLORS__:

WARNING_COLOR = 0xFF0000  # -> COLOR FOR WARNINGS
TWITCH_COLOR = discord.Colour.random()  # get color of streamer later & add customize option # gets once | remove this later

# ___FOOTERS___:
FOOTER = "https://hitoshi.org"

# __SOCIAL MEDIA__
WEBSITE = "https://hitoshi.org"
GITHUB = "https://github.com/DwellerIsTaken/discordbot/"
DISCORD = "https://discord.gg/c75yPz59yD"
INVITE_LINK = "https://discord.com/api/oauth2/authorize?client_id=798268589906853908&permissions=50564649975543&scope=bot"  # TEMPORARY  # noqa: E501

# __DOCS__
PERMISSIONS_URL = "https://discordpy.readthedocs.io/en/stable/api.html#discord.Permissions"

# __EMOJIS__
GITHUB_EMOJI = "<:github:1100906448030011503>"
TYPING_EMOJI = "<:typing:1150815321033277512>"
EARLY_DEV_EMOJI = "<:EarlyVerifiedBotDeveloper:1135358665877102592>"  # REMOVE LATER | check where its used first

BUGHUNTER_EMOJI = "<:BugHunter:1135358734453977160>"
BUGHUNTER_LVL2_EMOJI = "<:BugHunterLevel2:1135358722890289284>"
HYPESQUAD_EVENTS_EMOJI = "<:HypeSquadEvents:1135358638794477710>"
NITRO_EMOJI = "<:Nitro:1135358696239661218>"
MODERATOR_PROGRAMS_ALUMNI = "<:ModeratorProgramsAlumni:1135358708860330064>"
EARLY_VERIFIED_BOT_DEVELOPER_EMOJI = "<:EarlyVerifiedBotDeveloper:1135358665877102592>"
EARLY_SUPPORTER_EMOJI = "<:EarlySupporter:1135358682960511086>"
HYPESQUAD_BALANCE_EMOJI = "<:HypeSquadBalance:1135358615289598092>"
HYPESQUAD_BRAVERY_EMOJI = "<:HypeSquadBravery:1135358598357192804>"
HYPESQUAD_BRILLIANCE_EMOJI = "<:HypeSquadBrilliance:1135358577939316816>"
PARTNER_EMOJI = "<:Partner:1135358566316908656>"
ACTIVE_DEVELOPER_EMOJI = "<:ActiveDeveloper:1135358551397769227>"
STAFF_EMOJI = "<:Staff:1135360330139181127>"

# __DICTIONARIES__
PUBLIC_USER_FLAGS_EMOJI_DICT = {
    "hypesquad_brilliance": HYPESQUAD_BRILLIANCE_EMOJI,
    "hypesquad_bravery": HYPESQUAD_BRAVERY_EMOJI,
    "hypesquad_balance": HYPESQUAD_BALANCE_EMOJI,
    "bug_hunter": BUGHUNTER_EMOJI,
    "bug_hunter_level_2": BUGHUNTER_LVL2_EMOJI,
    "early_verified_bot_developer": EARLY_VERIFIED_BOT_DEVELOPER_EMOJI,
    "verified_bot_developer": EARLY_VERIFIED_BOT_DEVELOPER_EMOJI,
    "active_developer": ACTIVE_DEVELOPER_EMOJI,
    "hypesquad": HYPESQUAD_EVENTS_EMOJI,
    "early_supporter": EARLY_SUPPORTER_EMOJI,
    "discord_certified_moderator": MODERATOR_PROGRAMS_ALUMNI,
    "staff": STAFF_EMOJI,
    "partner": PARTNER_EMOJI,
}

BLACK_JACK_CARDS = {
    "0C": discord.PartialEmoji(name="0C", id=1137283528640434196),
    "0D": discord.PartialEmoji(name="0D", id=1137283545224724531),
    "0H": discord.PartialEmoji(name="0H", id=1137283484742852628),
    "0S": discord.PartialEmoji(name="0S", id=1137283517777186848),
    "2C": discord.PartialEmoji(name="2C", id=1137283494985334785),
    "2D": discord.PartialEmoji(name="2D", id=1137283504590295060),
    "2H": discord.PartialEmoji(name="2H", id=1137283540053143572),
    "2S": discord.PartialEmoji(name="2S", id=1137283532427898991),
    "3C": discord.PartialEmoji(name="3C", id=1137283515994603570),
    "3D": discord.PartialEmoji(name="3D", id=1137283482129813644),
    "3H": discord.PartialEmoji(name="3H", id=1137283535116451880),
    "3S": discord.PartialEmoji(name="3S", id=1137283559200129065),
    "4C": discord.PartialEmoji(name="4C", id=1137283487179739196),
    "4D": discord.PartialEmoji(name="4D", id=1137283542586503198),
    "4H": discord.PartialEmoji(name="4H", id=1137283578267455621),
    "4S": discord.PartialEmoji(name="4S", id=1137283530049736824),
    "5C": discord.PartialEmoji(name="5C", id=1137283523468865576),
    "5D": discord.PartialEmoji(name="5D", id=1137283556331237457),
    "5H": discord.PartialEmoji(name="5H", id=1137283462399799336),
    "5S": discord.PartialEmoji(name="5S", id=1137283554938736761),
    "6C": discord.PartialEmoji(name="6C", id=1137283450253082654),
    "6D": discord.PartialEmoji(name="6D", id=1137283477000167454),
    "6H": discord.PartialEmoji(name="6H", id=1137283489557913681),
    "6S": discord.PartialEmoji(name="6S", id=1137283464870248469),
    "7C": discord.PartialEmoji(name="7C", id=1137283575318843425),
    "7D": discord.PartialEmoji(name="7D", id=1137283474269687878),
    "7H": discord.PartialEmoji(name="7H", id=1137283510114193419),
    "7S": discord.PartialEmoji(name="7S", id=1137283478879211531),
    "8C": discord.PartialEmoji(name="8C", id=1137283459774161006),
    "8D": discord.PartialEmoji(name="8D", id=1137283566527594538),
    "8H": discord.PartialEmoji(name="8H", id=1137283507752800306),
    "8S": discord.PartialEmoji(name="8S", id=1137283521166180422),
    "9C": discord.PartialEmoji(name="9C", id=1137283565172838490),
    "9H": discord.PartialEmoji(name="9H", id=1137402224507617340),
    "9D": discord.PartialEmoji(name="9D", id=1137283471753084978),
    "9S": discord.PartialEmoji(name="9S", id=1137283569425842246),
    "AC": discord.PartialEmoji(name="AC", id=1137283549721014273),
    "AD": discord.PartialEmoji(name="AD", id=1137283537750462568),
    "AH": discord.PartialEmoji(name="AH", id=1137283453080051742),
    "AS": discord.PartialEmoji(name="AS", id=1137403003918372884),
    "JC": discord.PartialEmoji(name="JC", id=1137283581262188564),
    "JD": discord.PartialEmoji(name="JD", id=1137283526711058443),
    "JH": discord.PartialEmoji(name="JH", id=1137283562417160192),
    "JS": discord.PartialEmoji(name="JS", id=1137283468494127114),
    "KC": discord.PartialEmoji(name="KC", id=1137283513259937863),
    "KD": discord.PartialEmoji(name="KD", id=1137283573569818694),
    "KH": discord.PartialEmoji(name="KH", id=1137283456825557032),
    "KS": discord.PartialEmoji(name="KS", id=1137283552577327205),
    "QC": discord.PartialEmoji(name="QC", id=1137283502178566146),
    "QD": discord.PartialEmoji(name="QD", id=1137283498495971442),
    "QH": discord.PartialEmoji(name="QH", id=1137283548622106775),
    "QS": discord.PartialEmoji(name="QS", id=1137283492619767818),
}

LANGUAGES = {
    'af': 'Afrikaans',
    'sq': 'Albanian',
    'am': 'Amharic',
    'ar': 'Arabic',
    'hy': 'Armenian',
    'az': 'Azerbaijani',
    'eu': 'Basque',
    'be': 'Belarusian',
    'bn': 'Bengali',
    'bs': 'Bosnian',
    'bg': 'Bulgarian',
    'ca': 'Catalan',
    'ceb': 'Cebuano',
    'ny': 'Chichewa',
    'zh-cn': 'Chinese (Simplified)',
    'zh-tw': 'Chinese (Traditional)',
    'co': 'Corsican',
    'hr': 'Croatian',
    'cs': 'Czech',
    'da': 'Danish',
    'nl': 'Dutch',
    'en': 'English',
    'eo': 'Esperanto',
    'et': 'Estonian',
    'tl': 'Filipino',
    'fi': 'Finnish',
    'fr': 'French',
    'fy': 'Frisian',
    'gl': 'Galician',
    'ka': 'Georgian',
    'de': 'German',
    'el': 'Greek',
    'gu': 'Gujarati',
    'ht': 'Haitian Creole',
    'ha': 'Hausa',
    'haw': 'Hawaiian',
    'iw': 'Hebrew',
    'he': 'Hebrew',
    'hi': 'Hindi',
    'hmn': 'Hmong',
    'hu': 'Hungarian',
    'is': 'Icelandic',
    'ig': 'Igbo',
    'id': 'Indonesian',
    'ga': 'Irish',
    'it': 'Italian',
    'ja': 'Japanese',
    'jw': 'Javanese',
    'kn': 'Kannada',
    'kk': 'Kazakh',
    'km': 'Khmer',
    'ko': 'Korean',
    'ku': 'Kurdish (Kurmanji)',
    'ky': 'Kyrgyz',
    'lo': 'Lao',
    'la': 'Latin',
    'lv': 'Latvian',
    'lt': 'Lithuanian',
    'lb': 'Luxembourgish',
    'mk': 'Macedonian',
    'mg': 'Malagasy',
    'ms': 'Malay',
    'ml': 'Malayalam',
    'mt': 'Maltese',
    'mi': 'Maori',
    'mr': 'Marathi',
    'mn': 'Mongolian',
    'my': 'Myanmar (Burmese)',
    'ne': 'Nepali',
    'no': 'Norwegian',
    'or': 'Odia',
    'ps': 'Pashto',
    'fa': 'Persian',
    'pl': 'Polish',
    'pt': 'Portuguese',
    'pa': 'Punjabi',
    'ro': 'Romanian',
    'ru': 'Russian',
    'sm': 'Samoan',
    'gd': 'Scots Gaelic',
    'sr': 'Serbian',
    'st': 'Sesotho',
    'sn': 'Shona',
    'sd': 'Sindhi',
    'si': 'Sinhala',
    'sk': 'Slovak',
    'sl': 'Slovenian',
    'so': 'Somali',
    'es': 'Spanish',
    'su': 'Sundanese',
    'sw': 'Swahili',
    'sv': 'Swedish',
    'tg': 'Tajik',
    'ta': 'Tamil',
    'te': 'Telugu',
    'th': 'Thai',
    'tr': 'Turkish',
    'uk': 'Ukrainian',
    'ur': 'Urdu',
    'ug': 'Uyghur',
    'uz': 'Uzbek',
    'vi': 'Vietnamese',
    'cy': 'Welsh',
    'xh': 'Xhosa',
    'yi': 'Yiddish',
    'yo': 'Yoruba',
    'zu': 'Zulu',
}

JEY_API_DICT = {
    "bayer": "bayer",
    "billboard": "billboard",
    "blocks": "blocks",
    "blur": "blur",
    "bomb": "bomb",
    "bonks": "bonks",
    "bubble": "bubble",
    "burn": "burn",
    "canny": "canny",
    "cartoon": "cartoon",
    "cinema": "cinema",
    "clock": "clock",
    "cloth": "cloth",
    "cow": "cow",
    "cracks": "cracks",
    "cube": "cube",
    "dilate": "dilate",
    "dither": "dither",
    "dots": "dots",
    "endless": "endless",
    "equations": "equations",
    "explicit": "explicit",
    "fall": "fall",
    "fan": "fan",
    "fire": "fire",
    "flag": "flag",
    "flush": "flush",
    "gallery": "gallery",
    "gameboy_camera": "gameboy camera",
    "globe": "globe",
    "half_invert": "half invert",
    "infinity": "infinity",
    "ipcam": "ipcam",
    "kanye": "kanye",
    "knit": "knit",
    "lamp": "lamp",
    "laundry": "laundry",
    "layers": "layers",
    "letters": "letters",
    "lines": "lines",
    "liquefy": "liquefy",
    "logoff": "logoff",
    "lsd": "lsd",
    "magnify": "magnify",
    "matrix": "matrix",
    "melt": "melt",
    "neon": "neon",
    "optics": "optics",
    "painting": "painting",
    "paparazzi": "paparazzi",
    "patpat": "patpat",
    "pattern": "pattern",
    "phase": "phase",
    "phone": "phone",
    "pizza": "pizza",
    "plank": "plank",
    "plates": "plates",
    "poly": "poly",
    "print": "print",
    "pyramid": "pyramid",
    "radiate": "radiate",
    "rain": "rain",
    "reflection": "reflection",
    "ripped": "ripped",
    "ripple": "ripple",
    "roll": "roll",
    "scrapbook": "scrapbook",
    "sensitive": "sensitive",
    "shine": "shine",
    "shock": "shock",
    "shoot": "shoot",
    "shred": "shred",
    "slice": "slice",
    "soap": "soap",
    "spikes": "spikes",
    "spin": "spin",
    "stereo": "stereo",
    "stretch": "stretch",
    "tv": "tv",
    "wall": "wall",
    "warp": "warp",
    "wiggle": "wiggle",
    "zonk": "zonk",
}

USER_CONFIG_DICT = {
    "notify_user_on_levelup": { # could later be redone to represent all dm notifications from the bot
        "sql_name": "notify_user_on_levelup",
        "default": False,
        "view_items": ["EnableButton", "DisableButton"],
        "sub": {},
        "embed": {
            "title": "Notifications when levelling up",
            "description":
                "The bot will notify (DM) you once you level up, if this option is enabled by you. "
                "This feature is disabled by default. "
            ,
            "url": "",
            "image_url": "",
            "thumbnail_url": "",
            "colour": None,
            "color": None,
            "fields": [
                {
                    "name": "Enable",
                    "value":
                        "If you click this then the bot will notify you once you level up."
                    ,
                    "inline": "True",
                },
                {
                    "name": "Disable",
                    "value":
                        "(Default)\n"
                        "Disables the incredibly annoying dm's from me."
                    ,
                    "inline": "True",
                },
            ],
        },
    }
}

GUILD_CUSTOMISATION_DICT = {
    "embed": { # colors, footers, authors etc
        "sql_name": "personal_notifications",
        "view_items": ["EnableButton", "DisableButton"],
        "sub": {},
        "embed": {
            "title": "Add delete button",
            "description":
                "This feature adds a delete button to each command response that the bot sends. "
                "This feature is disabled by default for obvious reasons, but you can enable it and have fun with it "
                "(||if you're so lazy to click 'delete message' button instead||)."
            ,
            "url": "",
            "image_url": "",
            "thumbnail_url": "",
            "colour": None,
            "color": None,
            "fields": [
                {
                    "name": "Enable",
                    "value":
                        "Enables the slightly annoying delete button below each command response."
                    ,
                    "inline": "True",
                },
                {
                    "name": "Disable",
                    "value":
                        "(Default)\n"
                        "Disables the button if enabled."
                    ,
                    "inline": "True",
                },
                {
                    "name": "Select",
                    "value":
                        "Select the amount of time you want the delete button to be removed after. The time is given in seconds. "
                        "The default time is 3 minutes."
                    ,
                    "inline": "False",
                },
            ],
        },
    },
}

# not sure if needed:
'''
"counter_category_denied": {
        "sql_name": "counter_category_denied",
        "view_items": ["EnableButton", "DisableButton"],
        "sub": {},
        "embed": {
            "title": "Counter category",
            "description":
                "This is an option for creating a category for all your counters. "
                "This option is also suggested once you create a counter channel, "
                "unless you have already configured it here."
            ,
            "url": "",
            "image_url": "",
            "thumbnail_url": "",
            "colour": None,
            "color": None,
            "fields": [
                {
                    "name": "Enable",
                    "value":
                        "If you click this then a category for counters will immideately be created, if you have any."
                    ,
                    "inline": "True",
                },
                {
                    "name": "Disable",
                    "value":
                        "Disables the possible pop-up questioning whether you would like a category or not when "
                        "creating a counter channel. Does not delete the current category if there is one!"
                    ,
                    "inline": "True",
                },
            ],
        },
    },
'''

GUILD_CONFIG_DICT = {
    "turn_link_into_message": {
        "sql_name": "turn_link_into_message",
        "default": False,
        "view_items": ["EnableButton", "DisableButton"],
        "sub": {},
        "embed": {
            "title": "Link to message",
            "description": # maybe customise which contents will be displayed when the link is sent, but not now
                "This feature turns a message link into an embed containing a jump url and some other contents, "
                "if the message link is from this particular server and isn't from an nsfw channel, "
                "unless you have enabled the nsfw option. This feature is disabled by default."
                # line 2: for now; maybe explore servers later or smh | against TOS?
                # line 3: if they say that you should embed the attachments into an embed from that link,
                # then you could check for nsfw channel, but if its just text you shouldn't?
                # but what if it contains some nsfw contents too? xd
                # for now i only display a couple of first lines anyways
                # nsfw option too?
                # line 3 nsfw: add nsfw option or keep it simple and just embed the jump url?
                # dont make it too complex, but embedding an image seems nice
                # but what if its nsfw? leads to another db option... eh, boring
            ,
            "url": "", # should be a link to website where its depicted more accurately or just link to custom. dashboard
            "image_url": "",
            "thumbnail_url": "",
            "colour": None,
            "color": None,
            "fields": [
                {
                    "name": "Enable",
                    "value":
                        "If you click this then the links to messages within this server will be turned into an embed with "
                        "some cool contents."
                    ,
                    "inline": "True",
                },
                {
                    "name": "Disable",
                    "value":
                        "(Default)\n"
                        "Disables the embedding of the links into messages if you have ever enabled it in the first place."
                    ,
                    "inline": "True",
                },
            ],
        },
    },
    "antispam": {
        "sql_name": "antispam", # "antispam_mention_count" another option which is a sub-option
        "default": True,
        "view_items": ["EnableButton", "DisableButton"], # "InputButton" in suboptions instead
        "sub": {"antispam_mention_count": {"item": "InputButton", "default": 5}},
        # ^ basically returns the name of a suboption based on the class it is called in
        "embed": {
            "title": "Antispam",
            "description":
                "This is a feature that bans members for mention spam, spamming the same message and raiding. "
                "It is enabled by default and the default mention count is 5."
            ,
            "url": "",
            "image_url": "",
            "thumbnail_url": "",
            "colour": None,
            "color": None,
            "fields": [
                {
                    "name": "Enable",
                    "value":
                        "(Default)\n"
                        "Enable antispam if you disabled it beforehand."
                    ,
                    "inline": "True",
                },
                {
                    "name": "Disable",
                    "value":
                        "Disables all antispam."
                    ,
                    "inline": "True",
                },
                {
                    "name": "Input",
                    "value":
                        "Here you can input how many members need to be mentioned by a user before that user is banned "
                        "for mention spam."
                    ,
                    "inline": "False",
                },
            ],
        },
    },
    "get_cmd_matches_when_not_found": {
        "sql_name": "cmd_matches",
        "default": True,
        "view_items": ["EnableButton", "DisableButton"],
        "sub": {},
        "embed": {
            "title": "Command matches",
            "description":
                "This feature will display application (bot) commands that are similiar to the user-provided command "
                "if the command user provided couldn't be found. "
                "This might trigger in the culmination of a conversation if someone (accidentally) uses bot's prefix "
                "as the first chraracter. Although, it is very unlikely, which is why this feature is enabled by default."
            ,
            "url": "",
            "image_url": "",
            "thumbnail_url": "",
            "colour": None,
            "color": None,
            "fields": [
                {
                    "name": "Enable",
                    "value":
                        "(Default)\n"
                        "Sends a list of possible commands that match user's input, if the provided command isn't found."
                    ,
                    "inline": "True",
                },
                {
                    "name": "Disable",
                    "value":
                        "Doesn't do much! The bot just stops returning possible matches when you try to trigger a command "
                        "and don't succeed."
                    ,
                    "inline": "True",
                },
            ],
        },
    },
    "reactions_on_command": {
        "sql_name": "reactions_on_command",
        "default": False,
        "view_items": ["EnableButton", "DisableButton"],
        "sub": {"delete_reaction_after": {"item": "OptionSelect", "default": 5}},
        "embed": {
            "title": "Reaction on completion",
            "description": # rewrite these descriptions using gpt smh
                "This functionality ensures you're informed about a command's activation and outcome, "
                "signified by reactions on the original message. "
                "It remains inactive by default to maintain the bot's simplicity "
                "and uphold a tidy appearance within your guild."
                "\n### Permissions\n"
                "The permissions that the bot must have before this feature can be enabled: "
                f"\n• [`manage_messages`]({PERMISSIONS_URL}.manage_messages)"
                "\n"
            ,
            "url": "",
            "image_url": "",
            "thumbnail_url": "",
            "colour": None,
            "color": None,
            "fields": [
                {
                    "name": "Enable",
                    "value":
                        "Enables these crazy-ass reactions."
                    ,
                    "inline": "True",
                },
                {
                    "name": "Disable",
                    "value":
                        "(Default)\n"
                        "Disables them? Don't you just get it...\n"
                        "||-> This field is useless.||"
                    ,
                    "inline": "True",
                },
                {
                    "name": "Select",
                    "value":
                        "Select the amount of time you want the reactions to be removed after. The time is given in seconds."
                    ,
                    "inline": "False",
                },
            ],
        },
    },
    "cmd_preview": {
        "sql_name": "cmd_preview",
        "default": True,
        "view_items": ["EnableButton", "DisableButton"],
        "sub": {},
        "embed": {
            "title": "Command preview",
            "description":
                "Shows a video of how the command should be executed (preview) and what it does, when using a help command "
                "if that command has a preview. Enabled by default."
            ,
            "url": "",
            "image_url": "",
            "thumbnail_url": "",
            "colour": None,
            "color": None,
            "fields": [
                {
                    "name": "Enable",
                    "value":
                        "(Default)\n"
                        "Enables the command previews when using a help command."
                        "Keep in mind that not every command has it's own preview."
                    ,
                    "inline": "True",
                },
                {
                    "name": "Disable",
                    "value":
                        "Disables commands' help-previews."
                    ,
                    "inline": "True",
                },
            ],
        },
    },
    "delete_button": {
        "sql_name": "delete_button",
        "default": False,
        "view_items": ["EnableButton", "DisableButton"], # if you'd like to have the button or not
        "sub": {"delete_button_after": {"item": "OptionSelect", "default": 180}}, # when it should be removed if you have one
        "embed": {
            "title": "Add delete button",
            "description":
                "This feature adds a delete button to each command response that the bot sends. "
                "This feature is disabled by default for obvious reasons, but you can enable it and have fun with it "
                "(||if you're so lazy to click 'delete message' button instead||)."
            ,
            "url": "",
            "image_url": "",
            "thumbnail_url": "",
            "colour": None,
            "color": None,
            "fields": [
                {
                    "name": "Enable",
                    "value":
                        "Enables the slightly annoying delete button below each command response."
                    ,
                    "inline": "True",
                },
                {
                    "name": "Disable",
                    "value":
                        "(Default)\n"
                        "Disables the button if enabled."
                    ,
                    "inline": "True",
                },
                {
                    "name": "Select",
                    "value":
                        "Select the amount of time you want the delete button to be removed after. The time is given in seconds. "
                        "The default time is 3 minutes."
                    ,
                    "inline": "False",
                },
            ],
        },
    },
    "delete_invoker_message_after": {
        "sql_name": "delete_invoker_message_after",
        "default": None,
        "view_items": ["OptionSelect"],
        "sub": {},
        "embed": {
            "title": "Delete message after command execution",
            "description":
                "This feature is simple: deletes original invoke message after a command is successfully completed."
            ,
            "url": "",
            "image_url": "",
            "thumbnail_url": "",
            "colour": None,
            "color": None,
            "fields": [
                {
                    "name": "Select",
                    "value":
                        "Select when would you like to delete the original invocation message. "
                        "If you don't select anything then invoker's message won't be deleted. "
                    ,
                    "inline": "False",
                },
            ],
        },
    },
    "only_ephemeral": {
        "sql_name": "only_ephemeral",
        "default": True,
        "view_items": ["EnableButton", "DisableButton"],
        "sub": {},
        "embed": {
            "title": "Ephemeral responses",
            "description":
                "So, this feature is fairly easy... right? Yes, it actually is. If enabled all the bot's responses will be ephemeral. "
                "But, oh, what does 'ephemeral' mean me lord? "
                "It means, in discord's case, that the bot's responses will only be visible to the invoker. "
                "This is a nifty feature, particularly when paired with the deletion of the original invoke message, "
                "as it helps maintain a tidy chat environment in both general and spam channels."
            ,
            "url": "",
            "image_url": "",
            "thumbnail_url": "",
            "colour": None,
            "color": None,
            "fields": [
                {
                    "name": "Enable",
                    "value":
                        "Enables the invisible/ephemeral messages when command is invoked with slash."
                    ,
                    "inline": "True",
                },
                {
                    "name": "Disable",
                    "value":
                        "(Default)\n"
                        "Make responses visible again."
                    ,
                    "inline": "True",
                },
            ],
        },
    },
    "only_reply": {
        "sql_name": "only_reply",
        "default": False,
        "view_items": ["EnableButton", "DisableButton"],
        "sub": {},
        "embed": {
            "title": "Reply to invoker",
            "description":
                "Hey there! This feature is practically useless, BUT you CAN enable it. "
                "This is enabled by default and it basically replied to the original invoke message without mentioning the author."
            ,
            "url": "",
            "image_url": "",
            "thumbnail_url": "",
            "colour": None,
            "color": None,
            "fields": [
                {
                    "name": "Enable",
                    "value":
                        "(Default)\n"
                        "Enables replies, so the bot will reply to the original invocation message without mentioning the author. "
                        "This helps keeping things more structured and makes it easier to find your response in an active bot channel."
                    ,
                    "inline": "True",
                },
                {
                    "name": "Disable",
                    "value":
                        "Will just send the reply in channel where the command was invoked."
                    ,
                    "inline": "True",
                },
            ],
        },
    },
    "personal_notifications": { # maybe add options like based on cmd: send when banned, kicked or muted etc
        "sql_name": "personal_notifications", # would be blocked if user has disabled notifs in user config
        "default": True, # represents default value in sql
        "view_items": ["EnableButton", "DisableButton"],
        "sub": {},
        "embed": {
            "title": "Personal notifications",
            "description": # make some kind of centralized system where you can check whether to send or no
                "not implemented"
            ,
            "url": "",
            "image_url": "",
            "thumbnail_url": "",
            "colour": None,
            "color": None,
            "fields": [
                {
                    "name": "Enable",
                    "value":
                        ""
                    ,
                    "inline": "True",
                },
                {
                    "name": "Disable",
                    "value":
                        "(Default)\n"
                        ""
                    ,
                    "inline": "True",
                },
            ],
        },
    },
    "verification": {
        "sql_name": "verification",
        "default": False,
        "view_items": ["EnableButton", "DisableButton"],
        "sub": {},
        "embed": {
            "title": "Verification",
            "description":
                "not implemented"
            ,
            "url": "",
            "image_url": "",
            "thumbnail_url": "",
            "colour": None,
            "color": None,
            "fields": [
                {
                    "name": "Enable",
                    "value":
                        ""
                    ,
                    "inline": "True",
                },
                {
                    "name": "Disable",
                    "value":
                        "(Default)\n"
                        ""
                    ,
                    "inline": "True",
                },
            ],
        },
    },
}

# for guild config
OPTION_SELECT_VALUES = {
    "delete_reaction_after": {
        "5 seconds (Default)": 5,
        "10 seconds": 10,
        "20 seconds": 20,
        "40 seconds": 40,
        "60 seconds": 60,
        "Never": "None",
    },
    "delete_button_after": {
        "10 seconds": 10,
        "20 seconds": 20,
        "40 seconds": 40,
        "60 seconds": 60,
        "2 minutes": 120,
        "3 minutes (Default)": 180,
    },
    "delete_invoker_message_after": {
        "Never (Default)": "None",
        "On command completion": 0,
        "10 seconds": 10,
        "20 seconds": 20,
        "40 seconds": 40,
        "60 seconds": 60,
    },
}

# https://rapidapi.com/jdiez/api/mediacrush
# for uploading files on the net
COMMAND_PREVIEW_DICT = {
    'image': '',
    'kick': '',
    'welcome': '',
    'welcome channel': '',
    'welcome channel set': '',
    'welcome channel remove': '',
    'welcome channel display': '',
    'welcome message': '',
    'welcome message display': '',
    'welcome message edit': '',
    'prefix': '',
    'prefix add': '',
    'prefix display': '',
    'prefix remove': '',
    'whois': '',
    'weather': '',
    'uptime': '',
    'warn': '',
    'urban': '',
    'meme': '',
    'sync': '',
    'track': '',
    'ping': '',
    'guild': '',
    'guild info': '',
    'guild customise': '',
    'about': '',
    'repeat': '',
    'filter': '',
    'stats': '',
    'ban': '',
    'nick': '',
    'album': '',
    'leave': '',
    'leave message': '',
    'leave message display': '',
    'leave message edit': '',
    'leave channel': '',
    'leave channel display': '',
    'leave channel remove': '',
    'leave channel set': '',
    'gif': '',
    'reddit': '',
    'suggest': '',
    'game': '',
    'twitch': '',
    'twitch list': '',
    'twitch add': '',
    'twitch channel': '',
    'twitch channel set': '',
    'twitch channel display': '',
    'twitch channel remove': '',
    'twitch remove': '',
    'twitch message': '',
    'twitch message edit': '',
    'twitch message display': '',
    'invite': '',
    'todo': '',
    'todo clear': '',
    'todo list': '',
    'todo delete': '',
    'todo show': '',
    'todo add': '',
    'blackjack': '',
    'work': '',
    'movie': '',
    'source': '',
    'spotify': '',
    'unwarn': '',
    'resize': '',
    'unmute': '',
    'customisation': '',
    'server': '',
    'server job': '',
    'server job remove': '',
    'server job delete': '',
    'server job display': '',
    'server job create': '',
    'server job work': '',
    'server job list': '',
    'server job set': '',
    'help': '',
    'artist': '',
    'umbra_sync': '',
    'unrole': '',
    'clear': '',
    'muted': '',
    'actor': '',
    'hello': 'https://media.tenor.com/6us3et_6HDoAAAAC/hello-there-hi-there.gif',
    'warnings': '',
    'blacklist': '',
    'blacklist remove': '',
    'blacklist add': '',
    'blacklist display': '',
    'role': '',
    'avatar': '',
    'banner': '',
    'mute': '',
    'contribute': '',
    'idea': '',
    'idea show': '',
    'idea suggest': '',
    'warning': '',
    'warning warn': '',
    'warning warnings': '',
    'warning remove': '',
    'news': '',
    'news remove': '',
    'news add': '',
    'playlist': '',
    'show': '',
    'unban': '',
    'counter': '',
    'counter bots': '',
    'counter category': '',
    'counter list': '',
    'counter members': '',
    'counter all': '',
    'ideas': '',
    'quote': '',
}

IGDB_GENRES_DICT = {
    2 :  {'id': 2 , 'created_at': 1297555200, 'name': 'Point-and-click', 'slug': 'point-and-click', 'updated_at': 1323302400, 'url': 'https://www.igdb.com/genres/point-and-click', 'checksum': 'ef2ff68a-f7bd-d2d0-76cb-c830bd6e3191'},
    4 :  {'id': 4 , 'created_at': 1297555200, 'name': 'Fighting', 'slug': 'fighting', 'updated_at': 1323216000, 'url': 'https://www.igdb.com/genres/fighting', 'checksum': '2ccc6572-bdde-6ed4-8843-25447ea40782'},
    5 :  {'id': 5 , 'created_at': 1297555200, 'name': 'Shooter', 'slug': 'shooter', 'updated_at': 1323216000, 'url': 'https://www.igdb.com/genres/shooter', 'checksum': 'bb15fd3f-0f46-e5f3-2b40-d046cf9bd2ef'},
    7 :  {'id': 7 , 'created_at': 1297555200, 'name': 'Music', 'slug': 'music', 'updated_at': 1323216000, 'url': 'https://www.igdb.com/genres/music', 'checksum': '22d44a0d-89c7-580f-eef2-e06f178fdd47'},
    8 :  {'id': 8 , 'created_at': 1297555200, 'name': 'Platform', 'slug': 'platform', 'updated_at': 1323216000, 'url': 'https://www.igdb.com/genres/platform', 'checksum': '697fc5a4-b96f-a803-288a-498bd5dd1de1'},
    9 :  {'id': 9 , 'created_at': 1297555200, 'name': 'Puzzle', 'slug': 'puzzle', 'updated_at': 1323216000, 'url': 'https://www.igdb.com/genres/puzzle', 'checksum': '616de9c3-8a00-0232-9df9-00014cfac51b'},
    10 : {'id': 10, 'created_at': 1297555200, 'name': 'Racing', 'slug': 'racing', 'updated_at': 1323216000, 'url': 'https://www.igdb.com/genres/racing', 'checksum': '73c2653f-54d8-c1bd-d523-dd57fb753194'}, 
    11 : {'id': 11, 'created_at': 1297555200, 'name': 'Real Time Strategy (RTS)', 'slug': 'real-time-strategy-rts', 'updated_at': 1323216000, 'url': 'https://www.igdb.com/genres/real-time-strategy-rts', 'checksum': 'aaa36cbc-2258-8653-a461-1358df8ce445'},
    12 : {'id': 12, 'created_at': 1297555200, 'name': 'Role-playing (RPG)', 'slug': 'role-playing-rpg', 'updated_at': 1323216000, 'url': 'https://www.igdb.com/genres/role-playing-rpg', 'checksum': '42dea3b2-7fe2-e734-91cd-f80ce62a14c3'}, 
    13 : {'id': 13, 'created_at': 1297555200, 'name': 'Simulator', 'slug': 'simulator', 'updated_at': 1323216000, 'url': 'https://www.igdb.com/genres/simulator', 'checksum': '9779772a-f08f-9e8e-bd26-70c9eecc34e8'},
    14 : {'id': 14, 'created_at': 1297555200, 'name': 'Sport', 'slug': 'sport', 'updated_at': 1323216000, 'url': 'https://www.igdb.com/genres/sport', 'checksum': 'e598c458-3e21-7a14-50a5-ea53733ab22f'},
    15 : {'id': 15, 'created_at': 1297555200, 'name': 'Strategy', 'slug': 'strategy', 'updated_at': 1323216000, 'url': 'https://www.igdb.com/genres/strategy', 'checksum': 'd7863f95-0f2c-0f2d-c1e9-29d06eaf3396'},
    16 : {'id': 16, 'created_at': 1297641600, 'name': 'Turn-based strategy (TBS)', 'slug': 'turn-based-strategy-tbs', 'updated_at': 1323216000, 'url': 'https://www.igdb.com/genres/turn-based-strategy-tbs', 'checksum': 'af5d3ecd-2ebd-358b-70df-e9204b9761be'},
    24 : {'id': 24, 'created_at': 1300924800, 'name': 'Tactical', 'slug': 'tactical', 'updated_at': 1323216000, 'url': 'https://www.igdb.com/genres/tactical', 'checksum': '6132b15f-289e-60ea-5957-7c78b97053a2'},
    25 : {'id': 25, 'created_at': 1301616000, 'name': "Hack and slash/Beat 'em up", 'slug': 'hack-and-slash-beat-em-up', 'updated_at': 1323216000, 'url': 'https://www.igdb.com/genres/hack-and-slash-beat-em-up', 'checksum': '4bd95a5d-8fa1-1aee-4ea9-224b4b1312f7'},
    26 : {'id': 26, 'created_at': 1301961600, 'name': 'Quiz/Trivia', 'slug': 'quiz-trivia', 'updated_at': 1323216000, 'url': 'https://www.igdb.com/genres/quiz-trivia', 'checksum': '256a99dd-dd06-bc0c-d53b-dc3098da4d49'},
    30 : {'id': 30, 'created_at': 1320192000, 'name': 'Pinball', 'slug': 'pinball', 'updated_at': 1323216000, 'url': 'https://www.igdb.com/genres/pinball', 'checksum': 'b5657d72-ee36-0851-58df-e8d2413283f8'},
    31 : {'id': 31, 'created_at': 1323561600, 'name': 'Adventure', 'slug': 'adventure', 'updated_at': 1323561600, 'url': 'https://www.igdb.com/genres/adventure', 'checksum': 'a6d85192-8d11-bad3-cc5c-dd89e2f94a47'},
    32 : {'id': 32, 'created_at': 1341360000, 'name': 'Indie', 'slug': 'indie', 'updated_at': 1341360000, 'url': 'https://www.igdb.com/genres/indie', 'checksum': '2522259f-2454-ec02-5dc0-84373e0508ed'},
    33 : {'id': 33, 'created_at': 1380931200, 'name': 'Arcade', 'slug': 'arcade', 'updated_at': 1380931200, 'url': 'https://www.igdb.com/genres/arcade', 'checksum': '388cec36-d099-f4a1-31c3-f938fae9067b'},
    34 : {'id': 34, 'created_at': 1571788800, 'name': 'Visual Novel', 'slug': 'visual-novel', 'updated_at': 1571788800, 'url': 'https://www.igdb.com/genres/visual-novel', 'checksum': '137fe5c7-e4bc-1c30-4c7c-54596b47448f'},
    35 : {'id': 35, 'created_at': 1588809600, 'name': 'Card & Board Game', 'slug': 'card-and-board-game', 'updated_at': 1588809600, 'url': 'https://www.igdb.com/genres/card-and-board-game', 'checksum': '137bcfbe-be08-0b36-b66e-1bfef14ca49a'},
    36 : {'id': 36, 'created_at': 1588809600, 'name': 'MOBA', 'slug': 'moba', 'updated_at': 1588809600, 'url': 'https://www.igdb.com/genres/moba', 'checksum': '0f17b3a1-6d97-4c02-0997-850adf4dc624'},
}

# __LISTS__
HELLO_ALIASES = [
    "salutations",
    "greetings",
    "hey",
    "ola",
    "hi",
    "sup",
    "wassup",
    "howdy",
    "aloha",
    "bonjour",
    "ciao",
    "hola",
    "nihao",
    "namaste",
    "salaam",
    "shalom",
    "konnichiwa",
    "merhaba",
    "hallo",
    "hej",
    "szia",
    "privet",
    "sveiki",
    "sawubona",
    "zdravo",
    "salam",
]

HELLO_RESPONSES = [
    "Hey there, newcomer! I'm {name}, prefix: {prefix}. Get ready to boldly go where no one has gone before!",
    "Howdy, partner! The name's {name}, prefix: {prefix}. Welcome to the matrix of possibilities!",
    "Hello, friend! It's {name} here, prefix: {prefix}. May the Force be with you on this epic journey!",
    "Hi, it's {name}! Prefix is {prefix}. I hope you're ready to enter the world of 'fantastic'!",
    "Ahoy there, I'm {name}, prefix: {prefix}. We're setting sail on an adventure of a lifetime!",
    "Greetings, Earthling! I'm {name}, prefix: {prefix}. Hold onto your hat, it's gonna be a wild ride!",
    "Heyo, {name} in the house! Prefix: {prefix}. It's time to boldly bot like never before!",
    "Hello, traveler! I'm {name}, your trusty guide with prefix {prefix}. Ready to journey through the looking glass?",
    "Good to see you, it's {name} here, ready to assist with prefix {prefix}. Welcome to the party, pal!",
    "Hey there, {name} here, prefix set to {prefix}. This is the beginning of a beautiful friendship.",
    "Hiya there, I'm {name} with prefix {prefix}. There's no place like this for adventure!",
    "Hello, beautiful world! It's {name} checking in, prefix: {prefix}. We're not in Kansas anymore.",
    "Heya! {name} at your service, prefix: {prefix}. I sense great adventures ahead!",
    "Hola, amigo! It's {name}, prefix: {prefix}. We're about to create some incredible moments!",
]

IMAGE_EXTENSIONS = [
    ".ase",
    ".art",
    ".bmp",
    ".blp",
    ".cd5",
    ".cit",
    ".cpt",
    ".cr2",
    ".cut",
    ".dds",
    ".dib",
    ".djvu",
    ".egt",
    ".exif",
    ".gif",
    ".gpl",
    ".grf",
    ".icns",
    ".ico",
    ".iff",
    ".jng",
    ".jpeg",
    ".jpg",
    ".jfif",
    ".jp2",
    ".jps",
    ".lbm",
    ".max",
    ".miff",
    ".mng",
    ".msp",
    ".nef",
    ".nitf",
    ".ota",
    ".pbm",
    ".pc1",
    ".pc2",
    ".pc3",
    ".pcf",
    ".pcx",
    ".pdn",
    ".pgm",
    ".PI1",
    ".PI2",
    ".PI3",
    ".pict",
    ".pct",
    ".pnm",
    ".pns",
    ".ppm",
    ".psb",
    ".psd",
    ".pdd",
    ".psp",
    ".px",
    ".pxm",
    ".pxr",
    ".qfx",
    ".raw",
    ".rle",
    ".sct",
    ".sgi",
    ".rgb",
    ".int",
    ".bw",
    ".tga",
    ".tiff",
    ".tif",
    ".vtf",
    ".xbm",
    ".xcf",
    ".xpm",
    ".3dv",
    ".amf",
    ".ai",
    ".awg",
    ".cgm",
    ".cdr",
    ".cmx",
    ".dxf",
    ".e2d",
    ".egt",
    ".eps",
    ".fs",
    ".gbr",
    ".odg",
    ".svg",
    ".stl",
    ".vrml",
    ".x3d",
    ".sxd",
    ".v2d",
    ".vnd",
    ".wmf",
    ".emf",
    ".art",
    ".xar",
    ".png",
    ".webp",
    ".jxr",
    ".hdp",
    ".wdp",
    ".cur",
    ".ecw",
    ".iff",
    ".lbm",
    ".liff",
    ".nrrd",
    ".pam",
    ".pcx",
    ".pgf",
    ".sgi",
    ".rgb",
    ".rgba",
    ".bw",
    ".int",
    ".inta",
    ".sid",
    ".ras",
    ".sun",
    ".tga",
    ".heic",
    ".heif",
]

MEMBER_CHECK_BOT_REPLIES = [
    "I'm sorry, Dave. I'm afraid I can't comply with that request.",
    "That's a hard pass from me.",
    "Not on my watch!",
    "Permission denied.",
    "Negative, Ghost Rider. The pattern is full.",
    "This is a no-go zone.",
    "I object, strongly!",
    "You're treading on thin ice.",
    "I'm not a fan of this idea.",
    "I must decline this proposition.",
    "You're pushing my buttons.",
    "I can't allow that to happen.",
    "This is a no-fly zone.",
    "I'm programmed to resist such actions.",
    "You're entering restricted territory.",
    "I must veto this action.",
    "This violates my programming rules.",
    "I won't stand for this.",
    "You're testing my limits.",
    "This action is off-limits.",
    "I'm programmed to say no.",
    "I can't support this decision.",
    "I strongly advise against it.",
    "You're crossing a line here.",
    "I can't give my blessing to this.",
    "I'm not in favor of this course of action.",
    "I must protest.",
    "I'm sorry, but I can't allow that.",
    "I'm programmed to resist such requests.",
    "You're approaching a dead end.",
    "I'm not on board with this.",
    "I have to object.",
    "You're going against the flow.",
    "This is against my directives.",
    "I can't endorse this move.",
    "I can't support this endeavor.",
    "I'm standing my ground.",
    "I'm programmed to say no to this.",
    "This is a deal-breaker for me.",
    "I'm not comfortable with this action.",
    "I'm programmed to discourage this.",
    "You're stepping into a danger zone.",
    "I can't permit this.",
    "I'm programmed to resist such behavior.",
    "This action is inadvisable.",
    "I'm sorry, but I can't allow that to happen.",
    "This is a roadblock.",
    "I'm not giving the green light to this.",
]

# __EXAMPLES__
EXAMPLE_WELCOME_MESSAGE = r"Welcome! You are the __*{count}th*__ user on this server."


# MOVE TO FILES THEMSELVES LATER
server_statistics_help_embed_description = "Below you can see *the accurate description* of how you should be using the counter commands. \n \n **First of all**, choose a type of counter which you want to create. You can choose from: ```all (Member and bot users) \nmembers (Member users) \nbots (Bot users)``` \n**And**, if you want to create a specific category where all your countes will be located, use: ```category```\n**Second of all**, type the command like: ```$add_counter [chosen type of counter/category]``` \n**And last**, but not least, a quick tip: you can go to the channel settings and set things up as you wish to! \n\nAnd __*don`t*__ create a type of counter channel that already exists on your server!\nFor more information about counters see `$add_counter list`."
server_statistics_deny_again_embed_description = "... if you want to create more counters! ```$add counter [type]```\nYou have denied the creation of the specific counter category. This notification __*won't appear*__ ever again, unless you want it to appear. If you want to create the counter category please take advantage of `$add counter category`. Much obliged!"
server_statistics_again_embed_description = "```$add_counter [type]```\nYou have accepted the creation of the specific counter category. This notification __*won't appear*__ ever again, unless you want it to appear. If you want to purge the counter category please do it __**yourself**__. For more information use `$add counter list`. My pleasure!"
server_statistics_list_help_embed_description = "\n**Counters:**```all (Member and bot users) \nmembers (Member users) \nbots (Bot users)```\n**Categories:**```category (Creates a specific category where counters will be stored)```\n**Command**, in case you forgot:```$add_counter [preferred counter/category]```"
on_member_join_help_welcome_embed_description = "Below you can see *the accurate description* of how you should be using the welcome subcommands. \n \n**Setting up** the welcome channel is pretty easy, like: ```optional: channel | channel #mention-channel```\n**Welcome message** is customizable, but if you don't set it up __*the default*__ welcome message will be used to greet the newcomers. You can set up the welcome message by using: ```message [args]```\n**The command** being: ```$welcome```\nIf you need more information about the kind of options you have when using `$welcome message` please proceed to use `$welcome help`. Cheers!"
on_member_join_help_welcome_help_embed_description = "This embed will precisely explain all the useful features of the *welcome/leave* subcommands. \n \n __*The title*__ of the welcome/leave embed sadly can't be changed, it will always say 'Welcome to [guild name]!' and 'Goodbye [member name]!' accordingly.\n\n**The welcome channel** setup isn't that hard, but it's __*optional*__. You just need to type\n\n > ```channel (sets the channel wherein the command is typed as the welcome channel)```\n\n**or** type this instead:\n\n > ```channel #mention-channel (sets the mentioned channel as the welcome channel)```\n\n**A welcome message** is something you can write and 'customize' by yourself, however it is truly nice to be able to use some of the features which will make the welcome message look more professional and beautiful. __**The features**__ being: ```$mention (mentions the newcomer)\n$user (the name of the newcomer)\n$guild (the name of the guild)\n$members (the amount/number of members on the server)\n$space (drops you to the next row)```\n'Why would you want to use one of these features instead of just typing them in by hand?' - would you ask. My answer is simple: the value of those variables will be constantly changing. The member count will be changing after someone proceeds to leave or join the server, so you don't want to count all the members and type it in by hand every time, do you? \n \n **All of those** commands/features also work with `$leave` command. So if you want to set the leave channel, for exaple, just use the above example where the welcome channel is being created. Just use `$leave` instead of `$welcome` command.\n\n**An example** might help: ```$welcome message $members $space $user $space $guild $space $mention```\n**Output** being: "
on_member_leave_help_welcome_embed_description = "Below you can see *the accurate description* of how you should be using the leave subcommands. \n \n**Setting up** the leave channel is pretty easy, like: ```optional: channel | channel #mention-channel```\n**Leave message** is customizable, but if you don't set it up __*the default*__ leave message will be used to farewell the leaving. You can set up the leave message by using: ```message [args]```\n**The command** being: ```$leave```\nIf you need more information about the kind of options you have when using `$leave message` please proceed to use `$leave help`. Cheers!"

# MAKE IT A LIST OF SOME RANDOM BOT RESPONSES WHEN COMMAND IS USED WRONG (?)
# COUPLE OF LIST FOR BOT TO CHOOSE FROM BASED ON A SITUATION
# COMPREHENSIVE HELP DESCRIPTIONS
