# CUSTOMIZATION/GUILD CONFIG:
# -> Channel where the actions of moderators will be displayed (should be set by owner)
# -> Create multiple guild templates and apply one of them when command is used

# HELP COMMAND:
# -> Make a short description for every command
# -> Make a comprehensive description for a group/subgroup.
#       • Group: list all subgroups and commands with their description.
#       • Subgroup: list all commands within subgroup and their descriptions.

# CREATE IPC base for web.py and look into it
# SEPARATE FILE FOR OWNER COMMS
# IF CHANNEL IS DELETED BY USER CHECK IF ITS IN DB, IF SO: UPDATE TO NULL
# WHEN YOU REPLY TO SOMEONE WITH BOT COMMAND MAKE BOT REPLY TO THE PERSON YOU REPLIED TO INSTEAD OF YOU
# contributor command which should only be used by owner that will add contibutor to contributors.txt
# user mistake return format: either embed with color=warn_color or just a message ctx.reply(user_mistake=True)
# maybe some kind of ephemeral mode for moderators
# avoid discord formatting: if smth with '`' or '*' is pushed to db it might cause formatting problems withing embeds and str
