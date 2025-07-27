import discord
from discord.ext import commands
from discord import app_commands
import re
import os
import json
import time
from collections import deque

from utils.logger import log_action

SETTINGS_PATH = "data/settings/spamfilter.json"
USER_COOLDOWN = 10  # seconds
USER_HISTORY_LIMIT = 5  # check last 5 messages

def load_settings():
    if not os.path.exists(SETTINGS_PATH):
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        with open(SETTINGS_PATH, "w") as f:
            json.dump({"enabled": False, "ignored_channels": [], "spam_alert_role_id": None}, f)
    with open(SETTINGS_PATH, "r") as f:
        return json.load(f)

def save_settings(data):
    with open(SETTINGS_PATH, "w") as f:
        json.dump(data, f, indent=4)

class SpamFilter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings = load_settings()
        self.user_timestamps = {}  # cooldown tracker
        self.user_history = {}     # user_id: deque of last messages

    def reload_settings(self):
        self.settings = load_settings()

    def is_on_cooldown(self, user_id: int) -> bool:
        now = time.time()
        return now - self.user_timestamps.get(user_id, 0) < USER_COOLDOWN

    def update_cooldown(self, user_id: int):
        self.user_timestamps[user_id] = time.time()

    def update_history(self, user_id: int, content: str):
        if user_id not in self.user_history:
            self.user_history[user_id] = deque(maxlen=USER_HISTORY_LIMIT)
        self.user_history[user_id].append(content.strip().lower())

    def is_repeating_history(self, user_id: int) -> bool:
        history = self.user_history.get(user_id, [])
        if len(history) < USER_HISTORY_LIMIT:
            return False
        return all(msg == history[0] for msg in history)

    def is_spam(self, content: str, user_id: int) -> bool:
        lines = [line.strip() for line in content.split("\n") if line.strip()]
        if len(lines) >= 3 and all(line == lines[0] for line in lines):
            return True

        if re.search(r"([!?@#$%^&*+=~`<>{}\[\]_|\\\/])\1{5,}", content):
            return True

        if re.search(r"([a-zA-Z])\1{5,}", content):
            return True

        if self.is_repeating_history(user_id):
            return True

        return False

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        user_id = message.author.id

        if not self.settings.get("enabled", False):
            return

        if str(message.channel.id) in self.settings.get("ignored_channels", []):
            return

        self.update_history(user_id, message.content)

        if self.is_spam(message.content, user_id) and not self.is_on_cooldown(user_id):
            try:
                await message.delete()
            except discord.Forbidden:
                return
            except Exception as e:
                print(f"⚠️ Failed to delete spam message: {e}")
                return

            role_id = self.settings.get("spam_alert_role_id")
            role_mention = f"<@&{role_id}>" if role_id else None

            try:
                await log_action(
                    self.bot,
                    message.guild,
                    title="🚨 Spam Message Deleted",
                    content=(
                        f"**Author:** {message.author.mention} (`{message.author.id}`)\n"
                        f"**Channel:** {message.channel.mention}\n"
                        f"**Content:**\n```{message.content[:300]}```"
                    ),
                    user=message.author,
                    ping=role_mention  # ✅ Pings role outside embed
                )
            except Exception as e:
                print(f"⚠️ log_action failed in spam filter: {e}")

            self.update_cooldown(user_id)

    # ==== Slash Commands ====

    @app_commands.command(name="setspamfilter", description="Enable or disable spam filter globally")
    async def setspamfilter(self, interaction: discord.Interaction, enabled: bool):
        self.settings["enabled"] = enabled
        save_settings(self.settings)
        await interaction.response.send_message(
            f"✅ Spam filter is now {'enabled' if enabled else 'disabled'} across the server.",
            ephemeral=True
        )

    @app_commands.command(name="ignorespamchannel", description="Disable spam filter in a specific channel")
    async def ignorespamchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        ch_id = str(channel.id)
        if ch_id in self.settings["ignored_channels"]:
            await interaction.response.send_message("⚠️ This channel is already ignored.", ephemeral=True)
            return

        self.settings["ignored_channels"].append(ch_id)
        save_settings(self.settings)
        await interaction.response.send_message(f"✅ Spam filter disabled in {channel.mention}.", ephemeral=True)

    @app_commands.command(name="unignorespamchannel", description="Re-enable spam filter in an ignored channel")
    async def unignorespamchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        ch_id = str(channel.id)
        if ch_id not in self.settings["ignored_channels"]:
            await interaction.response.send_message("⚠️ This channel is not ignored.", ephemeral=True)
            return

        self.settings["ignored_channels"].remove(ch_id)
        save_settings(self.settings)
        await interaction.response.send_message(f"✅ Spam filter re-enabled in {channel.mention}.", ephemeral=True)

    @app_commands.command(name="setspamalertrole", description="Set a role to tag in spam log reports")
    @app_commands.checks.has_permissions(administrator=True)
    async def setspamalertrole(self, interaction: discord.Interaction, role: discord.Role):
        self.settings["spam_alert_role_id"] = role.id
        save_settings(self.settings)
        await interaction.response.send_message(f"✅ Spam alert role set to: {role.mention}", ephemeral=True)

    @app_commands.command(name="spamstatus", description="Show current spam filter settings")
    async def spamstatus(self, interaction: discord.Interaction):
        enabled = self.settings.get("enabled", False)
        ignored = self.settings.get("ignored_channels", [])
        alert_role = self.settings.get("spam_alert_role_id")

        embed = discord.Embed(title="🛡️ Spam Filter Status", color=0xf1c40f)
        embed.add_field(name="Status", value="✅ Enabled" if enabled else "❌ Disabled", inline=False)

        if ignored:
            channels = "\n".join(f"<#{cid}>" for cid in ignored)
            embed.add_field(name="Ignored Channels", value=channels, inline=False)
        else:
            embed.add_field(name="Ignored Channels", value="None", inline=False)

        if alert_role:
            embed.add_field(name="Alert Role", value=f"<@&{alert_role}>", inline=False)
        else:
            embed.add_field(name="Alert Role", value="Not set", inline=False)

        embed.set_footer(text=f"Cooldown: {USER_COOLDOWN}s per user")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(SpamFilter(bot))
