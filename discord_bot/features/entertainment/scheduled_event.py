'''from pydoc import text
from tokenize import String
from discord.ext import commands
from features.levelling.utils import levelling

class scheduled_event(commands.Cog, name = "scheduled_event"):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name = 'create_event', description="Creates a scheduled event.",with_app_command=True) 
    async def create_event(self, ctx, name: str, start_time, entity_type=..., privacy_level=..., channel=..., location=..., end_time=..., description: text, image=..., reason=None):
        async with ctx.typing():
            pass

async def setup(bot):
  await bot.add_cog(scheduled_event(bot))'''

'''import discord
import asqlite
from discord.ext import commands

#loading_emoji = '<a:loading:1011994440639971448>'

class User_Identification(discord.ui.View):
    def __init__(self):
        super().__init__()
        #self.buyer = None
        #self.seller = None

    #embed = discord.Embed(title = 'User Identification', description = f'Buyer: `None`\nSeller: `None`', color = 0x0080ff)
    embed = discord.Embed(title = 'User Identification', color = 0x0080ff)

    @discord.ui.button(label = 'I am buyer', style = discord.ButtonStyle.gray)
    async def buyer(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with asqlite.connect('main.sqlite') as connector:
            async with connector.cursor() as cursor:
                #self.buyer = interaction.user
                #self.stop()
                #interaction.embed = self.embed(title = 'User Identification', description = f'Buyer: {interaction.user.mention}\nSeller: `None`', color = 0x0080ff)
                await interaction.message.edit(embed = )

    @discord.ui.button(label = 'I am seller', style = discord.ButtonStyle.gray)
    async def seller(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with asqlite.connect('main.sqlite') as connector:
            async with connector.cursor() as cursor:
                #self.seller = interaction.user
                #self.stop()
                await interaction.message.edit(embed = discord.Embed(title = 'User Identification', description = f'Buyer: `None`\nSeller: {interaction.user.mention}', color = 0x0080ff))

class whatever(commands.Cog, name = "whatever"):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_channel_create(self,channel):
        #if channel.name.startswith('ticket-'):
            await channel.send(embed = discord.Embed(title = 'User Identification', description = 'Buyer: `None`\nSeller: `None`', color = 0x0080ff), view = User_Identification())'await asyncio.sleep(5)
            await message.delete()
            await channel.send(embed = discord.Embed(title = 'ROBLOX Limiteds Middleman System (v2.0.3)', description = 'Welcome to our new & improved Middleman system! Here we will handle any deal involving 4 or less Roblox limiteds. The system ensures the security of all our users, by taking the item(s) and holding them until the seller has been paid.', color = 0xe4741f).set_footer(text = 'Version: 2.0.3').set_thumbnail(url = 'https://tr.rbxcdn.com/e193d84b97364ffb305a46d1b698fed0/420/420/Image/Png'))
            await channel.send(embed = discord.Embed(title = 'Who are you dealing with?', description = 'eg. Ramen#9999\neg. 123456789123456789', color = 0xe4741f))
            def check(message):
                return message.channel == channel
            while True:
                message = await bot.wait_for('message', check = check)
                try:
                    user = await commands.MemberConverter().convert(await bot.get_context(message), message.content)
                    break
                except:
                    if message.author.id not in [557628352828014614, 1011978176450265179]:
                        await channel.send(embed = discord.Embed(description = 'Could not find user - it is likely they are not even in this server.', color = 0xc20802))
                        continue
            await channel.set_permissions(user, view_channel = True)
            await channel.send(embed = discord.Embed(description = 'Successfully added <@%s> to the ticket.' % user.id, color = 0xe4741f))
            view = User_Identification()
            await channel.send(embed = discord.Embed(title = 'User Identification', description = 'Buyer: `None`\nSeller: `None`', color = 0x0080ff), view = view)
            await view.wait()
            print(view.seller, view.buyer)'''

#async def setup(bot):
  #await bot.add_cog(whatever(bot))
