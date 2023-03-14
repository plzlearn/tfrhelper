import discord
from discord import Embed, Option
from discord.ext import commands, tasks
import sys
sys.path.append("../utils")
import utils.jsonhandler as json
import requests
import datetime
import pytz

class Market(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def item_embed(self, ctx, price: dict):
        date, time = convert_timestamp(price['LastUpdated'])
        # {"ItemId": "fishingbishopfisht5", "ItemName": "Abaia Serpe", "Price": "2200", "Availability": 1, "LastUpdated": "2023-03-14T11:31:25.811419", "HighestBuyOrder": 10, "Qty": 1}
        embed=Embed(title=f"{price['ItemName']}", url=f"https://nwdb.info/db/item/{price['ItemId']}", description=f"**Seer** market information for {price['ItemName']}")
        embed.set_author(name="New World Market Prices", url="https://nwmarketprices.com/68" ,icon_url="https://nwmarketprices.com/static/images/cropped-logo4-60.png")
        embed.add_field(name="__Price__", value=f"{price['Price']}", inline=True)
        embed.add_field(name="__Available__", value=f"{price['Availability']}", inline=True)
        embed.add_field(name="", value="", inline=True)
        embed.add_field(name="__Highest Buy Order__", value=f"{price['HighestBuyOrder']}", inline=True)
        embed.add_field(name="__Quantity__", value=f"{price['Qty']}", inline=True)
        embed.add_field(name="", value="", inline=True)
        embed.set_thumbnail(url=f"https://nwmarketprices.com/static/images/cropped-logo4-60.png")
        embed.set_footer(text=f"Last Updated: ᲼{date} ᲼•᲼ {time}\nRequested by {ctx.author.nick}, data provided by nwmarketprices.com")
        embed.set_image(url=f"https://cdn.nwdb.info/db/images/live/v21/icons/items_hires/{price['ItemId']}.png")
        embed.color=0x346049
        return embed
    

    @commands.slash_command(name="market", description="search market prices and other information")
    async def market(self, ctx, item: Option(str, description="name of the item to search for", required=True), hidden: Option(str, description="display search to everyone?", choices=["true","false"], default="true")):
        with open('prices_cache.json', 'r') as f:
            data = json.json.load(f)

        item_lower = item.lower()
        
        for price in data:
            if price['ItemName'].lower() == item_lower:  # Convert the item name in the data list to lowercase and compare
                embed = await self.item_embed(ctx, price)
                if hidden == "true":
                    await ctx.respond(embed=embed, ephemeral=True)
                else:
                    await ctx.respond(embed=embed, ephemeral=False)
                break  # Stop searching once we find the matching item
        else:
            await ctx.respond(f"No information found for **{item}**. There are currently no listings for **{item}**, or you've mistyped the name.", ephemeral=True)

def convert_timestamp(timestamp):
    # Create a datetime object for the given timestamp
    dt_naive = datetime.datetime.fromisoformat(timestamp)

    # Get the current datetime in EST timezone
    tz = pytz.timezone('US/Eastern')
    dt = tz.localize(dt_naive)
    current_time = datetime.datetime.now(tz)

    # Calculate the time difference between the current time and the given timestamp
    time_diff = current_time - dt

    # Assign the appropriate string value to the date variable
    if time_diff.days == 1:
        date = 'Yesterday'
    elif time_diff.days == 0:
        date = 'Today'
    else:
        date = dt.strftime('%m/%d')

    # Extract the time from the datetime object and convert it into a 12-hour format
    time = dt.astimezone(tz).strftime('%I:%M:%S %p')

    # Return the date and time strings
    return date, time 


def setup(bot):
    bot.add_cog(Market(bot))