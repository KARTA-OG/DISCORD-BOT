import discord
from discord.ext import commands
from discord import app_commands
import os
import json

WARN_LOG_PATH = "data/settings/warn_log_channels.json"

def load_warn_log_data():
    if not os.path.exists(WARN_LOG_PATH):
        os.makedirs(os.path.dirname(WARN_LOG_PATH), exist_ok=True)
        with open(WARN_LOG_PATH, "w") as f:
            json.dump({}, f)
    with open(WARN_LOG_PATH, "r") as f:
        return json.load(f)

def save_warn_log_data(data):
    with open(WARN_LOG_PATH, "w") as f:
        json.dump(data, f, indent=4)

class Warn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warn_logs = load_warn_log_data()  # {guild_id: channel_id}

    @app_commands.command(name="setwarnlog", description="Set the channel to log all warnings")
    async def setwarnlog(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message(
                "❌ You need `Manage Server` permission to set the warn log channel.",
                ephemeral=True
            )

        self.warn_logs[str(interaction.guild_id)] = channel.id
        save_warn_log_data(self.warn_logs)

        await interaction.response.send_message(
            f"✅ Warn log channel has been set to {channel.mention}.", ephemeral=True
        )

    @app_commands.command(name="warn", description="Warn a user with a reason")
    @app_commands.describe(user="The user you want to warn", reason="Reason for warning")
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        # DM the warned user
        try:
            embed_dm = discord.Embed(
                title="⚠️ You Have Been Warned",
                description=f"Reason: {reason}",
                color=discord.Color.red()
            )
            embed_dm.set_footer(text=f"Issued by {interaction.user}", icon_url=interaction.user.display_avatar.url)
            await user.send(embed=embed_dm)
        except discord.Forbidden:
            await interaction.response.send_message("❗ Could not DM the user. They may have DMs disabled.", ephemeral=True)

        # Send confirmation to moderator
        await interaction.response.send_message(f"✅ {user.mention} has been warned.", ephemeral=True)

        # Log in warn log channel
        channel_id = self.warn_logs.get(str(interaction.guild_id))
        if channel_id:
            channel = interaction.guild.get_channel(channel_id)
            if channel:
                embed_log = discord.Embed(
                    title="🚨 User Warned",
                    color=discord.Color.orange(),
                    timestamp=interaction.created_at
                )
                embed_log.add_field(name="👤 User", value=f"{user} ({user.id})", inline=False)
                embed_log.add_field(name="🧑‍⚖️ Warned by", value=f"{interaction.user} ({interaction.user.id})", inline=False)
                embed_log.add_field(name="📄 Reason", value=reason, inline=False)
                await channel.send(embed=embed_log)

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        await interaction.response.send_message("⚠️ An error occurred while processing the command.", ephemeral=True)
        print(f"Error in warn command: {error}")

async def setup(bot):
    await bot.add_cog(Warn(bot))
