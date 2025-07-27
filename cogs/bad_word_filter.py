import discord
from discord.ext import commands
from discord import app_commands
import os
import json
import re

from utils.logger import log_action  # ✅ Log system integration

SETTINGS_PATH = "data/settings/badwords.json"

def load_settings():
    os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
    if not os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, "w") as f:
            json.dump({"words": [], "ignored_channels": []}, f)
    with open(SETTINGS_PATH, "r") as f:
        return json.load(f)

def save_settings(settings):
    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=4)

class BadWordFilter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings = load_settings()

    def reload_settings(self):
        """🔁 Reload bad word settings from disk (used by /reloadsettings)"""
        self.settings = load_settings()

    def contains_bad_word(self, message: str):
        for word in self.settings["words"]:
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            if pattern.search(message):
                return True
        return False

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        if str(message.channel.id) in self.settings.get("ignored_channels", []):
            return

        if self.contains_bad_word(message.content):
            try:
                await message.delete()

                # ✅ Log the deleted message
                await log_action(
                    self.bot,
                    message.guild,
                    title="Bad Word Detected",
                    content=f"🚫 **Message by {message.author.mention} deleted in {message.channel.mention}**\n{message.content}",
                    user=message.author
                )

            except discord.Forbidden:
                pass

    @app_commands.command(name="addbadword", description="Add a new word to the bad word list")
    async def addbadword(self, interaction: discord.Interaction, word: str):
        word = word.lower()
        if word in self.settings["words"]:
            await interaction.response.send_message("⚠️ That word is already in the list.", ephemeral=True)
            return

        self.settings["words"].append(word)
        save_settings(self.settings)
        await interaction.response.send_message(f"✅ `{word}` has been added to the bad word list.", ephemeral=True)

    @app_commands.command(name="removebadword", description="Remove a word from the bad word list")
    async def removebadword(self, interaction: discord.Interaction, word: str):
        word = word.lower()
        if word not in self.settings["words"]:
            await interaction.response.send_message("⚠️ That word is not in the list.", ephemeral=True)
            return

        self.settings["words"].remove(word)
        save_settings(self.settings)
        await interaction.response.send_message(f"✅ `{word}` has been removed from the list.", ephemeral=True)

    @app_commands.command(name="listbadwords", description="Show all current bad words")
    async def listbadwords(self, interaction: discord.Interaction):
        words = self.settings.get("words", [])
        if not words:
            await interaction.response.send_message("🚫 No bad words set yet.", ephemeral=True)
            return

        word_list = ", ".join(f"`{w}`" for w in words)
        embed = discord.Embed(
            title="🧨 Bad Words List",
            description=word_list,
            color=0xe74c3c
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="ignorebadwordchannel", description="Ignore a channel from bad word filter")
    async def ignorebadwordchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        ch_id = str(channel.id)
        if ch_id in self.settings["ignored_channels"]:
            await interaction.response.send_message("⚠️ This channel is already ignored.", ephemeral=True)
            return

        self.settings["ignored_channels"].append(ch_id)
        save_settings(self.settings)
        await interaction.response.send_message(f"✅ Filter disabled in {channel.mention}", ephemeral=True)

    @app_commands.command(name="unignorebadwordchannel", description="Re-enable filter in an ignored channel")
    async def unignorebadwordchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        ch_id = str(channel.id)
        if ch_id not in self.settings["ignored_channels"]:
            await interaction.response.send_message("⚠️ This channel is not ignored.", ephemeral=True)
            return

        self.settings["ignored_channels"].remove(ch_id)
        save_settings(self.settings)
        await interaction.response.send_message(f"✅ Filter re-enabled in {channel.mention}", ephemeral=True)

    @app_commands.command(name="badwordstatus", description="Show current bad word filter settings")
    async def badwordstatus(self, interaction: discord.Interaction):
        words = self.settings.get("words", [])
        ignored_channels = self.settings.get("ignored_channels", [])

        embed = discord.Embed(title="🛡️ Bad Word Filter Status", color=0x3498db)
        embed.add_field(name="Total Words", value=str(len(words)), inline=True)
        embed.add_field(name="Ignored Channels", value=str(len(ignored_channels)), inline=True)

        if ignored_channels:
            ch_list = "\n".join(f"<#{cid}>" for cid in ignored_channels)
            embed.add_field(name="Ignored Channels List", value=ch_list, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(BadWordFilter(bot))
