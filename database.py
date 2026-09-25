import json
import logging
import discord
from typing import Optional, List

logger = logging.getLogger("bot.database")

class DiscordDatabase:
    def __init__(self, bot: discord.Client, channel_id: int):
        self.bot = bot
        self.channel_id = channel_id
        self.channel = None
        self._cache_by_discord = {}
        self._cache_by_github = {}
        self._message_map = {} # discord_id -> message object

    async def initialize(self):
        self.channel = self.bot.get_channel(self.channel_id)
        if not self.channel:
            try:
                self.channel = await self.bot.fetch_channel(self.channel_id)
            except discord.NotFound:
                logger.error(f"Database channel {self.channel_id} not found!")
                return
            except discord.Forbidden:
                logger.error(f"Bot lacks permissions to access database channel {self.channel_id}!")
                return
                
        logger.info(f"Initializing database from channel {self.channel_id}...")
        
        # Load all history
        count = 0
        async for msg in self.channel.history(limit=None, oldest_first=True):
            if msg.author.id != self.bot.user.id:
                continue
            
            try:
                content = msg.content
                if content.startswith("```json"):
                    content = content[7:-3].strip()
                
                record = json.loads(content)
                if record.get("_type") != "github_verification_record":
                    continue
                    
                discord_id = str(record["discord_id"])
                github_id = record["github_id"]
                
                self._cache_by_discord[discord_id] = record
                self._cache_by_github[github_id] = record
                self._message_map[discord_id] = msg
                count += 1
            except (json.JSONDecodeError, KeyError):
                pass
                
        logger.info(f"Loaded {count} records from database.")

    def _format_message(self, record: dict) -> str:
        record["_type"] = "github_verification_record"
        return f"```json\n{json.dumps(record, indent=2)}\n```"

    async def get_by_discord_id(self, discord_id: int) -> Optional[dict]:
        return self._cache_by_discord.get(str(discord_id))

    async def get_by_github_id(self, github_id: int) -> Optional[dict]:
        return self._cache_by_github.get(github_id)
        
    def get_all_records(self) -> List[dict]:
        return list(self._cache_by_discord.values())

    async def create(self, record: dict) -> bool:
        if not self.channel:
            return False
            
        discord_id = str(record["discord_id"])
        github_id = record["github_id"]
        
        msg_content = self._format_message(record)
        try:
            msg = await self.channel.send(content=msg_content)
            self._cache_by_discord[discord_id] = record
            self._cache_by_github[github_id] = record
            self._message_map[discord_id] = msg
            return True
        except Exception as e:
            logger.error(f"Failed to create record: {e}")
            return False

    async def update(self, record: dict) -> bool:
        if not self.channel:
            return False
            
        discord_id = str(record["discord_id"])
        
        if discord_id not in self._message_map:
            logger.warning(f"Message for {discord_id} not found, recreating.")
            return await self.create(record)
            
        msg = self._message_map[discord_id]
        msg_content = self._format_message(record)
        
        try:
            await msg.edit(content=msg_content)
            self._cache_by_discord[discord_id] = record
            github_id = record["github_id"]
            self._cache_by_github[github_id] = record
            return True
        except discord.NotFound:
            logger.warning(f"Message for {discord_id} deleted, recreating.")
            return await self.create(record)
        except Exception as e:
            logger.error(f"Failed to update record: {e}")
            return False

    async def delete(self, discord_id: int) -> bool:
        discord_id = str(discord_id)
        if discord_id not in self._message_map:
            return False
            
        msg = self._message_map[discord_id]
        record = self._cache_by_discord.get(discord_id)
        
        try:
            await msg.delete()
        except discord.NotFound:
            pass
        except Exception as e:
            logger.error(f"Failed to delete message: {e}")
            return False
            
        if record:
            github_id = record.get("github_id")
            if github_id in self._cache_by_github:
                del self._cache_by_github[github_id]
            del self._cache_by_discord[discord_id]
            
        del self._message_map[discord_id]
        return True
