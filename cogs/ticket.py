
import discord
from discord.ext import commands
from discord import app_commands
import json
import os

TICKET_CONFIG_PATH = "data/settings/ticket.json"

def load_config():
    if os.path.exists(TICKET_CONFIG_PATH):
        with open(TICKET_CONFIG_PATH, "r") as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(TICKET_CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)

class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="sethelprole", description="Set the Help role used for tickets")
    @app_commands.describe(role="The role to assign when user clicks help button")
    @app_commands.checks.has_permissions(administrator=True)
    async def sethelprole(self, interaction: discord.Interaction, role: discord.Role):
        config = load_config()
        gid = str(interaction.guild.id)
        config.setdefault(gid, {})["help_role"] = role.id
        save_config(config)
        await interaction.response.send_message(f"✅ Help role set to: {role.mention}", ephemeral=True)

    @app_commands.command(name="setticket", description="Post help button in this channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def setticket(self, interaction: discord.Interaction):
        config = load_config()
        gid = str(interaction.guild.id)
        config.setdefault(gid, {})["ticket_channel"] = interaction.channel.id
        save_config(config)
        view = TicketButton()
        await interaction.response.send_message("✅ Help button set! Members can now request help below:", view=view)

    @app_commands.command(name="resolveticket", description="Resolve a member's ticket (remove help role)")
    @app_commands.describe(member="The member to remove the help role from")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def resolveticket(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer(ephemeral=True)

        config = load_config()
        gid = str(interaction.guild.id)
        role_id = config.get(gid, {}).get("help_role")

        if not role_id:
            await interaction.followup.send("❌ Help role not set. Use `/sethelprole` first.")
            return

        help_role = interaction.guild.get_role(role_id)
        if not help_role:
            await interaction.followup.send("❌ Help role not found. Maybe it was deleted?")
            return

        if help_role in member.roles:
            await member.remove_roles(help_role, reason="Ticket resolved")
            try:
                await member.send(f"🎫 Your ticket in **{interaction.guild.name}** has been resolved. The help role was removed.")
            except discord.Forbidden:
                await interaction.followup.send(f"⚠️ Couldn't DM {member.mention}. They may have DMs off.")

            await interaction.followup.send(f"✅ Removed help role from {member.mention}")
        else:
            await interaction.followup.send(f"ℹ️ {member.mention} does not have the help role.")

class TicketButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎟️ Get Help", style=discord.ButtonStyle.primary, custom_id="get_help_button")
    async def get_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        config = load_config()
        gid = str(interaction.guild.id)
        role_id = config.get(gid, {}).get("help_role")

        if not role_id:
            await interaction.followup.send("❌ Help role not set. Please contact an admin.")
            return

        help_role = interaction.guild.get_role(role_id)
        if not help_role:
            await interaction.followup.send("❌ Help role not found. Please contact staff.")
            return

        if help_role in interaction.user.roles:
            await interaction.followup.send("⚠️ You already have the help role.")
            return

        try:
            await interaction.user.add_roles(help_role, reason="Requested help")
            try:
                await interaction.user.send("✅ Help role granted! Please check the help channel.")
            except discord.Forbidden:
                await interaction.followup.send("⚠️ Help role granted, but I couldn't DM you. Please check your DM settings.", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("❌ I couldn't assign the help role. Please contact staff.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Ticket(bot))
