import discord
from discord.ext import commands
from discord import app_commands
import json
import os

VCROLE_PATH = "data/settings/vcrole.json"

class VCRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Ensure storage exists
        os.makedirs("data/settings", exist_ok=True)
        if not os.path.exists(VCROLE_PATH):
            with open(VCROLE_PATH, "w") as f:
                json.dump({}, f)

    @app_commands.command(name="setvcrole", description="Set a role to be given when users join VC created by bot")
    @app_commands.describe(role="Select the role to assign when user joins VC")
    async def setvcrole(self, interaction: discord.Interaction, role: discord.Role):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("🚫 You must be an admin to use this command.", ephemeral=True)
            return

        # Save role
        with open(VCROLE_PATH, "r") as f:
            data = json.load(f)
        data[str(interaction.guild.id)] = role.id
        with open(VCROLE_PATH, "w") as f:
            json.dump(data, f, indent=4)

        await interaction.response.send_message(f"✅ VC role set to {role.mention}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(VCRole(bot))
