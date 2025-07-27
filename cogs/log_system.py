
import discord
from discord.ext import commands
from discord import app_commands
import os
import json
import datetime

LOG_PATH = "data/settings/log_channel.json"
VC_TRACKER = {}  # Stores join and stream times

def load_log_config():
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, "r") as f:
            return json.load(f)
    return {}

def save_log_config(data):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "w") as f:
        json.dump(data, f, indent=4)

def get_log_channel_id(guild_id: int):
    data = load_log_config()
    return data.get(str(guild_id))

class LogSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setlogchannel", description="Set the log channel for this server")
    @app_commands.checks.has_permissions(administrator=True)
    async def setlogchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)
        config = load_log_config()
        config[guild_id] = str(channel.id)
        save_log_config(config)

        await interaction.response.send_message(
            f"✅ Log channel set to {channel.mention}", ephemeral=True
        )

    @setlogchannel.error
    async def setlogchannel_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ You need Administrator permissions to use this command.",
                ephemeral=True
            )

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        log_channel_id = get_log_channel_id(member.guild.id)
        if not log_channel_id:
            return

        channel = member.guild.get_channel(int(log_channel_id))
        if not channel:
            return

        now = datetime.datetime.utcnow()
        uid = str(member.id)

        embed = discord.Embed(color=discord.Color.orange())
        embed.set_author(name=str(member), icon_url=member.display_avatar.url)

        # 🔊 Join
        if not before.channel and after.channel:
            embed.title = "🔊 Voice Join"
            embed.description = f"{member.mention} joined {after.channel.mention}"
            VC_TRACKER[uid] = {"join_time": now}

        # 📤 Leave
        elif before.channel and not after.channel:
            join_info = VC_TRACKER.get(uid, {})
            embed.title = "📤 Voice Leave"
            embed.description = f"{member.mention} left {before.channel.mention}"

            if "join_time" in join_info:
                duration = now - join_info["join_time"]
                minutes, seconds = divmod(duration.total_seconds(), 60)
                embed.add_field(name="⏱️ Duration", value=f"{int(minutes)}m {int(seconds)}s", inline=False)
            VC_TRACKER.pop(uid, None)

        # 🔁 Move
        elif before.channel != after.channel:
            embed.title = "🔁 Voice Moved"
            embed.description = f"{member.mention} moved from {before.channel.mention} to {after.channel.mention}"
            VC_TRACKER[uid] = {"join_time": now}

        # 📺 Streaming Start/Stop
        if not before.self_stream and after.self_stream:
            embed.title = "📺 Stream Started"
            embed.description = f"{member.mention} started streaming in {after.channel.mention}"
            VC_TRACKER.setdefault(uid, {})["stream_start"] = now

        elif before.self_stream and not after.self_stream:
            embed.title = "📴 Stream Ended"
            embed.description = f"{member.mention} stopped streaming in {before.channel.mention}"
            stream_start = VC_TRACKER.get(uid, {}).get("stream_start")
            if stream_start:
                duration = now - stream_start
                minutes, seconds = divmod(duration.total_seconds(), 60)
                embed.add_field(name="⏱️ Stream Duration", value=f"{int(minutes)}m {int(seconds)}s", inline=False)
                VC_TRACKER[uid]["stream_start"] = None

        else:
            if embed.title is None:
                return

        try:
            await channel.send(embed=embed)
        except Exception as e:
            print(f"⚠️ Failed to send voice log embed: {e}")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        log_channel_id = get_log_channel_id(member.guild.id)
        if not log_channel_id:
            return

        channel = member.guild.get_channel(int(log_channel_id))
        if not channel:
            return

        try:
            async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
                if entry.target.id == member.id:
                    embed = discord.Embed(
                        title="❌ Member Kicked",
                        description=f"{member.mention} was kicked by {entry.user.mention}",
                        color=discord.Color.red()
                    )
                    await channel.send(embed=embed)
                    return
        except Exception as e:
            print(f"⚠️ Error checking kick logs: {e}")

# ✅ Required
async def setup(bot):
    await bot.add_cog(LogSystem(bot))
