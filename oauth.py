import secrets
import httpx
import logging
from config import Config
from typing import Optional, Dict
import time

logger = logging.getLogger("bot.oauth")

# In-memory storage for oauth states (discord_id -> state)
_oauth_states: Dict[int, dict] = {}

class OAuthManager:
    @staticmethod
    def generate_state(discord_id: int) -> str:
        state = secrets.token_urlsafe(32)
        _oauth_states[discord_id] = {
            "state": state,
            "expires": time.time() + 600 # 10 mins
        }
        return state
        
    @staticmethod
    def verify_state(state: str) -> Optional[int]:
        current_time = time.time()
        for discord_id, data in list(_oauth_states.items()):
            if data["expires"] < current_time:
                del _oauth_states[discord_id]
                continue
            if data["state"] == state:
                del _oauth_states[discord_id]
                return discord_id
        return None

    @staticmethod
    async def exchange_code(code: str) -> Optional[str]:
        async with httpx.AsyncClient() as client:
            try:
                data = {
                    "client_id": Config.GITHUB_CLIENT_ID,
                    "client_secret": Config.GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": Config.GITHUB_REDIRECT_URI
                }
                headers = {"Accept": "application/json"}
                resp = await client.post("https://github.com/login/oauth/access_token", data=data, headers=headers)
                if resp.status_code == 200:
                    resp_data = resp.json()
                    return resp_data.get("access_token")
                return None
            except Exception as e:
                logger.error(f"Error exchanging OAuth code: {e}")
                return None
