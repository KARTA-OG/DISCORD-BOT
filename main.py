import discord
from discord.ext import commands
import os
import json
import asyncio
import keep_alive
import traceback

keep_alive.keep_alive()

CONFIG_PATH = "data/config.json"
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
else:
    config = {}

if "APPLICATION_ID" not in os.environ:
    raise ValueError("❌ Missing APPLICATION_ID in Render environment!")

intents = discord.Intents.all()
bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    application_id=int(os.environ["APPLICATION_ID"])
)

from cogs.vc_logic import handle_vc_update
from cogs.vc_create import VCButtonView
from cogs.ticket import TicketButton

@bot.event
async def setup_hook():
    bot.add_view(VCButtonView())
    bot.add_view(TicketButton())

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} ({bot.user.id})")

# Handle VC role logic
@bot.event
async def on_voice_state_update(member, before, after):
    await handle_vc_update(member, before, after)

# Load cogs dynamically
async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and filename != "vc_logic.py":
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"✅ Loaded cog: cogs.{filename[:-3]}")
            except Exception as e:
                print(f"❌ Failed to load cog: cogs.{filename}")
                traceback.print_exc()

# Main launch function
async def main():
    async with bot:
        await load_cogs()

        try:
            if config.get("test_guild_id"):
                test_guild = discord.Object(id=int(config["test_guild_id"]))
                commands = await bot.tree.sync(guild=test_guild)
                print(f"🧪 Synced {len(commands)} commands to test server: {config['test_guild_id']}")
            else:
                commands = await bot.tree.sync()
                print(f"🌐 Synced {len(commands)} global commands.")

            # 📌 Print all slash commands
            for cmd in commands:
                print(f"📌 /{cmd.name}")
        except Exception as e:
            print(f"❌ Slash command sync error: {e}")
            traceback.print_exc()

        token = os.getenv("DISCORD_BOT_TOKEN") or os.getenv("TOKEN")
        if not token:
            print("❌ Bot token not found. Set DISCORD_BOT_TOKEN or TOKEN in Render.")
            return

        print("🚀 Starting bot...")
        await bot.start(token)

asyncio.run(main())
