import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import time

CONFIG_PATH = "data/settings/auto_thread.json"

def load_enabled_channels():
    if not os.path.exists(CONFIG_PATH):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump([], f)
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def save_enabled_channels(data):
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=4)

class AutoThread(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.enabled_channels = load_enabled_channels()
        self.user_cooldowns = {}  # Format: {channel_id: {user_id: last_timestamp}}

    @app_commands.command(name="enableautothread", description="Enable auto-thread in this channel")
    async def enable_autothread(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message("❌ You need `Manage Channels` permission.", ephemeral=True)

        cid = interaction.channel.id
        if cid in self.enabled_channels:
            return await interaction.response.send_message("ℹ️ Auto-thread already enabled here.", ephemeral=True)

        self.enabled_channels.append(cid)
        save_enabled_channels(self.enabled_channels)
        await interaction.response.send_message("✅ Auto-thread enabled in this channel.", ephemeral=True)

    @app_commands.command(name="disableautothread", description="Disable auto-thread in this channel")
    async def disable_autothread(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message("❌ You need `Manage Channels` permission.", ephemeral=True)

        cid = interaction.channel.id
        if cid not in self.enabled_channels:
            return await interaction.response.send_message("ℹ️ Auto-thread is not enabled here.", ephemeral=True)

        self.enabled_channels.remove(cid)
        save_enabled_channels(self.enabled_channels)
        await interaction.response.send_message("✅ Auto-thread disabled in this channel.", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return

        cid = message.channel.id
        uid = message.author.id

        if cid not in self.enabled_channels:
            return

        # Skip if message is in a thread
        if isinstance(message.channel, discord.Thread):
            return

        now = time.time()
        if cid not in self.user_cooldowns:
            self.user_cooldowns[cid] = {}

        last_time = self.user_cooldowns[cid].get(uid, 0)
        if now - last_time < 60:
            # User is still in cooldown in this channel
            return

        # Update cooldown timestamp
        self.user_cooldowns[cid][uid] = now

        # Try to create thread
        try:
            await message.create_thread(name=f"💬 Thread for {message.author.name}")
        except discord.Forbidden:
            print(f"❌ Missing permissions to create thread in #{message.channel.name}")
        except Exception as e:
            print(f"⚠️ Error creating thread: {e}")

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        await interaction.response.send_message("⚠️ An unexpected error occurred.", ephemeral=True)
        print(f"Error in AutoThread command: {error}")

async def setup(bot):
    await bot.add_cog(AutoThread(bot))
