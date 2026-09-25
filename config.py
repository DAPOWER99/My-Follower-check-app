import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GITHUB_TARGET_USERNAME = os.getenv("GITHUB_TARGET_USERNAME", "dapower99")
    GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
    GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "")
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
    GUILD_ID = int(os.getenv("GUILD_ID", 0))
    VERIFIED_ROLE_ID = int(os.getenv("VERIFIED_ROLE_ID", 0))
    DATABASE_CHANNEL_ID = int(os.getenv("DATABASE_CHANNEL_ID", 0))
    OAUTH_SERVER_HOST = os.getenv("OAUTH_SERVER_HOST", "0.0.0.0")
    OAUTH_SERVER_PORT = int(os.getenv("PORT", os.getenv("OAUTH_SERVER_PORT", 8000)))
    OAUTH_FRONTEND_URL = os.getenv("OAUTH_FRONTEND_URL", f"http://127.0.0.1:{OAUTH_SERVER_PORT}")
