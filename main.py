import discord
from discord.ext import commands
import os
import json
import asyncio
import keep_alive
import traceback

# ✅ Start keep-alive for Render
keep_alive.keep_alive()

# ✅ Load config
CONFIG_PATH = "data/config.json"
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
else:
    config = {}

# ✅ Check required env var
if "APPLICATION_ID" not in os.environ:
    raise ValueError("❌ APPLICATION_ID is not set in Render!")

# ✅ Setup bot
intents = discord.Intents.all()
bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    application_id=int(os.environ["APPLICATION_ID"])
)

# ✅ Import view buttons
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

# ✅ VC role handler
@bot.event
async def on_voice_state_update(member, before, after):
    await handle_vc_update(member, before, after)

# ✅ Load all cogs from folder
async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and filename != "vc_logic.py":
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"✅ Loaded: cogs.{filename[:-3]}")
            except Exception:
                print(f"❌ Failed to load cogs.{filename}")
                traceback.print_exc()

# ✅ Main function
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

            # 👇 Print all synced command names
            for cmd in commands:
                print(f"📌 /{cmd.name}")
        except Exception as e:
            print(f"❌ Failed to sync slash commands: {e}")

        # ✅ Token check
        token = os.getenv("DISCORD_BOT_TOKEN") or os.getenv("TOKEN")
        if not token:
            print("❌ DISCORD_BOT_TOKEN not set in Render.")
            return

        print("🚀 Starting bot...")
        await bot.start(token)

asyncio.run(main())
