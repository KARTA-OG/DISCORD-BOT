import discord
from discord.ext import commands
from discord import app_commands

class Purge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="purge", description="Delete a number of recent messages")
    @app_commands.describe(amount="Number of messages to delete (2–100)")
    async def purge(self, interaction: discord.Interaction, amount: int):
        # Check permissions
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message(
                "❌ You need `Manage Messages` permission to use this command.",
                ephemeral=True
            )

        # Validate amount
        if amount < 2 or amount > 100:
            return await interaction.response.send_message(
                "⚠️ You can only delete between 2 and 100 messages.",
                ephemeral=True
            )

        # Defer response (for long tasks)
        await interaction.response.defer(ephemeral=True)

        # Delete messages
        deleted = await interaction.channel.purge(limit=amount)

        # Confirm deletion
        await interaction.followup.send(
            f"🧹 Deleted {len(deleted)} messages in {interaction.channel.mention}.",
            ephemeral=True
        )

    # Optional: Error handler
    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        await interaction.response.send_message("⚠️ An unexpected error occurred in `/purge`.", ephemeral=True)
        print(f"[Purge Error] {error}")

async def setup(bot):
    await bot.add_cog(Purge(bot))
