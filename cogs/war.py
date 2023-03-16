import discord
from discord.ext import commands, tasks
import asyncio
import datetime
import time
import pytz
import random
import os

intents = discord.Intents.default()
intents.voice_states = True
bot = commands.Bot(command_prefix='!', intents=intents)

respawn_waves = [60, 80, 100, 120, 140, 160, 180, 200, 220, 240, 260, 280, 300, 336, 365, 392, 413, 448, 476, 505, 532, 561, 589, 611, 653, 688, 725, 760, 798, 833, 868, 904, 940, 985, 1030, 1072, 1118, 1160, 1205, 1250, 1300, 1352, 1402, 1457, 1501, 1570, 1629, 1689, 1750]
#respawn_waves = [60, 80, 100, 120, 140, 160, 180, 200, 220, 240, 260, 290, 300, 336, 365, 392, 413, 448, 476, 505, 532, 561, 589, 611, 653, 688, 725, 760, 798, 833, 868, 904, 940, 985, 1030, 1072, 1118, 1160, 1205, 1250, 1300, 1352, 1402, 1457, 1501, 1570, 1629, 1689, 1750]

class War(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # You can set a default volume (0 to 1) and a default voice channel ID here:
    default_volume = 0.5
    default_voice_channel_id = 1072906528249630852

    @commands.slash_command(name="war", description="war commands")
    async def war(self, ctx, wartime: str, channel: int = default_voice_channel_id, volume: float = default_volume):
        await schedule_war(self, ctx, wartime, channel, volume)


async def schedule_war(self, ctx, war_time, channel_id, volume):
    # Convert the input time string to a datetime object
    war_time = datetime.datetime.strptime(war_time, "%H:%M")

    # Set the time zone for Eastern Daylight Time (EDT)
    edt = pytz.timezone("America/New_York")

    # Get the current time in EDT
    current_time = datetime.datetime.now(edt)

    # Set the war date to today or tomorrow, depending on the input time
    war_date = current_time.date()
    if war_time.time() <= current_time.time():
        war_date = war_date + datetime.timedelta(days=1)

    # Combine the date and time for the war
    war_time = edt.localize(datetime.datetime.combine(war_date, war_time.time()))

    # Calculate the time remaining until the war starts
    time_until_war = (war_time - current_time).total_seconds()

    # Send a confirmation message
    await ctx.send(f"Scheduled war for {war_time.strftime('%Y-%m-%d %H:%M %Z')}.")

    # Calculate the time to join the channel (2 minutes before the war or immediately)
    join_time = max(time_until_war - 120, 0)

    # Schedule the announce_respawn function to run when the bot should join the channel
    await asyncio.sleep(join_time)
    await announce_respawn(ctx, time_until_war - join_time, channel_id, volume)

async def play_audio(voice_client, file_name, volume):
    print(f"{datetime.datetime.now()} Playing {file_name}")  # Print the timestamp and the file being played
    # Stop any currently playing audio
    if voice_client.is_playing():
        voice_client.stop()

    source = discord.FFmpegPCMAudio(file_name)
    source = discord.PCMVolumeTransformer(source, volume)
    voice_client.play(source)

async def announce_respawn(ctx, time_until_war, channel, volume):
    voice_client = await ctx.guild.get_channel(channel).connect()
    await play_audio(voice_client, "./wav/intro.wav", volume)  # Introduce itself

    # Sleep until the war starts
    await asyncio.sleep(time_until_war)

    current_time = time.time()
    scheduled_start = current_time

    prev_wave = scheduled_start
    for wave in respawn_waves:
        wave_time = scheduled_start + wave
        time_since_last_wave = wave - prev_wave
        prev_wave = wave

        print(f"Next expected respawn wave at {datetime.datetime.fromtimestamp(wave_time)}")

        while current_time < wave_time - 30:
            await asyncio.sleep(1)
            current_time = time.time()

        if time_since_last_wave > 30:
            await play_audio(voice_client, "./wav/30_seconds.wav", volume)

        while current_time < wave_time - 20:
            await asyncio.sleep(1)
            current_time = time.time()

        if time_since_last_wave > 20:
            await play_audio(voice_client, "./wav/20_seconds.wav", volume)

        while current_time < wave_time - 15:
            await asyncio.sleep(1)
            current_time = time.time()

        if time_since_last_wave > 15:
            await play_audio(voice_client, "./wav/15_seconds.wav", volume)

        while current_time < wave_time - 10:
            await asyncio.sleep(1)
            current_time = time.time()

        if time_since_last_wave > 10:
            await play_audio(voice_client, "./wav/10_seconds.wav", volume)

        while current_time < wave_time - 5:
            await asyncio.sleep(1)
            current_time = time.time()

        for countdown in range(5, 0, -1):
            remaining_time = wave_time - current_time
            if remaining_time > countdown - 1:
                await play_audio(voice_client, f"./wav/{countdown}_seconds.wav", volume)
            await asyncio.sleep(remaining_time - (countdown - 1))
            current_time = time.time()
            if countdown == 1:
                break

        await play_audio(voice_client, "./wav/respawn.wav", volume)  # Announce the respawn

    # 1/10 chance of playing a random clip
    if random.randint(1, 10) == 1:
        # Wait for 15 seconds before playing the random clip
        await asyncio.sleep(15)

        random_directory = "./wav/random"
        random_files = [f for f in os.listdir(random_directory) if os.path.isfile(os.path.join(random_directory, f))]
        random_file = random.choice(random_files)
        random_file_path = os.path.join(random_directory, random_file)
        await play_audio(voice_client, random_file_path, volume)

    await voice_client.disconnect()

def setup(bot):
    bot.add_cog(War(bot))