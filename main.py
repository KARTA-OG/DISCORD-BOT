import discord
from discord.ext import commands
import os
import json
import asyncio
import keep_alive
import traceback

# ✅ Start keep-alive web server
keep_alive.keep_alive()

# ✅ Load config
CONFIG_PATH = "data/config.json"
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
else:
    config = {}

# ✅ Bot setup
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ✅ Persistent views
from cogs.vc_logic import handle_vc_update
from cogs.vc_create import VCButtonView
from cogs.ticket import TicketButton

@bot.event
async def setup_hook():
    # ✅ Only keep persistent views here
    bot.add_view(VCButtonView())
    bot.add_view(TicketButton())

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

@bot.event
async def on_voice_state_update(member, before, after):
    await handle_vc_update(member, before, after)

# 🔁 Load all cogs
async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and filename != "vc_logic.py":
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"✅ Loaded extension: cogs.{filename[:-3]}")
            except Exception:
                print(f"❌ Failed to load extension {filename}")
                traceback.print_exc()

# 🚀 Start bot
async def main():
    async with bot:
        await load_cogs()  # ⬅️ Load all cogs first!

        # ✅ Now sync slash commands
        if config.get("test_guild_id"):
            test_guild = discord.Object(id=int(config["test_guild_id"]))
            await bot.tree.sync(guild=test_guild)
            print(f"🧪 Slash commands synced to test server: {config['test_guild_id']}")
        else:
            await bot.tree.sync()
            print("🌐 Slash commands synced globally")

        token = os.getenv("DISCORD_BOT_TOKEN") or os.getenv("TOKEN")
        if not token:
            print("❌ Bot token not found. Set DISCORD_BOT_TOKEN in Render environment.")
            return

        print("🚀 Starting bot...")
        await bot.start(token)

asyncio.run(main())
