import os
import discord
from discord import ApplicationContext, Option
from discord.commands import SlashCommandGroup
from discord.ext import commands
import sys
sys.path.append("../utils")
from utils import lists
import utils.jsonhandler as json
from utils.sheets import create_vodsheet, open_vodsheet
from googleapiclient.errors import HttpError

# get the absolute path to the parent directory
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# load config file
config_file = os.path.join(parent_dir, 'config.json')
config = json.load_json_file(config_file)

def get_forumtag_id(name, tags):
  for tag in tags:
    if tag.name == name:
      return tag
  return None

class VoD(commands.Cog):
  
  def __init__(self, bot):
    self.bot = bot

  group = SlashCommandGroup(name="vod", description="vod management")

  @group.command(name="channel", description="set the vod submissions channel") # /vod channel ---- sub-command for setting the vod submission channel where threads will be created
  async def channel(
    self, 
    ctx: ApplicationContext, 
    channel: discord.ForumChannel
    ):
    
    # check if the user has the 'war manager' role
    role = discord.utils.find(lambda r: r.name == 'war manager', ctx.guild.roles)
    if role not in ctx.author.roles:
      return await ctx.respond("You need the 'war manager' role to use this command", ephemeral=True)
   
    # define the global config variable
    global config
    
    # get list of available channels on server
    server = self.bot.get_guild(ctx.guild.id)
    channels = [str(channel) for channel in server.forum_channels]
    
    # check if specified channel is on server
    if channel.name not in channels:
      await ctx.respond('Channel not found', ephemeral=True)
    else:
      
      # check that config dictionary exists before modifying
      if config is None:
        config = {}
     
      # update config file with new channel ID
      config['vod_channel_id'] = channel.id
      json.save_json_file(config_file, config)
      await ctx.respond(f'Thread channel set to #{channel.name}', ephemeral=True)

  @group.command(name="create", description="create a new vod submission thread") # /vod create ---- sub-command for creating a new vod submission thread
  async def create(
    self, 
    ctx: ApplicationContext, 
    territory: Option(str, description='Territory where war is located', choices=lists.territorylist, required=True), 
    type: Option(str, description='War type', choices=["Attack","Defense"], required=True), 
    result: Option(str, description='War type', choices=["Win","Loss"], required=True), 
    date: Option(str, description='War date - MM/DD', required=True)
    ):
    
    # check if the user has the 'war manager' role
    role = discord.utils.find(lambda r: r.name == 'war manager', ctx.guild.roles)
    if role not in ctx.author.roles:
      return await ctx.respond("You need the 'war manager' role to use this command", ephemeral=True)
    
    # create the thread
    thread_name = f"{territory} - {type} - {result} - {date}"
    channel = ctx.guild.get_channel(config['vod_channel_id'])
    tags = channel.available_tags
    if channel is None:
      await ctx.respond('Submission channel not found, please set a channel using /vod channel', ephemeral=True)
    else:
      try:
        default_message = f"VoD submissions for {thread_name}"
        thread = await channel.create_thread(name=thread_name, applied_tags= [get_forumtag_id(f"{territory}", tags), get_forumtag_id(f"{type}", tags), get_forumtag_id(f"{result}", tags)], content=default_message)
        
        # create the worksheet
        wks = create_vodsheet(thread_name)
        
        # add thread to thread_choices
        json.add_thread_choice(thread_name)
        await ctx.respond(f"Thread '{thread_name}' and worksheet created!", ephemeral=True)
      except HttpError as error:
        if error.resp.status == 400:
          await ctx.respond(f"A thread or worksheet with the name '{thread_name}' already exists.", ephemeral=True)
        else:
          raise error
      
  @group.command(name="submit", description="submit a vod") # /vod submit ---- sub-command for submitting a vod
  async def submit(
    self, 
    ctx: ApplicationContext, 
    war: Option(str, description='War to submit VOD for', choices=json.get_thread_choices(), required=True), 
    link: Option(str, description='VOD link', required=True)
    ):
    
    # Get the specified channel
    channel = self.bot.get_channel(config['vod_channel_id'])
    if channel is None:
        return await ctx.respond('Submission channel not found, please set a channel using /vod channel', ephemeral=True)

    # Get the list of threads in the channel
    guild = self.bot.get_guild(ctx.guild_id)
    threads = guild.threads
    channel_threads = [thread for thread in threads if thread.parent_id == channel.id]

    # Check if the specified thread name is valid
    thread_name = war
    for thread in channel_threads:
        if thread.name == thread_name:
            target_thread = thread
            break
    else:
        # Thread not found
        return await ctx.respond(f"Invalid thread name '{thread_name}'", ephemeral=True)

    # Send the VOD link to the thread
    await ctx.respond("Submitting...", ephemeral=True)
    user = ctx.author.display_name
    message = f"{user} has submitted a VOD: {link}"
    await target_thread.send(message)

    # Update the worksheet
    worksheet = open_vodsheet(thread_name)
    worksheet.insert_rows(row=1, number=1, values=[user, link])
    return await ctx.respond(f"VOD submitted to '{thread_name}'", ephemeral=True)

@commands.Cog.listener()
async def on_application_command_error(
    self, ctx: discord.ApplicationContext, error: discord.DiscordException
):
    if isinstance(error, discord.ext.commands.errors.MissingRole):
        await ctx.respond("You don't have permission to run this command!", ephemeral=True)
    else:
        # log the error
        print(f"An error occurred: {error}")
        await ctx.respond("An error occurred while running the command. Please try again later.", ephemeral=True)

def setup(bot):
    bot.add_cog(VoD(bot))