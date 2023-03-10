# define the Build class as a cog       
import os
import discord
import asyncio
import datetime
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

# load events file
events_file = os.path.join(parent_dir, 'events.json')
events = json.load_json_file(events_file)

event_types = {"Invasion": "👹","War": "⚔️","OPR": "🚩","Payouts": "💰","Custom": "🎉"}


class InputModal(Modal):
    def __init__(self, title, field) -> None:
        super().__init__(title=title)
        if field == "war_opponent":
            self.add_item(InputText(label="Opponent Name:", style=discord.InputTextStyle.short))
        elif field == "custom_emoji":
            self.add_item(InputText(label="Emoji:", style=discord.InputTextStyle.short))
        elif field == "event_description":
            self.add_item(InputText(label="Description:", style=discord.InputTextStyle.short))
        elif field == "war_signup":
            self.add_item(InputText(label="Signup Link:", style=discord.InputTextStyle.short))
        self.title = title

    async def callback(self, interaction: Interaction):
       self.new_value = self.children[0].value
       self.interaction = interaction
       await interaction.response.edit_message(content=f"{self.title} {self.new_value}", view=None, embed=None)
       self.stop()

class Events(commands.Cog):
  
    def __init__(self, bot):
      self.bot = bot 

    # define a new command for creating events
    @commands.slash_command(name="events", description="manage events")
    async def manage(self, ctx: ApplicationContext):

        async def show_event_menu(interaction: Interaction):
            role = discord.utils.find(lambda r: r.name == 'event manager', ctx.guild.roles)
            if role in ctx.author.roles:

                # create a new view for selecting a build
                event_menu_view = View(timeout=None)

                # Get the events
                events = json.get_events()
                events = sorted(events, key=lambda e: datetime.datetime.strptime(e['event_date'] + ' ' + e['event_time'], '%m/%d %I:%M %p'))

                # Create the event text string
                event_text = ""
                for event in events:
                    event_text += f"{event['event_text']}\n"

                # Create the embed
                embed = Embed(title="UPCOMING COMPANY EVENTS")
                embed.description = "======================================================================="
                embed.add_field(name="", value=event_text)

                # add a button for creating a new event
                add_button = Button(custom_id="events_add", label="New Event", emoji="➕", style=discord.ButtonStyle.success)
                add_button.callback = show_event_selection
                event_menu_view.add_item(add_button)

                # add a button for viewing and modifying event settings
                settings_button = Button(custom_id="events_settings", label="Settings", emoji="⚙️", style=discord.ButtonStyle.secondary)
                settings_button.callback = show_settings
                event_menu_view.add_item(settings_button)

                # if the user is coming back after a button press, edit the message, otherwise send a new message
                if interaction.message is not None:
                    try:
                        await interaction.response.edit_message(content="Please choose an option!", view=event_menu_view, embed=embed)
                    except discord.errors.InteractionResponded:
                        await interaction.followup.send(content="Please choose an option!", view=event_menu_view, embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message(content="Please choose an option!", view=event_menu_view, embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(content="You don't have permission to use this command", ephemeral=True)

        async def show_event_selection(interaction: Interaction):
            # create a new view for selecting a build
            event_selection_view = View(timeout=None)

            # add a button for each of the event types
            for event in event_types.keys():
                button = Button(custom_id=f"type_{event}", label=f"{event}", emoji=event_types.get(f"{event}"))
                event_dict = {"event_type": f"{event}",
                              "event_date": "",
                              "event_time": "",
                              "event_territory": "",
                              "war_type": "",
                              "war_opponent": "",
                              "war_signup": "",
                              "custom_emoji": "",
                              "event_description": ""}
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

        async def show_event_details(interaction: Interaction, event: dict, field=None, value=None):
            # update event dictionary if we have data
            if field != None:
                event[field] = value

            # create a new view for selecting a build
            event_details_view = None
            event_details_view = View(timeout=None)

            # Populate date_list with dates
            today = datetime.date.today()
            date_list = [today + datetime.timedelta(days=i) for i in range(7)]
            date_list = [d.strftime("%m/%d") for d in date_list]

            date_options = [SelectOption(label=option, value=option) for option in date_list]
            date_select = Select(placeholder="Date", options=date_options, custom_id="date_select")
            date_select.callback = lambda i, field="event_date": show_event_details(i, event, field, date_select.values[0])
            event_details_view.add_item(date_select)

            # add a button for each of the event types
            start_time = datetime.datetime.strptime('12:00 PM', '%I:%M %p')
            end_time = datetime.datetime.strptime('11:30 PM', '%I:%M %p')
            delta = datetime.timedelta(minutes=30)

            times_list = []

            while start_time <= end_time:
                times_list.append(start_time.strftime('%I:%M %p'))
                start_time += delta

            time_options = [SelectOption(label=option, value=option) for option in times_list]
            time_select = Select(placeholder="Time", options=time_options, custom_id="time_select")
            time_select.callback = lambda i, field="event_time": show_event_details(i, event, field, time_select.values[0])
            event_details_view.add_item(time_select)

            if event['event_type'] == "Invasion":
                territory_options = [SelectOption(label=option, value=option) for option in lists.territorylist]
                territory_select = Select(placeholder="Territory", options=territory_options, custom_id="territory_select")
                territory_select.callback = lambda i, field="event_territory": show_event_details(i, event, field, territory_select.values[0])
                event_details_view.add_item(territory_select)
            elif event['event_type'] == "War":
                territory_options = [SelectOption(label=option, value=option) for option in lists.territorylist]
                territory_select = Select(placeholder="Territory", options=territory_options, custom_id="territory_select")
                territory_select.callback = lambda i, field="event_territory": show_event_details(i, event, field, territory_select.values[0])
                event_details_view.add_item(territory_select)

                type_options = [SelectOption(label=option, value=option) for option in ["Attack","Defense"]]
                type_select = Select(placeholder="Attack/Defense", options=type_options, custom_id="type_select")
                type_select.callback = lambda i, field="war_type": show_event_details(i, event, field, type_select.values[0])
                event_details_view.add_item(type_select)
                
                opponent_button = Button(custom_id=f"war_opponent", label="Opponent", emoji="⚔️")
                opponent_button.callback = lambda i=interaction, title="Opponent:", field="war_opponent": input_button_callback(i, title, event, field)
                event_details_view.add_item(opponent_button)

                signup_button = Button(custom_id=f"war_signup", label="War Signup Link", emoji="🔗")
                signup_button.callback = lambda i=interaction, title="War Signup Link:", field="war_signup": input_button_callback(i, title, event, field)
                event_details_view.add_item(signup_button)

            elif event['event_type'] == "Custom":
                emoji_button = Button(custom_id=f"custom_emoji", label="Emoji", emoji="🙂")
                emoji_button.callback = lambda i=interaction, title="Event Emoji:", field="custom_emoji": input_button_callback(i, title, event, field)
                event_details_view.add_item(emoji_button)
                
                description_button = Button(custom_id=f"event_description", label="Description", emoji="📝")
                description_button.callback = lambda i=interaction, title="Event Description:", field="event_description": input_button_callback(i, title, event, field)
                event_details_view.add_item(description_button)


            embed = await event_embed(event)

            # add a button to create the event
            create_button = Button(custom_id="event_create", label="Create", style=discord.ButtonStyle.success)
            create_button.callback = lambda i=interaction: create_event(i, event)
            event_details_view.add_item(create_button)

            # add a back button to return to the event menu
            back_button = Button(custom_id="event_back", label="Back", style=discord.ButtonStyle.danger)
            back_button.callback = show_event_menu
            event_details_view.add_item(back_button)

            # if the user is coming back after a button press, edit the message, otherwise send a new message
            if interaction.message is not None:
                try:
                    await interaction.response.edit_message(content="Please select the events details!", view=event_details_view, embed=embed)
                except discord.errors.InteractionResponded:
                    await interaction.followup.send(content="Please select the events details!", view=event_details_view, embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(content="Please select the events details!", view=event_details_view, embed=embed, ephemeral=True)

            async def input_button_callback(interaction: Interaction, title, event, field):
                input_modal = InputModal(title, field)
                await interaction.response.send_modal(input_modal)
                await input_modal.wait()
                await show_event_details(input_modal.interaction, event, field, input_modal.new_value)

        async def create_event(interaction: Interaction, event):
            # Define the new event
            event_type = event['event_type']
            if event_type == 'Invasion':
                event_string = f"{event_types.get('Invasion')}︱{event['event_date']}︱{event['event_time']} EST︱**Invasion** - {event['event_territory']}"
            elif event_type == 'War':
                event_string = f"{event_types.get('War')}︱{event['event_date']}︱{event['event_time']} EST︱**War** - {event['event_territory']} {event['war_type']} **VS.** {event['war_opponent']} [Sign Up!]({event['war_signup']})"
            elif event_type == 'Payouts':
                event_string = f"{event_types.get('Payouts')}︱{event['event_date']}︱{event['event_time']} EST︱**Payouts!**"             
            elif event_type == 'OPR':
                event_string = f"{event_types.get('OPR')}︱{event['event_date']}︱{event['event_time']} EST︱**OPR Night!**"
            else:
                event_string = f"{event['custom_emoji']}︱{event['event_date']}︱{event['event_time']} EST︱**{event['event_description']}**"
            
            new_event = {'event_date': event['event_date'],'event_time': event['event_time'], 'event_text': event_string}

            json.add_event(new_event)

            await interaction.response.edit_message(content="Event Added", embed=None, view=None)

            await show_event_menu(interaction)
        
        async def show_settings(interaction: Interaction):
            # create a new view for selecting settings
            settings_view = View(timeout=None)

            # add a button for editing the auto-update time
            sch_button = Button(custom_id="events_sch", label="Set Schedule", emoji="🕒", style=discord.ButtonStyle.secondary)
            sch_button.callback = show_event_sch
            settings_view.add_item(sch_button)

            # add a back button to return to the event menu
            back_button = Button(custom_id="events_back", label="Back", style=discord.ButtonStyle.danger)
            back_button.callback = show_event_menu
            settings_view.add_item(back_button)

            get_settings = {key: config[key] for key in config.keys() & {'events_timezone', 'events_update_time'}}
            embed = await settings_embed("Current Settings:", "", get_settings)

            # if the user is coming back after a button pr ess, edit the message, otherwise send a new message
            if interaction.message is not None:
                try:
                    await interaction.response.edit_message(content="Please choose the settings you want to update!", view=settings_view, embed=embed)
                except discord.errors.InteractionResponded:
                    await interaction.followup.send(content="Please choose the settings you want to update!", view=settings_view, ephemeral=True, embed=embed)
            else:
                await interaction.response.send_message(content="Please choose the settings you want to update!", view=settings_view, ephemeral=True, embed=embed)

        async def show_event_sch(interaction: Interaction):
            # create a new view for selecting settings
            sch_view = View(timeout=None)

            # add a select for setting the auto-update schedule
            schedule_options = [SelectOption(label=f"{hour:02d}:00:00", value=f"{hour:02d}:00:00") for hour in range(0, 24)]
            schedule_dropdown = Select(custom_id="events_settings_schedule", placeholder="Select auto-update times", options=schedule_options, max_values=len(schedule_options))
            schedule_dropdown.callback = lambda i: apply_settings(i, "events_update_time", schedule_dropdown.values[0])
            sch_view.add_item(schedule_dropdown)

            get_setting = {key: config[key] for key in config.keys() & {'events_update_time'}}
            embed = await settings_embed("Current Setting:", "", get_setting)

            await interaction.response.edit_message(content="Schedule:", view=sch_view, embed=embed)

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
        
        async def event_embed(event: dict) -> Embed:
            # create a new embed with the build information
            embed = Embed(title=f"Creating New {event['event_type']} Event!", color=0xffc800)
            if event['event_type'] == 'Invasion':
                embed.add_field(name="Event Preview", value=f"{event_types.get('Invasion')}︱{event['event_date']}︱{event['event_time']} EST︱**Invasion** - {event['event_territory']}")
            elif event['event_type'] == 'War':
                embed.add_field(name="Event Preview", value=f"{event_types.get('War')}︱{event['event_date']}︱{event['event_time']} EST︱**War** - {event['event_territory']} {event['war_type']} **VS.** {event['war_opponent']} [Sign Up!]({event['war_signup']})")
            elif event['event_type'] == 'Payouts':
                embed.add_field(name="Event Preview", value=f"{event_types.get('Payouts')}︱{event['event_date']}︱{event['event_time']} EST︱**Payouts!**")                
            elif event['event_type'] == 'OPR':
                embed.add_field(name="Event Preview", value=f"{event_types.get('OPR')}︱{event['event_date']}︱{event['event_time']} EST︱**OPR Night!**")
            else:
                embed.add_field(name="Event Preview", value=f"{event['custom_emoji']}︱{event['event_date']}︱{event['event_time']} EST︱**{event['event_description']}**")
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