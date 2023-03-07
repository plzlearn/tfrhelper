import os
import discord
from discord import ApplicationContext, Option, Interaction, Embed, SelectOption
from discord.commands import SlashCommandGroup
from discord.ui import Button, View, Modal, InputText, Select
from discord.ext import commands
import datetime
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

class LinkModal(Modal):
    def __init__(self, thread: object, link: str) -> None:
        super().__init__(title="Vod Link:")
        self.thread = thread
        self.add_item(InputText(label="URL", style=discord.InputTextStyle.short))

    async def callback(self, interaction: Interaction):
       self.vod_link = self.children[0].value
       self.interaction = interaction
       await interaction.response.edit_message(content=f"Vod Link: {self.vod_link}", view=None, embed=None)
       self.stop()
    
class Vods(commands.Cog):
  
    def __init__(self, bot):
        self.bot = bot

    # define the thread_embed function as a top-level function within the Vods class
    async def thread_embed(self, territory=None, type=None, result=None, date=None) -> Embed:
        # create a new embed with the build information
        embed = Embed(title=f"Thread Name = {territory} - {type} - {result} - {date}", color=0xffc800)
        embed.set_thumbnail(url="https://i.imgur.com/uqeW9TO.png")
        embed.add_field(name="Territory", value=territory)
        embed.add_field(name="Type", value=type)
        embed.add_field(name="Result", value=result)
        embed.add_field(name="Date", value=date)
        return embed

    # define the vod_embed function as a top-level function within the Vods class
    async def vod_embed(self, thread=None, link=None) -> Embed:
        # create a new embed with the build information
        embed = Embed(title=f"Vod Submission", color=0xffc800)
        embed.set_thumbnail(url="https://i.imgur.com/uqeW9TO.png")
        if thread == None:
            embed.add_field(name="War", value=None)
        else:
            embed.add_field(name="War", value=thread.name)
        embed.add_field(name="Link", value=link)
        return embed 

    @commands.slash_command(name="vods", description="type /vods and the bot will guide you through the rest of the process")
    async def vods(self, ctx: ApplicationContext):
      
        # define the global config variable
        global config

        async def show_vod_menu(self, interaction: Interaction):
            vod_menu_view = View(timeout=None)
          
            # add a button for submitting a vod
            submit_vod_button = Button(custom_id="vod_submit", label="Submit VoD", emoji="📼", style=discord.ButtonStyle.primary)
            submit_vod_button.callback = lambda i: show_submission_menu(self, i)
            vod_menu_view.add_item(submit_vod_button)

            # check if the user has the 'war manager' role 
            role = discord.utils.find(lambda r: r.name == 'war manager', ctx.guild.roles)
            if role in ctx.author.roles:
              
                # add a button for creating a vod thread
                create_thread_button = Button(custom_id="thread_create", label="New Submission Thread", emoji="➕", style=discord.ButtonStyle.success)
                create_thread_button.callback = lambda i: show_thread_menu(self, i)
                vod_menu_view.add_item(create_thread_button)         
          
                # add a button for editing vod submission forum channel
                set_channel_button = Button(custom_id="channel_set", label="Set VoD Channel", emoji="📺", style=discord.ButtonStyle.secondary)
                set_channel_button.callback = lambda i: show_channel_menu(self, i)
                vod_menu_view.add_item(set_channel_button)     

            # if the user is coming back after a button press, edit the message, otherwise send a new message
            if interaction.message is not None:
                try:
                    await interaction.response.edit_message(content="Please choose an option!", view=vod_menu_view, embed=None)
                except discord.errors.InteractionResponded:
                    await interaction.followup.send(content="Please choose an option!", view=vod_menu_view, ephemeral=True)
            else:
                await interaction.response.send_message(content="Please choose an option!", view=vod_menu_view, ephemeral=True)
      
        async def show_submission_menu(self, interaction: Interaction, thread=None, link=None):
            submit_vod_view = View(timeout=None)

            # Get the specified channel
            channel = self.bot.get_channel(config['vod_channel_id'])
            if channel is None:
                return await interaction.response.edit_message(content="Submission channel not found, please contact leadership")
            
            thread_choices = json.get_thread_choices()

            # Get the list of threads in the channel
            guild = self.bot.get_guild(ctx.guild_id)
            threads = guild.threads
            channel_threads = {str(thread): thread for thread in threads if thread.parent_id == channel.id}

            # Filter the threads by name
            channel_threads_filtered = {name: thread for name, thread in channel_threads.items() if thread.name in thread_choices}
            
            thread_options = [SelectOption(label=option, value=option) for option in channel_threads_filtered.keys()]
            thread_select = Select(placeholder="War", options=thread_options, custom_id="thread_select")
            thread_select.callback = lambda i: show_submission_menu(self, i, channel_threads[thread_select.values[0]], link)
            submit_vod_view.add_item(thread_select)

            link_button = Button(custom_id="link_set", label="Vod Link", emoji="🔗", style=discord.ButtonStyle.primary)
            link_button.callback = lambda i=interaction: link_button_callback(self, i, thread, link)
            submit_vod_view.add_item(link_button)

            if thread != None and link != None:
                submit_button = Button(custom_id="vod_submit", label="Submit VoD", emoji="✅", style=discord.ButtonStyle.success)
                submit_button.callback = lambda i=interaction: submit_vod(self, i, thread, link)
                submit_vod_view.add_item(submit_button)

            embed = await self.vod_embed(thread, link)            

            if interaction.message is not None:
                try:
                    await interaction.response.edit_message(content=f"Select a war and enter a link!", view=submit_vod_view, embed=embed)
                except discord.errors.InteractionResponded:
                    await interaction.followup.send(content=f"Select a war and enter a link!", view=submit_vod_view, embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(content=f"Select a war and enter a link!", view=submit_vod_view, embed=embed, ephemeral=True)

            async def link_button_callback(self, interaction: Interaction, thread, link):
                input_modal = LinkModal(thread, link)
                await interaction.response.send_modal(input_modal)
                await input_modal.wait()
                await show_submission_menu(self, input_modal.interaction, input_modal.thread, input_modal.vod_link)
            
            async def submit_vod(self, interaction: Interaction, thread, link):
      
                user = ctx.author.display_name
                message = f"{user} has submitted a VOD: {link}"
                await thread.send(message)
      
                # Update the worksheet
                worksheet = open_vodsheet(thread.name)
                worksheet.insert_rows(row=1, number=1, values=[user, link])

                if interaction.message is not None:
                    try:
                        await interaction.response.edit_message(content=f"VOD submitted to '{thread.name}'",  view=None, embed=None)
                    except discord.errors.InteractionResponded:
                        await interaction.followup.send(content=f"VOD submitted to '{thread.name}'",  view=None, ephemeral=True)
                else:
                    await interaction.response.send_message(content=f"VOD submitted to '{thread.name}'",  view=None, ephemeral=True)

      

        async def show_thread_menu(self, interaction: Interaction, territory=None, type=None, result=None, date=None):
            create_thread_view = View(timeout=None)

            # Populate date_list with dates
            today = datetime.date.today()
            date_list = [today - datetime.timedelta(days=i) for i in range(4)]
            date_list = [d.strftime("%m/%d") for d in date_list]

            territory_options = [SelectOption(label=option, value=option) for option in lists.territorylist]
            territory_select = Select(placeholder="Territory", options=territory_options, custom_id="territory_select")
            territory_select.callback = lambda i: show_thread_menu(self, i, territory_select.values[0], type, result, date)
            create_thread_view.add_item(territory_select)

            type_options = [SelectOption(label=option, value=option) for option in ["Attack","Defense"]]
            type_select = Select(placeholder="Attack/Defense", options=type_options, custom_id="type_select")
            type_select.callback = lambda i: show_thread_menu(self, i, territory, type_select.values[0], result, date)
            create_thread_view.add_item(type_select)

            result_options = [SelectOption(label=option, value=option) for option in ["Win","Loss"]]
            result_select = Select(placeholder="Win/Loss", options=result_options, custom_id="result_select")
            result_select.callback = lambda i: show_thread_menu(self, i, territory, type, result_select.values[0], date)
            create_thread_view.add_item(result_select)

            date_options = [SelectOption(label=option, value=option) for option in date_list]
            date_select = Select(placeholder="Date", options=date_options, custom_id="date_select")
            date_select.callback = lambda i: show_thread_menu(self, i, territory, type, result, date_select.values[0])
            create_thread_view.add_item(date_select)

            if territory != None and result != None and type != None and date != None:
                create_thread_button = Button(custom_id="thread_create", label="Create Thread", emoji="✅", style=discord.ButtonStyle.success)
                create_thread_button.callback = lambda i=interaction: create_thread(self, i, territory, type, result, date)
                create_thread_view.add_item(create_thread_button)

            embed = await self.thread_embed(territory, type, result, date)

            await interaction.response.edit_message(content="Fill out the options to create a new thread!", view=create_thread_view, embed=embed)
          
            async def create_thread(self, interaction: Interaction, territory, type, result, date):
                # create the thread
                thread_name = f"{territory} - {type} - {result} - {date}"
                channel = ctx.guild.get_channel(config['vod_channel_id'])
                tags = channel.available_tags
                if channel is None:
                    await interaction.response.edit_message(content='Submission channel not found, please set a channel using /vod channel')
                else:
                    try:
                        default_message = f"VoD submissions for {thread_name}"
                        await channel.create_thread(name=thread_name, applied_tags= [get_forumtag_id(f"{territory}", tags), get_forumtag_id(f"{type}", tags), get_forumtag_id(f"{result}", tags)], content=default_message)
      
                        # create the worksheet
                        create_vodsheet(thread_name)
      
                        # add thread to thread_choices
                        json.add_thread_choice(thread_name)
                        await interaction.response.edit_message(content=f"Thread '{thread_name}' and worksheet created!", view=None, embed=None)
                    except HttpError as error:
                        if error.resp.status == 400:
                            await interaction.response.edit_message(content=f"A thread or worksheet with the name '{thread_name}' already exists.", view=None, embed=None)
                        else:
                            raise error
                await show_vod_menu(self, interaction)

        async def show_channel_menu(self, interaction: Interaction):
            select_channel_view = View(timeout=None)

            # get list of available channels on server
            server = self.bot.get_guild(ctx.guild.id)
            channels = {str(channel): channel.id for channel in server.forum_channels}
            print(channels)

            # if channels has options, display a selection view
            if channels:
                # create the selectmenu
                options = [SelectOption(label=option, value=option) for option in channels.keys()]
                select = Select(placeholder="Select a channel", options=options, custom_id="channel_select")
                select.callback = lambda i: update_channel(self, i, channels[select.values[0]])
                select_channel_view.add_item(select)

                # add a cancel button
                cancel_button = Button(label="Cancel", style=discord.ButtonStyle.secondary, custom_id="cancel")
                cancel_button.callback = lambda i: show_vod_menu(self, i)
                select_channel_view.add_item(cancel_button)
                await interaction.response.edit_message(content="Please select a channel for VoD submissions.", embed=None, view=select_channel_view)

                async def update_channel(self, interaction: Interaction, channel_id):
                    # update config file with new channel ID
                    config['vod_channel_id'] = channel_id
                    json.save_json_file(config_file, config)
                    await interaction.response.edit_message(content=f"Thread channel set to <#{channel_id}>", view=None)
                    await show_vod_menu(self, interaction)
            else:
                await interaction.response.edit_message(content="No forum channels found.", embed=None, view=None)
                await show_vod_menu(self, interaction)
          
         
        await show_vod_menu(self, ctx)

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
    bot.add_cog(Vods(bot))