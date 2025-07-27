import discord
from discord.ext import commands
from discord import app_commands

class Purge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="purge", description="Delete messages in this channel (1–50)")
    @app_commands.describe(amount="Number of messages to delete (1–50)")
    async def purge(self, interaction: discord.Interaction, amount: app_commands.Range[int, 1, 50]):
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message(
                "❌ You need `Manage Messages` permission to use this command.",
                ephemeral=True
            )

        if not interaction.channel.permissions_for(interaction.guild.me).manage_messages:
            return await interaction.response.send_message(
                "❌ I don't have permission to manage messages here.",
                ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        try:
            deleted = await interaction.channel.purge(limit=amount)
            await interaction.followup.send(f"🧹 Deleted {len(deleted)} messages.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"⚠️ Failed to delete messages.\nError: `{e}`", ephemeral=True)

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        try:
            await interaction.response.send_message("⚠️ An error occurred.", ephemeral=True)
        except discord.InteractionResponded:
            await interaction.followup.send("⚠️ An error occurred after response.", ephemeral=True)
        print(f"[PURGE ERROR] {error}")

async def setup(bot):
    await bot.add_cog(Purge(bot))
