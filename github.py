import httpx
import logging
from config import Config

logger = logging.getLogger("bot.github")

class GitHubAPI:
    def __init__(self):
        self.target_username = Config.GITHUB_TARGET_USERNAME
        
    async def get_user_by_username(self, username: str) -> dict:
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"https://api.github.com/users/{username}")
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 404:
                    return {"error": "not_found"}
                elif resp.status_code == 403:
                    return {"error": "rate_limited"}
                else:
                    return {"error": "api_error", "status": resp.status_code}
            except Exception as e:
                logger.error(f"Network error fetching user {username}: {e}")
                return {"error": "network_error"}

    async def get_user_by_token(self, token: str) -> dict:
        async with httpx.AsyncClient() as client:
            try:
                headers = {"Authorization": f"Bearer {token}"}
                resp = await client.get("https://api.github.com/user", headers=headers)
                if resp.status_code == 200:
                    return resp.json()
                else:
                    return {"error": "api_error", "status": resp.status_code}
            except Exception as e:
                logger.error(f"Network error fetching auth user: {e}")
                return {"error": "network_error"}

    async def check_follows(self, username: str) -> dict:
        if username.lower() == self.target_username.lower():
            # If the user is the target themselves, consider them as "following"
            return {"follows": True}
            
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"https://api.github.com/users/{username}/following/{self.target_username}")
                if resp.status_code == 204:
                    return {"follows": True}
                elif resp.status_code == 404:
                    return {"follows": False}
                elif resp.status_code == 403:
                    return {"error": "rate_limited"}
                else:
                    return {"error": "api_error", "status": resp.status_code}
            except Exception as e:
                logger.error(f"Network error checking follows for {username}: {e}")
                return {"error": "network_error"}
