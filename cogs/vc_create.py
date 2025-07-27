import discord
from discord.ext import commands
from discord import app_commands
from cogs.vc_logic import create_voice_channel  # ✅ Make sure this exists and works

# 🔹 VC Setup View (Dropdown + Button)
class VCSetupView(discord.ui.View):
    def __init__(self, bot: commands.Bot, user: discord.User):
        super().__init__(timeout=60)
        self.bot = bot
        self.user = user
        self.selected_type = None
        self.selected_limit = None
        self.add_item(VCTypeSelect(self))
        self.add_item(VCLimitSelect(self))
        self.add_item(ConfirmVCButton(self))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("🚫 This interaction isn’t for you.", ephemeral=True)
            return False
        return True

# 🔹 Dropdown for VC Type
class VCTypeSelect(discord.ui.Select):
    def __init__(self, parent: VCSetupView):
        self.parent = parent
        options = [
            discord.SelectOption(label="Public", value="public"),
            discord.SelectOption(label="Private", value="private")
        ]
        super().__init__(placeholder="Select VC Type", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        self.parent.selected_type = self.values[0]
        await interaction.response.send_message(f"✅ VC Type set to `{self.values[0]}`", ephemeral=True)

# 🔹 Dropdown for VC Member Limit
class VCLimitSelect(discord.ui.Select):
    def __init__(self, parent: VCSetupView):
        self.parent = parent
        options = [discord.SelectOption(label=str(i), value=str(i)) for i in range(1, 16)]
        super().__init__(placeholder="Select VC Member Limit", options=options, row=1)

    async def callback(self, interaction: discord.Interaction):
        self.parent.selected_limit = int(self.values[0])
        await interaction.response.send_message(f"✅ Member limit set to `{self.values[0]}`", ephemeral=True)

# 🔹 Confirm Button
class ConfirmVCButton(discord.ui.Button):
    def __init__(self, parent: VCSetupView):
        super().__init__(label="✅ Confirm & Create VC", style=discord.ButtonStyle.green, row=2)
        self.parent = parent

    async def callback(self, interaction: discord.Interaction):
        vc_type = self.parent.selected_type
        user_limit = self.parent.selected_limit

        if not vc_type or not user_limit:
            await interaction.response.send_message(
                "⚠️ Please select both VC type and limit before confirming.",
                ephemeral=True
            )
            return

        # 🛠 Prevent interaction crash — use defer + followup
        await interaction.response.defer(ephemeral=True)

        await create_voice_channel(
            bot=self.parent.bot,
            guild=interaction.guild,
            user=interaction.user,
            channel=interaction.channel,
            category=interaction.channel.category,
            vc_type=vc_type,
            user_limit=user_limit
        )

        await interaction.followup.send(
            f"🎧 Created your `{vc_type}` VC with limit {user_limit}!"
        )

        self.parent.stop()

# 🔹 VC Button (sent by slash command)
class VCButton(discord.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="🎧 Create VC", style=discord.ButtonStyle.blurple, custom_id="create_vc_btn")
    async def create_vc_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "🔽 Please choose your VC type and member limit:",
            view=VCSetupView(bot=self.bot, user=interaction.user),
            ephemeral=True
        )

# 🔹 Persistent View for Startup (used in main.py)
class VCButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(PersistentVCButton())

# 🔹 Persistent Button (auto-working after bot restart)
class PersistentVCButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🎧 Create VC", style=discord.ButtonStyle.blurple, custom_id="create_vc_btn")

    async def callback(self, interaction: discord.Interaction):
        bot = interaction.client
        await interaction.response.send_message(
            "🔽 Please choose your VC type and member limit:",
            view=VCSetupView(bot=bot, user=interaction.user),
            ephemeral=True
        )

# 🔹 Slash Command to send the button
class VCCreator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="addvcbutton", description="Add a voice channel creation button in this channel")
    async def addvcbutton(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "🎧 Press the button below to create your own voice channel:",
            view=VCButton(bot=self.bot)
        )

async def setup(bot):
    await bot.add_cog(VCCreator(bot))
