import discord
from discord.ext import commands
from discord import app_commands
import json
import os

BADWORD_PATH = "data/settings/badwords.json"
STICKY_PATH = "data/settings/sticky_channels.json"
LOG_PATH = "data/settings/log.json"

class StatusReload(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def load_json(self, path):
        if not os.path.exists(path):
            return {}
        with open(path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}

    @app_commands.command(name="botstatus", description="Show current bot feature status")
    @app_commands.checks.has_permissions(administrator=True)
    async def botstatus(self, interaction: discord.Interaction):
        badword_data = self.load_json(BADWORD_PATH)
        sticky_data = self.load_json(STICKY_PATH)
        log_data = self.load_json(LOG_PATH)

        embed = discord.Embed(title="📊 Bot Feature Status", color=0x3498db)

        # Log Channel
        log_status = "❌ Not Set"
        if str(interaction.guild.id) in log_data:
            ch_id = log_data[str(interaction.guild.id)]
            log_status = f"<#{ch_id}>"

        # Sticky Channels
        sticky_list = [f"<#{cid}>" for cid in sticky_data] if isinstance(sticky_data, list) else []
        sticky_status = ", ".join(sticky_list) if sticky_list else "❌ None"

        # Bad Words
        word_count = len(badword_data.get("words", []))
        ignored_channels = badword_data.get("ignored_channels", [])

        embed.add_field(name="📁 Log Channel", value=log_status, inline=False)
        embed.add_field(name="📌 Sticky Channels", value=sticky_status, inline=False)
        embed.add_field(name="🧨 Bad Words Count", value=f"{word_count}", inline=True)
        embed.add_field(
            name="🛑 Ignored Channels",
            value=", ".join(f"<#{ch}>" for ch in ignored_channels) if ignored_channels else "None",
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="reloadsettings", description="Reload all settings from disk")
    @app_commands.checks.has_permissions(administrator=True)
    async def reloadsettings(self, interaction: discord.Interaction):
        try:
            # Reload sticky settings
            sticky_cog = self.bot.get_cog("StickySystem")
            if sticky_cog:
                sticky_cog.sticky_channels = self.load_json(STICKY_PATH) or []

            # Reload bad word settings
            bad_cog = self.bot.get_cog("BadWordFilter")
            if bad_cog:
                bad_cog.settings = self.load_json(BADWORD_PATH) or {"words": [], "ignored_channels": []}

            await interaction.response.send_message("🔁 All settings reloaded from disk.", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to reload: `{e}`", ephemeral=True)

    @botstatus.error
    async def botstatus_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ You need Administrator permission to use this command.", ephemeral=True)

    @reloadsettings.error
    async def reloadsettings_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ You need Administrator permission to use this command.", ephemeral=True)

# ✅ Setup function
async def setup(bot):
    await bot.add_cog(StatusReload(bot))
