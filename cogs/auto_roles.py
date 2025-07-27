import discord
from discord.ext import commands
from discord import app_commands
import os
import json

from utils.logger import log_action

SETTINGS_PATH = "data/settings/autorole.json"

def load_config():
    if not os.path.exists(SETTINGS_PATH):
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        with open(SETTINGS_PATH, "w") as f:
            json.dump({}, f)
    with open(SETTINGS_PATH, "r") as f:
        return json.load(f)

def save_config(data):
    with open(SETTINGS_PATH, "w") as f:
        json.dump(data, f, indent=4)

class AutoRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()

    @app_commands.command(name="setautoroles", description="Set 3 roles to automatically assign to new members")
    @app_commands.checks.has_permissions(administrator=True)
    async def setautoroles(
        self,
        interaction: discord.Interaction,
        role1: discord.Role,
        role2: discord.Role,
        role3: discord.Role
    ):
        guild_id = str(interaction.guild.id)
        self.config[guild_id] = [role1.id, role2.id, role3.id]
        save_config(self.config)

        await interaction.response.send_message(
            f"✅ Auto-role setup complete! New users will receive: {role1.mention}, {role2.mention}, {role3.mention}",
            ephemeral=True
        )

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild_id = str(member.guild.id)
        role_ids = self.config.get(guild_id, [])

        if not role_ids:
            return

        roles = [member.guild.get_role(rid) for rid in role_ids]
        roles = [r for r in roles if r is not None]

        if not roles:
            return

        try:
            await member.add_roles(*roles, reason="Auto role on join")
        except discord.Forbidden:
            print(f"❌ Missing permission to add roles to {member.display_name}")
            return
        except Exception as e:
            print(f"❌ Failed to add auto-roles to {member.display_name}: {e}")
            return

        # 🔁 Log the auto-role assignment
        try:
            await log_action(
                self.bot,
                member.guild,
                title="👥 Auto Role Assigned",
                content=f"{member.mention} joined and was automatically given roles: " +
                        ", ".join(r.mention for r in roles),
                user=member
            )
        except Exception as e:
            print(f"⚠️ Failed to log auto-role for {member.name}: {e}")

async def setup(bot):
    await bot.add_cog(AutoRoles(bot))
