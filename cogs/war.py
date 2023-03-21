import discord
from discord import SlashCommandGroup, Interaction
from discord.ext import commands
import asyncio
import datetime
import time
import pytz
import random
import os
import logging

#respawn_waves = [60, 80, 100, 120, 140, 160, 180, 200, 220, 240, 260, 280, 300, 336, 365, 392, 413, 448, 476, 505, 532, 561, 589, 611, 653, 688, 725, 760, 798, 833, 868, 904, 940, 985, 1030, 1072, 1118, 1160, 1205, 1250, 1300, 1352, 1402, 1457, 1501, 1570, 1629, 1689, 1750]
respawn_waves = [20, 40, 60, 80, 100, 120, 140, 160, 180, 200, 220, 240, 260, 280, 308, 336, 364, 392, 420, 448, 476, 504, 532, 560, 588, 616, 652, 688, 724, 760, 796, 832, 868, 904, 940, 984, 1028, 1072, 1116, 1160, 1204, 1248, 1300, 1352, 1404, 1456, 1508, 1568, 1628, 1688, 1748]

class War(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.loop_running = False
        self.logger = logging.getLogger("tfrhelper.war")
        self.logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    # You can set a default volume (0 to 1) and a default voice channel ID here:
    default_volume = 0.5
    default_voice_channel_id = 1072906528249630852

    war = SlashCommandGroup(name="war", description="respawn caller commands")

    @war.command(name='schedule', help='Schedule a war.')
    async def schedule(self, interaction: Interaction, wartime: str, channel: int = default_voice_channel_id, volume: float = default_volume):
        await schedule_war(self, interaction, wartime, channel, volume)

    @war.command(name='stop', help='Disconnect the bot from the voice channel.')
    async def stop(self, interaction: Interaction):
        voice_client = interaction.guild.voice_client
        self.logger.info(f"{interaction.user.name} issued the stop command")
        if voice_client is not None and voice_client.is_connected():
            await voice_client.disconnect()
            await interaction.response.send_message(content="Disconnected from the voice channel.")
            self.loop_running = False
            self.logger.info(f"{self.bot.user} disconnected from the voice channel. Loop running: {self.loop_running}")
        else:
            await interaction.response.send_message(content="I'm not connected to a voice channel.")
            self.loop_running = False
            self.logger.info(f"Loop running: {self.loop_running}")

async def schedule_war(self, interaction: Interaction, war_time, channel_id, volume):
    # Convert the input time string to a datetime object in 12-hour format
    war_time = datetime.datetime.strptime(war_time, "%I:%M %p")

    # Set the time zone for Eastern Daylight Time (EDT)
    edt = pytz.timezone("America/New_York")

    # Get the current time in EDT
    current_time = datetime.datetime.now(edt)

    # Set the war date to today or tomorrow, depending on the input time
    war_date = current_time.date()
    if war_time.time() < (current_time - datetime.timedelta(minutes=30)).time():
        war_date = war_date + datetime.timedelta(days=1)

    # Combine the date and time for the war
    war_time = edt.localize(datetime.datetime.combine(war_date, war_time.time()))

    # Calculate the time remaining until the war starts
    time_until_war = (war_time - current_time).total_seconds()

    # Send a confirmation message
    await interaction.response.send_message(content=f"Scheduled war for {war_time.strftime('%Y-%m-%d %H:%M %Z')}.")

    # Calculate the time to join the channel (2 minutes before the war or immediately)
    join_time = max(time_until_war - 120, 0)

    # Schedule the announce_respawn function to run when the bot should join the channel
    await asyncio.sleep(join_time)
    await announce_respawn(self, interaction, time_until_war - join_time, channel_id, volume, war_time.timestamp())

async def play_audio(self, voice_client, file_name, volume):
    self.logger.info(f"Playing {file_name}")
    # Stop any currently playing audio
    if voice_client.is_playing():
        voice_client.stop()

    source = discord.FFmpegPCMAudio(file_name)
    source = discord.PCMVolumeTransformer(source, volume)
    voice_client.play(source)

async def announce_respawn(self, interaction: Interaction, time_until_war, channel, volume, scheduled_start):
    voice_client = await interaction.guild.get_channel(channel).connect()
    self.loop_running = True
    self.logger.info(f"{self.bot.user} connected to the {interaction.guild.get_channel(channel).name} channel.")

    # Only play the intro if the scheduled start of the war has not passed
    if time_until_war > 0:
        await play_audio(self, voice_client, "./wav/intro.wav", volume)  # Introduce itself

    # Sleep until the war starts
    await asyncio.sleep(time_until_war)

    current_time = time.time()

    # Calculate the elapsed time since the scheduled start of the war in seconds
    elapsed_time = int(current_time - scheduled_start)

    # Find the nearest respawn wave
    nearest_wave_index = None
    for i, wave in enumerate(respawn_waves):
        if wave >= elapsed_time:
            nearest_wave_index = i
            break

    # If no wave is found, start from the first wave
    if nearest_wave_index is None:
        nearest_wave_index = 0

    prev_wave = scheduled_start
    for wave in respawn_waves[nearest_wave_index:]:
        wave_time = scheduled_start + wave
        time_since_last_wave = wave - prev_wave
        prev_wave = wave

        if self.loop_running:
            self.logger.info(f"Next expected respawn wave at {datetime.datetime.fromtimestamp(wave_time)}")

            while current_time < wave_time - 30:
                await asyncio.sleep(1)
                current_time = time.time()

            if time_since_last_wave > 30 and self.loop_running:
                await play_audio(self, voice_client, "./wav/30_seconds.wav", volume)

            while current_time < wave_time - 20 and self.loop_running:
                await asyncio.sleep(1)
                current_time = time.time()

            if time_since_last_wave > 20 and self.loop_running:
                await play_audio(self, voice_client, "./wav/20_seconds.wav", volume)

            while current_time < wave_time - 15 and self.loop_running:
                await asyncio.sleep(1)
                current_time = time.time()

            if time_since_last_wave > 15 and self.loop_running:
                await play_audio(self, voice_client, "./wav/15_seconds.wav", volume)

            while current_time < wave_time - 10 and self.loop_running:
                await asyncio.sleep(1)
                current_time = time.time()

            if time_since_last_wave > 10 and self.loop_running:
                await play_audio(self, voice_client, "./wav/10_seconds.wav", volume)

            while current_time < wave_time - 5 and self.loop_running:
                await asyncio.sleep(1)
                current_time = time.time()

            for countdown in range(5, 0, -1):
                remaining_time = wave_time - current_time
                if remaining_time > countdown - 1 and self.loop_running:
                    await play_audio(self, voice_client, f"./wav/{countdown}_seconds.wav", volume)
                await asyncio.sleep(remaining_time - (countdown - 1))
                current_time = time.time()
                if countdown == 1:
                    break

            if self.loop_running:
                await play_audio(self, voice_client, "./wav/respawn.wav", volume)  # Announce the respawn
        else:
            self.logger.info(f"Loop running: {self.loop_running}")
            return

    # Calculate the war duration
    war_duration = 1800
    
    # Calculate the end time of the war
    war_end_time = scheduled_start + war_duration
    
    # Wait until the end of the war
    while current_time < war_end_time and self.loop_running:
        await asyncio.sleep(1)
        current_time = time.time()
    
    # Play a random clip with a 1/10 chance
    if random.randint(1, 10) == 1 and self.loop_running:
        # Wait for 15 seconds before playing the random clip
        await asyncio.sleep(15)
    
        random_directory = "./wav/random"
        random_files = [f for f in os.listdir(random_directory) if os.path.isfile(os.path.join(random_directory, f))]
        random_file = random.choice(random_files)
        random_file_path = os.path.join(random_directory, random_file)
        await play_audio(self, voice_client, random_file_path, volume)
    
    await voice_client.disconnect()
    self.loop_running = False
    self.logger.info(f"{self.bot.user} disconnected from the voice channel. Loop running: {self.loop_running}")

def setup(bot):
    bot.add_cog(War(bot))