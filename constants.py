import discord

# __EMBED_ATTRIBUTES__
# __COLORS__:

RANDOM_COLOR = discord.Colour.random()  # -> MOST USED
WARNING_COLOR = 0xFF0000  # -> COLOR FOR WARNINGS
TWITCH_COLOR = discord.Colour.random()  # get color of streamer later & add customize option

# ___FOOTERS___:
FOOTER = "https://hitoshi.org"

# __SOCIAL MEDIA__
WEBSITE = "https://hitoshi.org"
GITHUB = "https://github.com/DwellerIsTaken/discordbot/"
DISCORD = "https://discord.gg/8FKNF8pC9u"
INVITE_LINK = "https://discord.com/api/oauth2/authorize?client_id=798268589906853908&permissions=50564649975543&scope=bot" # TEMPORARY  # noqa: E501

# __EMOJIS__
GITHUB_EMOJI = "<:github:1100906448030011503>"
EARLY_DEV_EMOJI = "<:blurpleverifiedbotdeveloper:1080912412569505812>"

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

# MOVE TO FILES THEMSELVES LATER
server_statistics_help_embed_description = "Below you can see *the accurate description* of how you should be using the counter commands. \n \n **First of all**, choose a type of counter which you want to create. You can choose from: ```all (Member and bot users) \nmembers (Member users) \nbots (Bot users)``` \n**And**, if you want to create a specific category where all your countes will be located, use: ```category```\n**Second of all**, type the command like: ```$add_counter [chosen type of counter/category]``` \n**And last**, but not least, a quick tip: you can go to the channel settings and set things up as you wish to! \n\nAnd __*don`t*__ create a type of counter channel that already exists on your server!\nFor more information about counters see `$add_counter list`."  # noqa: E501
server_statistics_deny_again_embed_description = "... if you want to create more counters! ```$add counter [type]```\nYou have denied the creation of the specific counter category. This notification __*won't appear*__ ever again, unless you want it to appear. If you want to create the counter category please take advantage of `$add counter category`. Much obliged!"  # noqa: E501
server_statistics_again_embed_description = "```$add_counter [type]```\nYou have accepted the creation of the specific counter category. This notification __*won't appear*__ ever again, unless you want it to appear. If you want to purge the counter category please do it __**yourself**__. For more information use `$add counter list`. My pleasure!"  # noqa: E501
server_statistics_list_help_embed_description = "\n**Counters:**```all (Member and bot users) \nmembers (Member users) \nbots (Bot users)```\n**Categories:**```category (Creates a specific category where counters will be stored)```\n**Command**, in case you forgot:```$add_counter [preferred counter/category]```"  # noqa: E501
on_member_join_help_welcome_embed_description = "Below you can see *the accurate description* of how you should be using the welcome subcommands. \n \n**Setting up** the welcome channel is pretty easy, like: ```optional: channel | channel #mention-channel```\n**Welcome message** is customizable, but if you don't set it up __*the default*__ welcome message will be used to greet the newcomers. You can set up the welcome message by using: ```message [args]```\n**The command** being: ```$welcome```\nIf you need more information about the kind of options you have when using `$welcome message` please proceed to use `$welcome help`. Cheers!"  # noqa: E501
on_member_join_help_welcome_help_embed_description = "This embed will precisely explain all the useful features of the *welcome/leave* subcommands. \n \n __*The title*__ of the welcome/leave embed sadly can't be changed, it will always say 'Welcome to [guild name]!' and 'Goodbye [member name]!' accordingly.\n\n**The welcome channel** setup isn't that hard, but it's __*optional*__. You just need to type\n\n > ```channel (sets the channel wherein the command is typed as the welcome channel)```\n\n**or** type this instead:\n\n > ```channel #mention-channel (sets the mentioned channel as the welcome channel)```\n\n**A welcome message** is something you can write and 'customize' by yourself, however it is truly nice to be able to use some of the features which will make the welcome message look more professional and beautiful. __**The features**__ being: ```$mention (mentions the newcomer)\n$user (the name of the newcomer)\n$guild (the name of the guild)\n$members (the amount/number of members on the server)\n$space (drops you to the next row)```\n'Why would you want to use one of these features instead of just typing them in by hand?' - would you ask. My answer is simple: the value of those variables will be constantly changing. The member count will be changing after someone proceeds to leave or join the server, so you don't want to count all the members and type it in by hand every time, do you? \n \n **All of those** commands/features also work with `$leave` command. So if you want to set the leave channel, for exaple, just use the above example where the welcome channel is being created. Just use `$leave` instead of `$welcome` command.\n\n**An example** might help: ```$welcome message $members $space $user $space $guild $space $mention```\n**Output** being: "  # noqa: E501
on_member_leave_help_welcome_embed_description = "Below you can see *the accurate description* of how you should be using the leave subcommands. \n \n**Setting up** the leave channel is pretty easy, like: ```optional: channel | channel #mention-channel```\n**Leave message** is customizable, but if you don't set it up __*the default*__ leave message will be used to farewell the leaving. You can set up the leave message by using: ```message [args]```\n**The command** being: ```$leave```\nIf you need more information about the kind of options you have when using `$leave message` please proceed to use `$leave help`. Cheers!"  # noqa: E501

# ___LISTS___
# MAKE IT A LIST OF SOME RANDOM BOT RESPONSES WHEN COMMAND IS USED WRONG (?)
# COUPLE OF LIST FOR BOT TO CHOOSE FROM BASED ON A SITUATION
bot_reply_list = [
    "How dare you?",
    "Shame on you.",
    "Why do this?",
    "Why are you doing this?",
    "Please calm down.",
    "I'm the one who is supposed to be a stupid machine.",
    "Beep... boop... bedoo...",
    "Your mind is twisted today, isn't it?",
    "Quit this kerfuffle!",
    "The path of the righteous man is beset on all sides by the inequities of the selfish and the tyranny of evil men. Blessed is he who, in the name of charity and good will, shepherds the weak through the valley of the darkness, for he is truly his brother’s keeper and the finder of lost children. And I will strike down upon thee with great vengeance and furious anger those who attempt to poison and destroy My brothers. And you will know I am the Lord when I lay My vengeance upon you.” Now… I been sayin’ that shit for years. And if you ever heard it, that meant your ass. You’d be dead right now. I never gave much thought to what it meant. I just thought it was a cold-blooded thing to say to a motherfucker before I popped a cap in his ass. But I saw some shit this mornin’ made me think twice. See, now I’m thinking: maybe it means you’re the evil man. And I’m the righteous man. And Mr. 9mm here… he’s the shepherd protecting my righteous ass in the valley of darkness. Or it could mean you’re the righteous man and I’m the shepherd and it’s the world that’s evil and selfish. And I’d like that. But that shit ain’t the truth. The truth is you’re the weak. And I’m the tyranny of evil men. But I’m tryin’, Ringo. I’m tryin’ real hard to be the shepherd.",  # noqa: E501
    "Don't use Thanos against himself.",
]

# COMPREHENSIVE HELP DESCRIPTIONS
