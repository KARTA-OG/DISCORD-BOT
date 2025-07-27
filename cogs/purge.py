import discord
from discord.ext import commands
from discord import app_commands

class Purge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="purge", description="Delete messages in this channel (1–50)")
    @app_commands.describe(amount="Number of messages to delete (1–50)")
    async def purge(self, interaction: discord.Interaction, amount: app_commands.Range[int, 1, 50]):
        # Check user permissions manually
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message(
                "❌ You need `Manage Messages` permission to use this command.",
                ephemeral=True
            )

        # Check bot permissions
        if not interaction.channel.permissions_for(interaction.guild.me).manage_messages:
            return await interaction.response.send_message(
                "❌ I don't have permission to manage messages in this channel.",
                ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        try:
            deleted = await interaction.channel.purge(limit=amount)
            await interaction.followup.send(f"🧹 Deleted {len(deleted)} messages.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(
                f"⚠️ Failed to delete messages. Error: `{e}`", ephemeral=True
            )

    # Optional: Handle errors globally for this cog
    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(
                "❌ You are missing required permissions to use this command.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "⚠️ An unexpected error occurred while executing the command.",
                ephemeral=True
            )
            # Optional: log the error
            print(f"Error in /purge: {error}")

async def setup(bot):
    await bot.add_cog(Purge(bot))
