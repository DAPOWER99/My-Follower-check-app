import asyncio
import logging
from discord.ext import tasks
from verification import VerificationManager
from database import DiscordDatabase
from github import GitHubAPI

logger = logging.getLogger("bot.tasks")

class VerificationTasks:
    def __init__(self, db: DiscordDatabase, gh: GitHubAPI, verify_mgr: VerificationManager):
        self.db = db
        self.gh = gh
        self.verify_mgr = verify_mgr

    @tasks.loop(hours=48)
    async def recheck_all_users(self):
        logger.info("Starting scheduled recheck of all verified users...")
        records = self.db.get_all_records()
        verified_records = [r for r in records if r.get("verified")]
        
        for record in verified_records:
            username = record["github_username"]
            follow_data = await self.gh.check_follows(username)
            
            if "error" in follow_data:
                err = follow_data["error"]
                logger.warning(f"Error checking {username}: {err}. Skipping.")
                continue # don't remove roles on api error
                
            follows = follow_data.get("follows", False)
            if not follows:
                logger.info(f"User {username} no longer follows target. Removing verification.")
                await self.verify_mgr.process_unfollow(record)
            else:
                import datetime
                record["last_verified_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                await self.db.update(record)
                
            await asyncio.sleep(1) # prevent hitting rate limits
            
        logger.info("Finished scheduled recheck.")

    @recheck_all_users.before_loop
    async def before_recheck(self):
        # Wait for bot to be fully ready before starting
        await asyncio.sleep(60)
