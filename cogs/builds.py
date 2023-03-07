import os
import discord
import asyncio
from discord import ApplicationContext, Interaction, Embed, SelectOption
from discord.ext import commands
from discord.ui import Button, View, Modal, InputText, Select
import sys
sys.path.append("../utils")
from utils import lists
import utils.dbhandler as db
import utils.sheets as gs
import utils.imgur as img

# create a dictionary of field options
field_options = {"role": lists.rolelist,"weapon1": lists.weaponlist,"weapon2": lists.weaponlist,"ability": lists.abilitylist,"weight": lists.weightlist}
# create a dictionary of friendly field names
friendly_names = {"buildname": "Build Name","role": "Role","weapon1": "Weapon 1","weapon2": "Weapon 2","ability": "Heartrune Ability","weight": "Weight Class","gearscore": "Gear Score","notes": "Notes"}
# create a dictionary of role emoji mappings
role_emojis = {"Bruiser": "⚔️","Dex": "🏹","Group Healer": "⚕️","Zerg Healer": "⚕️","Support": "🔮","Assassin": "🥷"}

class FieldModal(Modal):
    def __init__(self, field: str, build_number: int, selected_build: dict) -> None:
        super().__init__(title="Update Build")
        self.field = field
        self.build_number = build_number
        self.selected_build = selected_build
        self.add_item(InputText(label=friendly_names.get(f"{field}"), style=discord.InputTextStyle.short))

    # define the build_info_embed function as a top-level function within the Build class
    async def build_info_embed(self, build: dict) -> Embed:
      embed = Embed(title=f"{build['buildname']} ({build['role']})", color=0xffc800)
      embed.set_thumbnail(url="https://img.icons8.com/windows/128/FFFFFF/new-world.png")
      embed.add_field(name="Weapon 1", value=build['weapon1'])
      embed.add_field(name="Weapon 2", value=build['weapon2'])
      embed.add_field(name="Heartrune Ability", value=build['ability'])
      embed.add_field(name="Weight Class", value=build['weight'])
      embed.add_field(name="Gear Score", value=build['gearscore'])
      embed.add_field(name="Notes", value=build['notes'] or "None")
      embed.add_field(name="Gear", value=build['gear'] or "None")
      if build['gear'] != None:
          embed.set_image(url=build['gear'])
      return embed

    async def callback(self, interaction: discord.Interaction):
        new_value = self.children[0].value

        # validate the new value based on the field data type
        if self.field == "gearscore":
            try:
                new_value = int(new_value)
                if new_value < 300 or new_value > 625:
                    raise ValueError
            except ValueError:
                await interaction.response.edit_message(content="Invalid value. Please enter an integer between 300 and 625.")
                return
        else:
            valid_options = field_options.get(self.field)
            if valid_options and new_value not in valid_options:
                options_str = "\n".join(valid_options)
                await interaction.response.edit_message(content=f"Invalid value. Please enter one of the following options:\n{options_str}")
                return
       
        # update the selected build with the new field value
        self.selected_build[self.field] = new_value

        # update the build in the database
        await db.db_edit_build(interaction.user.id, self.selected_build['id'], self.field, new_value)
        await interaction.response.edit_message(content=f"Updating build: **{self.selected_build['buildname']}** <a:2923printsdark:1079993998116134932>")
        gs.gs_edit_build(interaction.user.id, self.selected_build['id'], self.field, new_value)

        embed = await self.build_info_embed(self.selected_build)
      
        await interaction.edit_original_response(content=f"Updated **"+friendly_names.get(f"{self.field}")+f"** to **{new_value}** for build: **{self.selected_build['buildname']}**.", embed=embed)

