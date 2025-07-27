import discord
from discord.ext import commands
import os
import json
import asyncio
import keep_alive
import traceback

# ✅ Start keep-alive web server (for Render free tier to stay alive)
keep_alive.keep_alive()

# ✅ Load configuration from JSON
CONFIG_PATH = "data/config.json"
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
else:
    config = {}

# ✅ Ensure required environment variable is set
if "APPLICATION_ID" not in os.environ:
    raise ValueError("❌ Missing APPLICATION_ID environment variable. Set it in Render.")

# ✅ Bot setup with all intents and application_id
intents = discord.Intents.all()
bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    application_id=int(os.environ["APPLICATION_ID"])  # Required for slash command sync
)

# ✅ Import persistent views from cogs
from cogs.vc_logic import handle_vc_update
from cogs.vc_create import VCButtonView
from cogs.ticket import TicketButton

# ✅ Setup persistent views (required after bot restarts)
@bot.event
async def setup_hook():
    bot.add_view(VCButtonView())
    bot.add_view(TicketButton())

# ✅ On bot ready: Print bot info
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} ({bot.user.id})")

    try:
        if config.get("test_guild_id"):
            test_guild = discord.Object(id=int(config["test_guild_id"]))
            await bot.tree.sync(guild=test_guild)
            print(f"🧪 Slash commands synced to test server: {config['test_guild_id']}")
        else:
            await bot.tree.sync()
            print("🌐 Slash commands synced globally.")
    except Exception as e:
        print(f"❌ Failed to sync slash commands: {e}")

# ✅ Voice channel update events (for VC role system)
@bot.event
async def on_voice_state_update(member, before, after):
    await handle_vc_update(member, before, after)

# ✅ Load all cog files dynamically
async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and filename != "vc_logic.py":
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"✅ Loaded extension: cogs.{filename[:-3]}")
            except Exception:
                print(f"❌ Failed to load extension: cogs.{filename}")
                traceback.print_exc()

# ✅ Main function to launch bot
async def main():
    async with bot:
        await load_cogs()

        # ✅ Sync slash commands (again here after cogs load)
        try:
            if config.get("test_guild_id"):
                test_guild = discord.Object(id=int(config["test_guild_id"]))
                await bot.tree.sync(guild=test_guild)
                print(f"🧪 Slash commands synced to test server: {config['test_guild_id']}")
            else:
                await bot.tree.sync()
                print("🌐 Slash commands synced globally.")
        except Exception as e:
            print(f"❌ Slash command sync error: {e}")

        # ✅ Fetch bot token from Render environment
        token = os.getenv("DISCORD_BOT_TOKEN") or os.getenv("TOKEN")
        if not token:
            print("❌ Bot token not found. Set DISCORD_BOT_TOKEN or TOKEN in Render environment.")
            return

        print("🚀 Starting bot...")
        await bot.start(token)

# ✅ Run main entry point
asyncio.run(main())
