import discord
from discord.ext import commands
from discord import app_commands
import json
import os

CONFIG_PATH = "data/settings/auto_thread.json"

def load_config():
    if not os.path.exists(CONFIG_PATH):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump([], f)
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=4)

class AutoThread(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.enabled_channels = load_config()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.channel.id in self.enabled_channels:
            try:
                await message.create_thread(name=f"💬 Thread for {message.author.name}")
                print(f"✅ Created thread in #{message.channel.name} for {message.author}")
            except discord.Forbidden:
                print(f"❌ No permission to create thread in #{message.channel.name}")
            except Exception as e:
                print(f"⚠️ Failed to create thread: {e}")

    @app_commands.command(name="enableautothread", description="Enable auto-thread creation in this channel")
    async def enable_autothread(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message(
                "❌ You need `Manage Channels` permission to use this.", ephemeral=True
            )

        cid = interaction.channel.id
        if cid in self.enabled_channels:
            return await interaction.response.send_message("ℹ️ Already enabled.", ephemeral=True)

        self.enabled_channels.append(cid)
        save_config(self.enabled_channels)
        await interaction.response.send_message("✅ Auto-thread enabled for this channel.", ephemeral=True)

    @app_commands.command(name="disableautothread", description="Disable auto-thread in this channel")
    async def disable_autothread(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message(
                "❌ You need `Manage Channels` permission to use this.", ephemeral=True
            )

        cid = interaction.channel.id
        if cid not in self.enabled_channels:
            return await interaction.response.send_message("ℹ️ Auto-thread is not enabled here.", ephemeral=True)

        self.enabled_channels.remove(cid)
        save_config(self.enabled_channels)
        await interaction.response.send_message("✅ Auto-thread disabled for this channel.", ephemeral=True)

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        try:
            await interaction.response.send_message("⚠️ Something went wrong.", ephemeral=True)
        except discord.InteractionResponded:
            await interaction.followup.send("⚠️ Error occurred after response.", ephemeral=True)
        print(f"[AUTO_THREAD ERROR] {error}")

async def setup(bot):
    await bot.add_cog(AutoThread(bot))