# define the Build class as a cog
class Build(commands.Cog):
  
    def __init__(self, bot):
      self.bot = bot 

    # define the build_info_embed function as a top-level function within the Build class
    async def build_info_embed(self, build: dict) -> Embed:
      # create a new embed with the build information
      embed = Embed(title=f"{build['buildname']} ({build['role']})", color=0xffc800)
      embed.set_thumbnail(url="https://img.icons8.com/windows/128/FFFFFF/new-world.png")
      embed.add_field(name="Weapon 1", value=build['weapon1'])
      embed.add_field(name="Weapon 2", value=build['weapon2'])
      embed.add_field(name="Heartrune Ability", value=build['ability'])
      embed.add_field(name="Weight Class", value=build['weight'])
      embed.add_field(name="Gear Score", value=build['gearscore'])
      embed.add_field(name="Notes", value=build['notes'] or "None")
      embed.add_field(name="Gear", value=build['gear'] or "None")
      if build['gear'] != None:
          embed.set_image(url=build['gear'])
      return embed 

    # define a new subcommand for managing builds
    @commands.slash_command(name="builds", description="manage your builds")
    async def manage(self, ctx: ApplicationContext):

        # define a function to display the build selection menu
        async def show_build_selection(interaction: Interaction):
            user_id = interaction.user.id

            # get the user's build from the database
            user_builds = await db.db_get_user_builds(user_id)

            # create a new view for selecting a build
            build_selection_view = View(timeout=None)

            # add a button for each of the user's builds
            for build in user_builds:
                button = Button(custom_id=f"build_{build['id']}", label=build['buildname'], emoji=role_emojis.get(f"{build['role']}"))
                button.callback = lambda i, build=build: show_build_menu(i, build)
                build_selection_view.add_item(button)

            # add a button for creating a new build
            add_button = Button(custom_id="build_add", label="New Build", emoji="➕", style=discord.ButtonStyle.success)
            add_button.callback = lambda i: show_build_menu(i, {"id": 0, "user_id": user_id, "buildname": "New Build", "role": "", "weapon1": "", "weapon2": "", "ability": "", "weight": "", "gearscore": "", "notes": "", "gear": ""})
            build_selection_view.add_item(add_button)

            # if the user is coming back after a button press, edit the message, otherwise send a new message
            if interaction.message is not None:
                try:
                    await interaction.response.edit_message(content="Please choose a build to manage!", view=build_selection_view, embed=None)
                except discord.errors.InteractionResponded:
                    await interaction.followup.send(content="Please choose a build to manage!", view=build_selection_view, ephemeral=True)
            else:
                await interaction.response.send_message(content="Please choose a build to manage!", view=build_selection_view, ephemeral=True)

        # define a function to display the build menu
        async def show_build_menu(interaction: Interaction, build):
            
            # define a function to update a build field
            async def update_build_field(interaction: Interaction, field):
                field_name = friendly_names[field]
                field_options_list = field_options.get(field, [])

                # if the field has options, display a selection view
                if field_options_list:
                    # create the selectmenu
                    options = [SelectOption(label=option, value=option) for option in field_options_list]
                    select = Select(placeholder=f"Select a new value for {field_name}", options=options, custom_id=f"{field}_select")
                    select.callback = lambda i: update_build_field_selection(i, field, select.values[0], build)
                    selection_view = View(timeout=None)
                    selection_view.add_item(select)

                    # add a cancel button
                    cancel_button = Button(label="Cancel", style=discord.ButtonStyle.secondary, custom_id="cancel")
                    cancel_button.callback = lambda i: show_build_menu(i, build)
                    selection_view.add_item(cancel_button)
                    await interaction.response.edit_message(content=f"Please select a new value for {field_name}:", embed=None, view=selection_view)
                
                # otherwise, display an input modal for the field
                else:
                    input_modal = FieldModal(field, build['id'], build)
                    await interaction.response.send_modal(input_modal)
                
                
                async def update_build_field_selection(interaction: Interaction, field: str, option: str, build: dict):
                    build_id = build['id']
                    user_id = interaction.user.id
                    build[field] = option
                    await db.db_edit_build(user_id, build_id, field, option)
                    await interaction.response.edit_message(content=f"Updating build: **{build['buildname']}** <a:2923printsdark:1079993998116134932>", view=None)
                    gs.gs_edit_build(user_id, build_id, field, option)
                    user_builds = await db.db_get_user_builds(user_id)
                    for i, b in enumerate(user_builds):
                        if b['id'] == build_id:
                            user_builds[i] = build
                            break
                    embed = await self.build_info_embed(build)
                    await interaction.edit_original_response(content=f"Updated {friendly_names[field]} to {option} for build: {build['buildname']}.", view=menu_view, embed=embed)

            async def upload_gear_image(interaction: Interaction, build: dict):
                await interaction.response.edit_message(content="Please attach an image of your gear by using 'Upload a File' in the '+' menu, or by pasting a link and hitting enter.", view=None, embed=None)
                build_id = build['id']
                user_id = interaction.user.id
                # wait for the user to send the image\
                check = lambda m: m.author.id == interaction.user.id and m.channel.id == interaction.channel.id and m.attachments
                try:
                    message = await self.bot.wait_for(event="message", check=check)
                    # get the image from the message attachment
                    image_url = img.upload_image_to_imgur(await message.attachments[0].read())
                    build['gear'] = image_url
                    # update the build in the database and spreadsheet with the image URL
                    await db.db_edit_build(user_id, build_id, "gear", image_url)
                    await interaction.edit_original_response(content="Uploading gear image <a:2923printsdark:1079993998116134932>")
                    gs.gs_edit_build(user_id, build_id, "gearpic", image_url)
                    # display a message to confirm the image upload
                    await interaction.edit_original_response(content="Gear image uploaded successfully!")
                    # delete the user's message
                    await message.delete()
                except asyncio.TimeoutError:
                    await interaction.edit_original_response(content="No image uploaded. Please try again.")
                # show the build menu again
                await show_build_menu(interaction, build)
            
            # define a function to display a confirmation view for removing a build
            async def remove_build_confirmation(interaction: Interaction):
                embed = await self.build_info_embed(build)
                confirm_view = View(timeout=None)
                confirm_button = Button(label="Confirm", style=discord.ButtonStyle.red, custom_id="confirm_remove")
                confirm_button.callback = lambda i: remove_build(i, build)
                cancel_button = Button(label="Cancel", style=discord.ButtonStyle.secondary, custom_id="cancel_remove")
                cancel_button.callback = lambda i: show_build_menu(i, build)
                confirm_view.add_item(confirm_button)
                confirm_view.add_item(cancel_button)
                await interaction.response.edit_message(content=f"Are you sure you want to remove this build?\nBuild: {build['buildname']}", embed=embed, view=confirm_view)

            async def remove_build(interaction: Interaction, build: dict):
                user_id = interaction.user.id
                build_id = build['id']
                await db.db_remove_build(user_id, build_id)
                await gs.gs_remove_build(user_id, build_id)
                await interaction.response.edit_message(content=f"Removed build: {build['buildname']}", view=None, embed=None)
                await show_build_selection(interaction)

            # if the build is new, add it to the database and spreadsheet
            if build['id'] == 0:
                if interaction.user.nick == None:
                    username = interaction.user.name
                else:
                    username = interaction.user.nick
                build['id'] = await db.db_add_build(build['user_id'], build['buildname'], build['role'], build['weapon1'], build['weapon2'], build['ability'], build['weight'], build['gearscore'], build['notes'], build['gear'])
                await gs.gs_add_build(build['id'], build['user_id'],  username, build['buildname'], build['role'], build['weapon1'], build['weapon2'], build['ability'], build['weight'], build['gearscore'], build['notes'], build['gear'])

            # create a new view for managing the build
            menu_view = None
            menu_view = View(timeout=None)

            # add a button for each build field
            for field in build:
                if field == "id" or field == "user_id" or field == 'gear':
                    continue
                button = Button(label=friendly_names[field], custom_id=f"{field}")
                button.callback = lambda i, field=field: update_build_field(i, field)
                menu_view.add_item(button)

            gear_image_button = Button(label="Gear Image", custom_id="gear_image")
            gear_image_button.callback = lambda i: upload_gear_image(i, build)
            menu_view.add_item(gear_image_button)

            # add a button for removing the build
            remove_button = Button(label="Remove", style=discord.ButtonStyle.red, custom_id="remove")
            remove_button.callback = remove_build_confirmation
            menu_view.add_item(remove_button)

            # add a button for going back to the build selection view
            back_button = Button(label="Back", style=discord.ButtonStyle.primary, custom_id="back")
            back_button.callback = show_build_selection
            menu_view.add_item(back_button)

            # Create an embed with the build information
            embed = await self.build_info_embed(build)

            # if the user is coming back after a button press, edit the message, otherwise send a new message
            if interaction.message is not None:
                try:
                    await interaction.response.edit_message(content=f"Managing build: **{build['buildname']}**, use the buttons to edit fields or remove this build", embed=embed, view=menu_view)
                except discord.errors.InteractionResponded:
                    await interaction.followup.send(content=f"Managing build: **{build['buildname']}**, use the buttons to edit fields or remove this build", embed=embed, view=menu_view, ephemeral=True)
            else:
                await interaction.response.send_message(content=f"Managing build: **{build['buildname']}**, use the buttons to edit fields or remove this build", embed=embed, view=menu_view, ephemeral=True)
            
        # initial build selection view
        await show_build_selection(ctx)

    @manage.error
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        if isinstance(error, discord.ext.commands.errors.MissingRole):
            await ctx.respond("You don't have permission to run this command!", ephemeral=True)
        else:
            # log the error
            print(f"An error occurred: {error}")
            await ctx.respond("An error occurred while running the command. Please try again later.", ephemeral=True)



def setup(bot):
    bot.add_cog(Build(bot))