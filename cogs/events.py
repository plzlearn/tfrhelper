# define the Build class as a cog       
import os
import discord
import asyncio
from discord import ApplicationContext, Interaction, Embed, SelectOption
from discord.commands import SlashCommandGroup
from discord.ext import commands
from discord.ui import Button, View, Modal, InputText, Select
import utils.jsonhandler as json
import sys
sys.path.append("../utils")
from utils import lists

# get the absolute path to the parent directory
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# load config file
config_file = os.path.join(parent_dir, 'config.json')
config = json.load_json_file(config_file)

event_types = {"Invasion": "👹","War": "⚔️","OPR": "🚩","Payouts": "💰","Other": "🎉"}

class Events(commands.Cog):
  
    def __init__(self, bot):
      self.bot = bot 

    # define a new command for creating events
    @commands.slash_command(name="events", description="manage events")
    async def manage(self, ctx: ApplicationContext):

        async def show_event_menu(interaction: Interaction):
            # create a new view for selecting a build
            event_menu_view = View(timeout=None)

            # add a button for creating a new event
            add_button = Button(custom_id="events_add", label="New Event", emoji="➕", style=discord.ButtonStyle.success)
            add_button.callback = show_event_selection
            event_menu_view.add_item(add_button)

            # add a button for viewing current event embed
            view_button = Button(custom_id="events_view", label="View Events", emoji="🔍", style=discord.ButtonStyle.primary)
            view_button.callback = show_events
            event_menu_view.add_item(view_button)

            # add a button for viewing and modifying event settings
            settings_button = Button(custom_id="events_settings", label="Settings", emoji="⚙️", style=discord.ButtonStyle.secondary)
            settings_button.callback = show_settings
            event_menu_view.add_item(settings_button)

            # if the user is coming back after a button press, edit the message, otherwise send a new message
            if interaction.message is not None:
                try:
                    await interaction.response.edit_message(content="Please choose an option!", view=event_menu_view, embed=None)
                except discord.errors.InteractionResponded:
                    await interaction.followup.send(content="Please choose an option!", view=event_menu_view, ephemeral=True)
            else:
                await interaction.response.send_message(content="Please choose an option!", view=event_menu_view, ephemeral=True)

        async def show_event_selection(interaction: Interaction):
            # create a new view for selecting a build
            event_selection_view = View(timeout=None)

            # add a button for each of the event types
            for event in event_types.keys():
                button = Button(custom_id=f"type_{event}", label=f"{event}", emoji=event_types.get(f"{event}"))
                event_dict = {"event_type": f"{event}"}
                button.callback = lambda i, event=event_dict: show_event_details(i, event)
                event_selection_view.add_item(button)

            # add a back button to return to the event menu
            back_button = Button(custom_id="events_back", label="Back", style=discord.ButtonStyle.danger)
            back_button.callback = show_event_menu
            event_selection_view.add_item(back_button)

            # if the user is coming back after a button press, edit the message, otherwise send a new message
            if interaction.message is not None:
                try:
                    await interaction.response.edit_message(content="Please choose the type of event you want to add!", view=event_selection_view, embed=None)
                except discord.errors.InteractionResponded:
                    await interaction.followup.send(content="Please choose the type of event you want to add!", view=event_selection_view, ephemeral=True)
            else:
                await interaction.response.send_message(content="Please choose the type of event you want to add!", view=event_selection_view, ephemeral=True)

        async def show_event_details(interaction: Interaction, event: dict):
            # create a new view for selecting a build
            event_details_view = View(timeout=None)

            # add a button for each of the event types
            date_button = Button(custom_id=f"event_date", label="Date", emoji="📅")
            date_button.callback = lambda i, field="event_date", event=event: edit_event(i, field, event)
            event_details_view.add_item(date_button)

            # add a button for each of the event types
            time_button = Button(custom_id=f"event_time", label="Time", emoji="🕒")
            time_button.callback = lambda i, field="event_time", event=event: edit_event(i, field, event)
            event_details_view.add_item(time_button)

            if event['event_type'] == "Invasion":
                territory_button = Button(custom_id=f"{event}_territory", label="Territory", emoji="🗺️")
                territory_button.callback = lambda i, field="event_territory", event=event: edit_event(i, field, event)
                event_details_view.add_item(territory_button)
            elif event['event_type'] == "War":
                territory_button = Button(custom_id=f"{event}_territory", label="Territory", emoji="🗺️")
                territory_button.callback = lambda i, field="event_territory", event=event: edit_event(i, field, event)
                event_details_view.add_item(territory_button)
                type_button = Button(custom_id=f"{event}_type", label="Attack/Defense", emoji="❔")
                type_button.callback = lambda i, field="event_wartype", event=event: edit_event(i, field, event)
                event_details_view.add_item(type_button)                 
                opponent_button = Button(custom_id=f"{event}_opponent", label="Opponent", emoji="⚔️")
                opponent_button.callback = lambda i, field="event_opponent", event=event: edit_event(i, field, event)
                event_details_view.add_item(opponent_button)

            embed = await event_embed("Editing Event", "", event)

            # add a button to create the event
            create_button = Button(custom_id="event_create", label="Create", style=discord.ButtonStyle.success)
            create_button.callback = create_event
            event_details_view.add_item(create_button)

            # add a back button to return to the event menu
            back_button = Button(custom_id="event_back", label="Back", style=discord.ButtonStyle.danger)
            back_button.callback = show_event_menu
            event_details_view.add_item(back_button)

            # if the user is coming back after a button press, edit the message, otherwise send a new message
            if interaction.message is not None:
                try:
                    await interaction.response.edit_message(content="Please choose the type of event you want to add!", view=event_details_view, embed=embed)
                except discord.errors.InteractionResponded:
                    await interaction.followup.send(content="Please choose the type of event you want to add!", view=event_details_view, ephemeral=True)
            else:
                await interaction.response.send_message(content="Please choose the type of event you want to add!", view=event_details_view, ephemeral=True)

        async def edit_event(interaction: Interaction, event: dict):
            return

        async def create_event(interaction: Interaction):
            return
        
        async def show_events(interaction: Interaction):
            return 
        
        async def show_settings(interaction: Interaction):
            # create a new view for selecting settings
            settings_view = View(timeout=None)

            # add a button for editing the timezone
            tz_button = Button(custom_id="events_tz", label="Set Timezone", emoji="🌍", style=discord.ButtonStyle.secondary)
            tz_button.callback = show_event_tz
            settings_view.add_item(tz_button)

            # add a button for editing the auto-update time
            sch_button = Button(custom_id="events_sch", label="Set Schedule", emoji="🕒", style=discord.ButtonStyle.secondary)
            sch_button.callback = show_event_sch
            settings_view.add_item(sch_button)

            # add a back button to return to the event menu
            back_button = Button(custom_id="events_back", label="Back", style=discord.ButtonStyle.danger)
            back_button.callback = show_event_menu
            settings_view.add_item(back_button)

            get_settings = {key: config[key] for key in config.keys() & {'events_timezone', 'events_schedule'}}
            embed = await settings_embed("Current Settings:", "", get_settings)

            # if the user is coming back after a button pr ess, edit the message, otherwise send a new message
            if interaction.message is not None:
                try:
                    await interaction.response.edit_message(content="Please choose the settings you want to update!", view=settings_view, embed=embed)
                except discord.errors.InteractionResponded:
                    await interaction.followup.send(content="Please choose the settings you want to update!", view=settings_view, ephemeral=True, embed=embed)
            else:
                await interaction.response.send_message(content="Please choose the settings you want to update!", view=settings_view, ephemeral=True, embed=embed)

        async def show_event_tz(interaction: Interaction):
            # create a new view for selecting settings
            tz_view = View(timeout=None)

            timezone_options = [
                SelectOption(label="Eastern Time (US & Canada)", value="America/New_York"),
                SelectOption(label="Central Time (US & Canada)", value="America/Chicago"),
                SelectOption(label="Mountain Time (US & Canada)", value="America/Denver"),
                SelectOption(label="Pacific Time (US & Canada)", value="America/Los_Angeles")
            ]
            timezone_dropdown = Select(custom_id="events_settings_timezone", placeholder="Select timezone", options=timezone_options)
            timezone_dropdown.callback = lambda i: apply_settings(i, "events_timezone", timezone_dropdown.values[0])
            tz_view.add_item(timezone_dropdown)

            get_setting = {key: config[key] for key in config.keys() & {'events_timezone'}}
            embed = await settings_embed("Current Setting:", "", get_setting)

            await interaction.response.edit_message(content="Select a timezone:", view=tz_view, embed=embed)

        async def show_event_sch(interaction: Interaction):
            # create a new view for selecting settings
            sch_view = View(timeout=None)

            # add a select for setting the auto-update schedule
            schedule_options = [SelectOption(label=f"{hour}:00", value=str(hour)) for hour in range(0, 23)]
            schedule_dropdown = Select(custom_id="events_settings_schedule", placeholder="Select auto-update times", options=schedule_options, max_values=len(schedule_options))
            schedule_dropdown.callback = lambda i: apply_settings(i, "events_schedule", schedule_dropdown.values[0])
            sch_view.add_item(schedule_dropdown)

            get_setting = {key: config[key] for key in config.keys() & {'events_schedule'}}
            embed = await settings_embed("Current Setting:", "", get_setting)

            await interaction.response.edit_message(content="Test", view=sch_view, embed=embed)

        async def apply_settings(interaction: Interaction, setting, value):
            # update config file with new channel ID
            config[setting] = value
            json.save_json_file(config_file, config)
            asyncio.timeout(3)
            await show_settings(interaction)

        async def settings_embed(title: str, desc: str, options: dict) -> Embed:
          # create a new embed with the build information
          embed = Embed(title=title, color=0xffc800)
          embed.description = desc
          names = options.keys()
          for setting in names:
            embed.add_field(name=setting, value=options[f"{setting}"])
          return embed
        
        async def event_embed(title: str, desc: str, options: dict) -> Embed:
          # create a new embed with the build information
          embed = Embed(title=title, color=0xffc800)
          embed.description = desc
          names = options.keys()
          for setting in names:
            embed.add_field(name=setting, value=options[f"{setting}"])
          return embed

        # initial event creation view
        await show_event_menu(ctx)

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
    bot.add_cog(Events(bot))