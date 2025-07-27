import discord
import json
import os

SETTINGS_PATH = "data/settings/log_channel.json"

def get_log_channel_id(guild_id: int):
    if not os.path.exists(SETTINGS_PATH):
        return None

    with open(SETTINGS_PATH, "r") as f:
        data = json.load(f)
        return data.get(str(guild_id))

async def log_action(
    bot,
    guild: discord.Guild,
    title: str,
    content: str,
    user: discord.User = None,
    ping: str = None  # Optional ping (e.g., "<@&role_id>")
):
    channel_id = get_log_channel_id(guild.id)
    if not channel_id:
        return

    log_channel = guild.get_channel(int(channel_id))
    if not log_channel:
        return

    embed = discord.Embed(title=title, description=content, color=0xff9f43)

    if user:
        embed.set_footer(text=f"{user.name}#{user.discriminator}", icon_url=user.display_avatar.url)

    try:
        if ping:
            await log_channel.send(content=ping, embed=embed)
        else:
            await log_channel.send(embed=embed)
    except discord.Forbidden:
        print("❌ Missing permissions to send logs in the log channel.")
    except Exception as e:
        print(f"⚠️ Failed to send log: {e}")
