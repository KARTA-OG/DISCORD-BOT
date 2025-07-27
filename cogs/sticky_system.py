import discord
from discord.ext import commands
from discord import app_commands
import os
import json
from utils.logger import log_action

STICKY_PATH = "data/settings/sticky_channels.json"

def load_sticky_config():
    if os.path.exists(STICKY_PATH):
        with open(STICKY_PATH, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_sticky_config(data):
    os.makedirs(os.path.dirname(STICKY_PATH), exist_ok=True)
    with open(STICKY_PATH, "w") as f:
        json.dump(data, f, indent=4)

REMINDER_TEXT = (
    "📌 **PLEASE DO NOT TEXT HERE , IT IS POST ONLY CHANNEL .**\n"
    "ONLY LINKS AND ADJUSTMENTS ARE ALLOWED TO BE POSTED , CHAT IN THREAD LINKED TO EVERY POST ."
)

class StickySystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sticky_channels = load_sticky_config()
        self.last_reminder_messages = {}  # {channel_id: message}

    def is_valid_post(self, message: discord.Message):
        if message.attachments:
            return True
        if any(url in message.content.lower() for url in ["http://", "https://"]):
            return True
        return False

    async def send_reminder(self, channel: discord.TextChannel):
        try:
            if channel.id in self.last_reminder_messages:
                try:
                    await self.last_reminder_messages[channel.id].delete()
                except (discord.NotFound, discord.Forbidden):
                    pass

            new_msg = await channel.send(REMINDER_TEXT)
            self.last_reminder_messages[channel.id] = new_msg

        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        if isinstance(message.channel, discord.Thread):
            return

        if str(message.channel.id) not in self.sticky_channels:
            return

        if self.is_valid_post(message):
            try:
                await message.create_thread(
                    name=f"Discussion with {message.author.display_name}",
                    auto_archive_duration=1440
                )
            except (discord.Forbidden, discord.HTTPException):
                pass

            await self.send_reminder(message.channel)
            return

        try:
            await message.delete()
        except (discord.Forbidden, discord.HTTPException):
            pass

        try:
            await log_action(
                self.bot,
                message.guild,
                title="Sticky Channel Violation",
                content=(
                    f"🗑️ **Message by {message.author.mention} deleted in {message.channel.mention}** "
                    f"(Not an image or link)\n{message.content}"
                ),
                user=message.author
            )
        except Exception:
            pass

        await self.send_reminder(message.channel)

    @app_commands.command(name="enablesticky", description="Enable sticky note mode in this channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def enablesticky(self, interaction: discord.Interaction):
        ch_id = str(interaction.channel.id)
        if ch_id in self.sticky_channels:
            await interaction.response.send_message(
                "⚠️ Sticky mode is already enabled in this channel.", ephemeral=True
            )
            return

        self.sticky_channels.append(ch_id)
        save_sticky_config(self.sticky_channels)
        await interaction.response.send_message("✅ Sticky note mode enabled in this channel.", ephemeral=True)

    @app_commands.command(name="disablesticky", description="Disable sticky note mode in this channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def disablesticky(self, interaction: discord.Interaction):
        ch_id = str(interaction.channel.id)
        if ch_id not in self.sticky_channels:
            await interaction.response.send_message(
                "⚠️ Sticky mode is not enabled in this channel.", ephemeral=True
            )
            return

        self.sticky_channels.remove(ch_id)
        save_sticky_config(self.sticky_channels)
        await interaction.response.send_message("✅ Sticky note mode disabled in this channel.", ephemeral=True)

    @enablesticky.error
    async def enablesticky_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ You need Administrator permission to use this command.",
                ephemeral=True
            )

    @disablesticky.error
    async def disablesticky_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ You need Administrator permission to use this command.",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(StickySystem(bot))
