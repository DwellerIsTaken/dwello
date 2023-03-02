import discord 
import text_variables

async def interaction_check(interaction: discord.Interaction, author: discord.User) -> bool:
    if interaction.user.id == author.id:
        return True

    else:
        missing_permissions_embed = discord.Embed(title = "Permission Denied.", description = f"You can't interact with someone else's buttons.", color = discord.Color.random())
        missing_permissions_embed.set_image(url = '\n https://cdn-images-1.medium.com/max/833/1*kmsuUjqrZUkh_WW-nDFRgQ.gif')
        missing_permissions_embed.set_footer(text=text_variables.footer)
        return await interaction.response.send_message(embed=missing_permissions_embed, ephemeral=True)