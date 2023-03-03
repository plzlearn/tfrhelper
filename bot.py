import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
load_dotenv()

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"), intents=intents)

# the elements are just the names of your .py files
cogs = ["cogs.vod", "cogs.build", "cogs.events"]

# you can also add the on_ready event as usual here if you'd like
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

for cog in cogs:
    bot.load_extension(cog) # loads in each file, Cog, that you defined in the list

bot.run(os.getenv('DISCORD_TOKEN'))