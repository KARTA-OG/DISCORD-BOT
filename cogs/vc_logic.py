import discord
from discord.ext import commands
import asyncio
import json
import os

active_vcs = {}

VCROLE_PATH = "data/settings/vcrole.json"
LOG_PATH = "data/settings/logchannel.json"

# Load saved VC roles
if os.path.exists(VCROLE_PATH):
    with open(VCROLE_PATH, "r") as f:
        vc_roles = json.load(f)
else:
    vc_roles = {}

# Load log channel settings
if os.path.exists(LOG_PATH):
    with open(LOG_PATH, "r") as f:
        log_channels = json.load(f)
else:
    log_channels = {}

async def create_voice_channel(bot: commands.Bot, guild: discord.Guild, user: discord.User,
                               channel: discord.TextChannel, category: discord.CategoryChannel,
                               vc_type: str, user_limit: int):

    vc_name = f"{user.name}'s VC"

    # Set permissions
    if vc_type == "private":
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(connect=False, view_channel=False),
            user: discord.PermissionOverwrite(connect=True, view_channel=True, manage_channels=True)
        }
    else:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(connect=True, view_channel=True)
        }

    # Create VC
    voice_channel = await guild.create_voice_channel(
        name=vc_name,
        category=category,
        overwrites=overwrites,
        user_limit=user_limit
    )

    # Move user to VC
    try:
        if user.voice:
            await user.move_to(voice_channel)
    except Exception as e:
        print(f"❌ Failed to move user: {e}")

    # Track VC
    active_vcs[voice_channel.id] = {
        "creator_id": user.id,
        "guild_id": guild.id
    }

    # Log VC creation
    await log_vc_creation(bot, guild.id, user, voice_channel.name, vc_type, user_limit)

    # Auto-delete task
    bot.loop.create_task(auto_delete_vc(bot, voice_channel))

async def auto_delete_vc(bot: commands.Bot, voice_channel: discord.VoiceChannel):
    await asyncio.sleep(10)
    while True:
        await asyncio.sleep(10)
        try:
            if len(voice_channel.members) == 0:
                await voice_channel.delete()
                active_vcs.pop(voice_channel.id, None)
                print(f"🗑️ Deleted empty VC: {voice_channel.name}")
                break
        except Exception as e:
            print(f"❌ Error deleting VC: {e}")
            break

# Handle VC join/leave role
async def handle_vc_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    guild_id = str(member.guild.id)
    role_id = vc_roles.get(guild_id)

    if not role_id:
        return

    role = member.guild.get_role(role_id)
    if not role:
        return

    # User joins a VC created by bot
    if after.channel and after.channel.id in active_vcs:
        try:
            await member.add_roles(role, reason="Joined bot-created VC")
        except Exception as e:
            print(f"❌ Failed to add VC role: {e}")

    # User leaves a VC created by bot
    elif before.channel and before.channel.id in active_vcs:
        try:
            await member.remove_roles(role, reason="Left bot-created VC")
        except Exception as e:
            print(f"❌ Failed to remove VC role: {e}")

# Log VC creation
async def log_vc_creation(bot, guild_id, user, vc_name, vc_type, user_limit):
    guild_id = str(guild_id)
    log_channel_id = log_channels.get(guild_id)
    if not log_channel_id:
        return

    guild = bot.get_guild(int(guild_id))
    if not guild:
        return

    channel = guild.get_channel(int(log_channel_id))
    if not channel:
        return

    embed = discord.Embed(
        title="🎧 Voice Channel Created",
        color=discord.Color.green()
    )
    embed.add_field(name="Name", value=vc_name, inline=True)
    embed.add_field(name="Type", value=vc_type.title(), inline=True)
    embed.add_field(name="User Limit", value=str(user_limit), inline=True)
    embed.add_field(name="Created By", value=user.mention, inline=False)
    embed.set_footer(text=f"Guild: {guild.name}", icon_url=guild.icon.url if guild.icon else None)

    try:
        await channel.send(embed=embed)
    except Exception as e:
        print(f"❌ Failed to send VC log: {e}")
