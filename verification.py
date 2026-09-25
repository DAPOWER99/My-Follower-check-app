import discord
import logging
import datetime
from config import Config
from database import DiscordDatabase
from github import GitHubAPI

logger = logging.getLogger("bot.verification")

class VerificationManager:
    def __init__(self, bot: discord.Client, db: DiscordDatabase, gh: GitHubAPI):
        self.bot = bot
        self.db = db
        self.gh = gh

    async def verify_user(self, member: discord.Member, github_username: str, github_id: int, method: str) -> str:
        # Check if github account already used by someone else
        existing = await self.db.get_by_github_id(github_id)
        if existing and str(existing["discord_id"]) != str(member.id):
            return "❌ This GitHub account is already linked to another Discord user."

        # Check follow status
        follow_data = await self.gh.check_follows(github_username)
        
        if "error" in follow_data:
            err = follow_data["error"]
            if err == "rate_limited":
                return "⏳ GitHub API is currently rate limited. Please try again later."
            else:
                return f"⚠️ An error occurred while checking GitHub status: {err}"
                
        follows = follow_data.get("follows", False)
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        record = await self.db.get_by_discord_id(member.id)
        if not record:
            record = {
                "discord_id": str(member.id),
                "github_id": github_id,
                "github_username": github_username,
                "verified": follows,
                "role_given": False,
                "created_at": now_str,
                "last_verified_at": now_str,
                "verification_method": method
            }
        else:
            record["github_id"] = github_id
            record["github_username"] = github_username
            record["verified"] = follows
            record["last_verified_at"] = now_str
            record["verification_method"] = method
            
        guild = self.bot.get_guild(Config.GUILD_ID)
        role = guild.get_role(Config.VERIFIED_ROLE_ID) if guild else None
        
        if follows:
            if role:
                try:
                    await member.add_roles(role, reason="GitHub Verification Passed")
                    record["role_given"] = True
                except discord.Forbidden:
                    logger.error(f"Missing permissions to add role to {member.id}.")
                except Exception as e:
                    logger.error(f"Failed to give role to {member.id}: {e}")
            else:
                logger.error(f"Verified role {Config.VERIFIED_ROLE_ID} not found.")
                
            await self.db.update(record)
            return f"✅ Verification successful! You are following **{Config.GITHUB_TARGET_USERNAME}**."
        else:
            if role and role in member.roles:
                try:
                    await member.remove_roles(role, reason="GitHub Verification Failed")
                    record["role_given"] = False
                except discord.Forbidden:
                    logger.error(f"Missing permissions to remove role from {member.id}.")
                except Exception as e:
                    logger.error(f"Failed to remove role from {member.id}: {e}")
            
            await self.db.update(record)
            return f"❌ Verification failed. You are not following **{Config.GITHUB_TARGET_USERNAME}**."

    async def process_unfollow(self, record: dict):
        discord_id = int(record["discord_id"])
        guild = self.bot.get_guild(Config.GUILD_ID)
        if not guild:
            return
            
        member = guild.get_member(discord_id)
        
        record["verified"] = False
        record["role_given"] = False
        record["last_verified_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        if member:
            role = guild.get_role(Config.VERIFIED_ROLE_ID)
            if role and role in member.roles:
                try:
                    await member.remove_roles(role, reason="No longer following target GitHub account")
                except Exception as e:
                    logger.error(f"Failed to remove role: {e}")
        
        await self.db.update(record)
        
        # DM user if they are still in the server
        if member:
            try:
                embed = discord.Embed(
                    title="⚠️ GitHub Verification Failed",
                    description=(
                        f"We checked your GitHub account and it is no longer following **@{Config.GITHUB_TARGET_USERNAME}**.\n\n"
                        "Your verified Discord role has been removed.\n\n"
                        "To restore your verification:\n"
                        f"1. Follow @{Config.GITHUB_TARGET_USERNAME} on GitHub.\n"
                        "2. Return to the Discord server.\n"
                        "3. Open the verification panel and verify again."
                    ),
                    color=discord.Color.red()
                )
                await member.send(embed=embed)
            except Exception:
                logger.warning(f"Could not DM user {discord_id} about unfollow.")
