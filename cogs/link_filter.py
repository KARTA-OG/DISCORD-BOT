import discord
from discord.ext import commands
from discord import app_commands
import re
import os
import json

from utils.logger import log_action  # ✅ Import logger

LINK_REGEX = re.compile(r"https?://\S+")

SETTINGS_PATH = "data/settings/linkfilter.json"

def load_settings():
    if not os.path.exists(SETTINGS_PATH):
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        with open(SETTINGS_PATH, "w") as f:
            json.dump({}, f)
    with open(SETTINGS_PATH, "r") as f:
        return json.load(f)

def save_settings(settings):
    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=4)

class LinkFilter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings = load_settings()

    def reload_settings(self):
        self.settings = load_settings()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        channel_id = str(message.channel.id)
        if channel_id not in self.settings:
            return

        config = self.settings[channel_id]
        if not config.get("enabled", False):
            return

        whitelisted_roles = config.get("roles", [])
        if any(str(role.id) in whitelisted_roles for role in message.author.roles):
            return

        whitelisted = config.get("whitelist", [])
        found_links = LINK_REGEX.findall(message.content.lower())

        for link in found_links:
            if any(domain.lower() in link for domain in whitelisted):
                continue

            try:
                await message.delete()
                await message.channel.send(
                    f"🚫 {message.author.mention}, links are not allowed in this channel.",
                    delete_after=5
                )

                try:
                    await log_action(
                        self.bot,
                        message.guild,
                        title="🔗 Link Blocked",
                        content=(
                            f"**User:** {message.author.mention} (`{message.author.id}`)\n"
                            f"**Channel:** {message.channel.mention}\n"
                            f"**Message:** `{link}`"
                        ),
                        user=message.author
                    )
                except Exception as e:
                    print(f"⚠️ Logging failed (link blocked): {e}")
                return

            except discord.Forbidden:
                pass

    @app_commands.command(name="setlinkfilter", description="Enable or disable link filtering in this channel")
    @app_commands.describe(enabled="Enable or disable link filtering in this channel")
    async def setlinkfilter(self, interaction: discord.Interaction, enabled: bool):
        channel_id = str(interaction.channel_id)
        self.settings.setdefault(channel_id, {"enabled": False, "whitelist": [], "roles": []})
        self.settings[channel_id]["enabled"] = enabled
        save_settings(self.settings)

        status = "enabled ✅" if enabled else "disabled ❌"
        await interaction.response.send_message(
            f"🔒 Link filter has been {status} in this channel.", ephemeral=True
        )

        try:
            await log_action(
                self.bot,
                interaction.guild,
                title="🔧 Link Filter Toggled",
                content=f"**{interaction.user.mention}** set link filter to `{enabled}` in {interaction.channel.mention}",
                user=interaction.user
            )
        except Exception as e:
            print(f"⚠️ Logging failed (toggle filter): {e}")

    @app_commands.command(name="addlinkwhitelist", description="Allow a specific domain (like youtube.com) in this channel")
    async def addlinkwhitelist(self, interaction: discord.Interaction, domain: str):
        channel_id = str(interaction.channel_id)
        self.settings.setdefault(channel_id, {"enabled": False, "whitelist": [], "roles": []})
        domain = domain.lower()

        if domain in self.settings[channel_id]["whitelist"]:
            await interaction.response.send_message("⚠️ This domain is already allowed.", ephemeral=True)
            return

        self.settings[channel_id]["whitelist"].append(domain)
        save_settings(self.settings)
        await interaction.response.send_message(f"✅ `{domain}` has been whitelisted for this channel.", ephemeral=True)

        try:
            await log_action(
                self.bot,
                interaction.guild,
                title="➕ Domain Whitelisted",
                content=f"`{domain}` allowed by {interaction.user.mention} in {interaction.channel.mention}",
                user=interaction.user
            )
        except Exception as e:
            print(f"⚠️ Logging failed (add domain): {e}")

    @app_commands.command(name="removelinkwhitelist", description="Remove a whitelisted domain from this channel")
    async def removelinkwhitelist(self, interaction: discord.Interaction, domain: str):
        channel_id = str(interaction.channel_id)
        domain = domain.lower()

        if channel_id not in self.settings or domain not in self.settings[channel_id].get("whitelist", []):
            await interaction.response.send_message("⚠️ That domain is not whitelisted.", ephemeral=True)
            return

        self.settings[channel_id]["whitelist"].remove(domain)
        save_settings(self.settings)
        await interaction.response.send_message(f"✅ `{domain}` removed from whitelist.", ephemeral=True)

        try:
            await log_action(
                self.bot,
                interaction.guild,
                title="➖ Domain Removed from Whitelist",
                content=f"`{domain}` removed by {interaction.user.mention} in {interaction.channel.mention}",
                user=interaction.user
            )
        except Exception as e:
            print(f"⚠️ Logging failed (remove domain): {e}")

    @app_commands.command(name="addlinkwhitelistrole", description="Allow members with this role to bypass link filter in this channel")
    async def addlinkwhitelistrole(self, interaction: discord.Interaction, role: discord.Role):
        channel_id = str(interaction.channel_id)
        self.settings.setdefault(channel_id, {"enabled": False, "whitelist": [], "roles": []})

        if str(role.id) in self.settings[channel_id]["roles"]:
            await interaction.response.send_message("⚠️ This role is already whitelisted.", ephemeral=True)
            return

        self.settings[channel_id]["roles"].append(str(role.id))
        save_settings(self.settings)
        await interaction.response.send_message(f"✅ Role {role.mention} is now allowed to post links.", ephemeral=True)

    @app_commands.command(name="removelinkwhitelistrole", description="Remove a role from link whitelist in this channel")
    async def removelinkwhitelistrole(self, interaction: discord.Interaction, role: discord.Role):
        channel_id = str(interaction.channel_id)
        if str(role.id) not in self.settings.get(channel_id, {}).get("roles", []):
            await interaction.response.send_message("⚠️ This role is not in whitelist.", ephemeral=True)
            return

        self.settings[channel_id]["roles"].remove(str(role.id))
        save_settings(self.settings)
        await interaction.response.send_message(f"✅ Role {role.mention} removed from whitelist.", ephemeral=True)

    @app_commands.command(name="listlinkwhitelist", description="Show link filtering status and allowed domains for this channel")
    async def listlinkwhitelist(self, interaction: discord.Interaction):
        channel_id = str(interaction.channel_id)
        config = self.settings.get(channel_id, {"enabled": False, "whitelist": [], "roles": []})
        enabled = config["enabled"]
        whitelist = config["whitelist"]
        role_ids = config["roles"]

        description = f"🔒 **Link Filter:** {'Enabled ✅' if enabled else 'Disabled ❌'}\n"
        if whitelist:
            description += "\n**Allowed Domains:**\n" + "\n".join(f"• `{d}`" for d in whitelist)
        else:
            description += "\n*No domains are currently allowed.*"

        if role_ids:
            roles = [f"<@&{rid}>" for rid in role_ids]
            description += f"\n\n**Whitelisted Roles:**\n" + "\n".join(roles)

        embed = discord.Embed(title="📁 Link Filter Settings", description=description, color=0x00b0f4)
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(LinkFilter(bot))
