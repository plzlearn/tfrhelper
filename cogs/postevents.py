import discord
from discord import Embed
from discord.ext import commands, tasks
import sys
sys.path.append("../utils")
import utils.jsonhandler as jsonhandler
import asyncio
import datetime
import pytz
import requests

class PostEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.display_events_task.start()
        self.update_prices_cache_task.start()

    def cog_unload(self):
        self.display_events_task.cancel()
        self.update_prices_cache_task.cancel()

    async def update_prices_cache(self):
        url = "https://nwmarketprices.com/api/latest-prices/68/"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            with open('prices_cache.json', 'w') as f:
                jsonhandler.json.dump(data, f)
        else:
            print(f"Error: {response.status_code}")

    @tasks.loop(hours=24)
    async def update_prices_cache_task(self):
        await self.update_prices_cache()

    @tasks.loop(hours=1)
    async def display_events_task(self):
        # Get the destination channel or user ID from the config file
        config_file = 'config.json'
        config = jsonhandler.load_json_file(config_file)
        destination_id = config.get('events_channel_id')

        if destination_id is not None:
            # Get the destination channel or user object
            destination = await self.bot.fetch_channel(destination_id)

            # Get the events
            events = jsonhandler.get_events()
            events = sorted(events, key=lambda e: datetime.datetime.strptime(e['event_date'] + ' ' + e['event_time'], '%m/%d %I:%M %p'))

            # Create the event text string
            event_text = ""
            for event in events:
                event_text += f"{event['event_text']}\n"

            # Create the embed
            embed = Embed(title="UPCOMING COMPANY EVENTS")
            embed.description = "======================================================================="
            embed.add_field(name="", value=event_text)

            # Calculate the time until the next update
            update_time_str = config.get('events_update_time', '10:00:00')  # Update time in 24-hour format
            timezone_str = config.get('events_timezone', 'UTC')
            timezone = pytz.timezone(timezone_str)
            now = datetime.datetime.now(tz=timezone)
            tomorrow = now + datetime.timedelta(days=1)
            update_time = datetime.datetime.strptime(update_time_str, "%H:%M:%S").time()
            update_datetime_local = timezone.localize(datetime.datetime.combine(tomorrow.date(), update_time))
            # Convert datetime to UTC
            update_datetime_utc = update_datetime_local.astimezone(pytz.utc)

            # If it's not yet time to post the initial embed, wait until the scheduled time
            if self.display_events_task.current_loop == 0:
                await asyncio.sleep((update_datetime_utc - datetime.datetime.now(pytz.utc)).total_seconds())

            # Send the embed to the destination channel or user
            await destination.send(embed=embed)

        # Wait until the next update time
        await asyncio.sleep((update_datetime_utc - datetime.datetime.now(pytz.utc)).total_seconds())

    def cog_unload(self):
        self.display_events_task.cancel()
        self.update_prices_cache_task.cancel()

def setup(bot):
    bot.add_cog(PostEvents(bot))