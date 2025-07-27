import discord
from discord.ext import commands
from discord import app_commands
import os
import json
import asyncio

from utils.logger import log_action

VERIFY_CONFIG_PATH = "data/settings/verify.json"

def load_config():
    if not os.path.exists(VERIFY_CONFIG_PATH):
        os.makedirs(os.path.dirname(VERIFY_CONFIG_PATH), exist_ok=True)
        with open(VERIFY_CONFIG_PATH, "w") as f:
            json.dump({}, f)
    with open(VERIFY_CONFIG_PATH, "r") as f:
        return json.load(f)

def save_config(data):
    with open(VERIFY_CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=4)

class VerifyButton(discord.ui.View):
    def __init__(self, role_id: int):
        super().__init__(timeout=None)
        self.role_id = role_id

    @discord.ui.button(label="✅ Verify", style=discord.ButtonStyle.success, custom_id="verify_button")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = load_config()
        guild_id = str(interaction.guild.id)

        role_id = config.get(guild_id)
        if not role_id:
            await interaction.response.send_message("⚠️ Verification role not configured.", ephemeral=True)
            return

        role = interaction.guild.get_role(role_id)
        if not role:
            await interaction.response.send_message("⚠️ Verification role not found.", ephemeral=True)
            return

        if role in interaction.user.roles:
            await interaction.response.send_message("✅ You are already verified!", ephemeral=True)
        else:
            await interaction.response.defer(ephemeral=True)  # Prevent crash
            try:
                await interaction.user.add_roles(role)

                # ✅ Send public confirmation and auto-delete it
                msg = await interaction.channel.send(f"{interaction.user.mention} 🎉 You are now verified!")
                await log_action(
                    interaction.client,
                    interaction.guild,
                    title="✅ Member Verified",
                    content=f"{interaction.user.mention} has been verified and given {role.mention}.",
                    user=interaction.user
                )
                await asyncio.sleep(5)
                await msg.delete()
            except discord.Forbidden:
                await interaction.followup.send("❌ I don't have permission to give roles.", ephemeral=True)

class VerifySystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()

    @app_commands.command(name="setverifyrole", description="Set the role to assign when a user verifies")
    @app_commands.checks.has_permissions(administrator=True)
    async def setverifyrole(self, interaction: discord.Interaction, role: discord.Role):
        guild_id = str(interaction.guild.id)
        self.config[guild_id] = role.id
        save_config(self.config)
        await interaction.response.send_message(f"✅ Verification role set to {role.mention}", ephemeral=True)

    @app_commands.command(name="setupverify", description="Send a verify button in this channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def setupverify(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        role_id = self.config.get(guild_id)
        if not role_id:
            await interaction.response.send_message("⚠️ You must set a verify role first using `/setverifyrole`.", ephemeral=True)
            return

        embed = discord.Embed(
            title="🔐 Verify Yourself",
            description="Click the button below to verify and get access to the server.",
            color=0x2ecc71
        )
        view = VerifyButton(role_id=role_id)
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Verification panel sent.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(VerifySystem(bot))
