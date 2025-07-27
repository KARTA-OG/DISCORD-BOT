import discord
from discord.ext import commands
from discord import app_commands

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Show all available bot commands")
    async def help(self, interaction: discord.Interaction):
        try:
            embed = discord.Embed(
                title="🛠️ VERSA Bot Help Menu",
                description="Here are the available commands and features:",
                color=discord.Color.blurple()
            )

            embed.add_field(
                name="🛡️ Moderation",
                value=(
                    "`/warn`, `/setwarnlog`, `/setspamfilter`, `/spamstatus`, `/ignorespamchannel`, `/unignorespamchannel`, `/setspamalertrole`\n"
                    "`/addbadword`, `/removebadword`, `/badwordstatus`, `/setlinkfilter`, `/addlinkwhitelist`, `/removelinkwhitelist`, `/purge`"
                ),
                inline=False
            )

            embed.add_field(
                name="✅ Verification",
                value="`/setverifyrole`, `/setupverify`",
                inline=False
            )

            embed.add_field(
                name="🎟️ Tickets",
                value="`/setticket`, `/resolveticket`",
                inline=False
            )

            embed.add_field(
                name="🖼️ Sticky Media Channels",
                value="`/enablesticky`, `/disablesticky`",
                inline=False
            )

            embed.add_field(
                name="🧵 Auto Threads",
                value="`/enableautothread`, `/disableautothread`",
                inline=False
            )

            embed.add_field(
                name="🔊 Private Voice Channels",
                value="`/vcbutton`, `/setvcrole`",
                inline=False
            )

            embed.add_field(
                name="🎭 Auto Roles",
                value="`/addautorole`, `/removeautorole`, `/listautoroles`",
                inline=False
            )

            embed.add_field(
                name="📋 Logging & Utility",
                value="`/setlogchannel`, `/status`, `/reload`, `/help`",
                inline=False
            )

            embed.set_footer(text="Use each command directly in a slash command menu for more details.")
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            print(f"❌ Error in /help command: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ An error occurred while displaying help.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(HelpCommand(bot))
