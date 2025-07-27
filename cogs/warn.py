import discord
from discord.ext import commands
from discord import app_commands
import json
import os

WARN_DATA_PATH = "data/warnings/warn_data.json"
WARN_LOG_PATH = "data/warnings/warn_log_channel.json"

def load_json(path, default):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(default, f, indent=4)
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

class WarnSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warn_data = load_json(WARN_DATA_PATH, {})
        self.log_channel_data = load_json(WARN_LOG_PATH, {})

    def is_admin(self, user: discord.Member):
        config = load_json("data/config.json", {})
        admin_role_id = config.get("admin_role_id")
        return admin_role_id in [role.id for role in user.roles]

    @app_commands.command(name="warn", description="Issue a warning to a user.")
    @app_commands.describe(user="User to warn", reason="Reason for the warning")
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        if not self.is_admin(interaction.user):
            return await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)

        uid = str(user.id)
        if uid not in self.warn_data:
            self.warn_data[uid] = []

        self.warn_data[uid].append({
            "reason": reason,
            "moderator": str(interaction.user),
        })
        save_json(WARN_DATA_PATH, self.warn_data)

        # DM the user
        try:
            await user.send(f"⚠️ You have been warned in **{interaction.guild.name}** for:\n> {reason}")
        except:
            pass

        await interaction.response.send_message(f"✅ Warned {user.mention} for: `{reason}`", ephemeral=True)

        # Log it
        log_channel_id = self.log_channel_data.get(str(interaction.guild.id))
        if log_channel_id:
            log_channel = interaction.guild.get_channel(log_channel_id)
            if log_channel:
                embed = discord.Embed(title="⚠️ User Warned", color=discord.Color.orange())
                embed.add_field(name="User", value=f"{user} ({user.id})", inline=False)
                embed.add_field(name="Moderator", value=str(interaction.user), inline=False)
                embed.add_field(name="Reason", value=reason, inline=False)
                await log_channel.send(embed=embed)

    @app_commands.command(name="warnstatus", description="View warnings of a user.")
    async def warnstatus(self, interaction: discord.Interaction, user: discord.Member):
        uid = str(user.id)
        warns = self.warn_data.get(uid, [])

        if not warns:
            return await interaction.response.send_message(f"✅ {user.mention} has no warnings.", ephemeral=True)

        embed = discord.Embed(title=f"⚠️ Warnings for {user}", color=discord.Color.yellow())
        for idx, warn in enumerate(warns, start=1):
            embed.add_field(name=f"#{idx}", value=f"**Reason:** {warn['reason']}\n**By:** {warn['moderator']}", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="removewarn", description="Remove a specific warning by number")
    @app_commands.describe(user="User to remove warning from", index="Warning number to remove (1, 2...)")
    async def removewarn(self, interaction: discord.Interaction, user: discord.Member, index: int):
        if not self.is_admin(interaction.user):
            return await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)

        uid = str(user.id)
        if uid not in self.warn_data or index < 1 or index > len(self.warn_data[uid]):
            return await interaction.response.send_message("⚠️ Invalid warning index.", ephemeral=True)

        removed = self.warn_data[uid].pop(index - 1)
        if not self.warn_data[uid]:
            del self.warn_data[uid]

        save_json(WARN_DATA_PATH, self.warn_data)
        await interaction.response.send_message(f"✅ Removed warning #{index} from {user.mention}: `{removed['reason']}`", ephemeral=True)

    @app_commands.command(name="setwarnlog", description="Set the channel to log warnings.")
    @app_commands.describe(channel="The channel where warning logs will be sent")
    async def setwarnlog(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not self.is_admin(interaction.user):
            return await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)

        self.log_channel_data[str(interaction.guild.id)] = channel.id
        save_json(WARN_LOG_PATH, self.log_channel_data)
        await interaction.response.send_message(f"✅ Set warning log channel to {channel.mention}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(WarnSystem(bot))
