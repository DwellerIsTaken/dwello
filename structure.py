# -> MESSAGE RETURN FORMAT
    # | Success: send an embed - not necessarily with a title - in both cases
    # | Error: slash - use an ephemeral reply, prefix - use a reply with mention_author = True
    # | Moderation: slash - return an ephemeral reply to the invoker, prefix - return reply with mention_author = False
    #      * extra - embed in ctx.channel with invoker.mention to let everyone know someone used moderation command (we could make it a customisable feature: 
    #           • send msg directly to invoker and not in guild,
    #           • or both, or neither and it will be displayed in audit_logs,
    #           • or let owner create admin channel where all the moderator actions will be displayed)
    # | Embeds: try to create separate string vars to store embed's description and plit them, stringvar = ("" ""), to save space
    
# -> GROUPS/SUBGROUPS
    # | Invoke: invoke_without_command = True, with_app_command = True
    # | Return: return either a help (command) message or invoke some representative command within that group/subgroup