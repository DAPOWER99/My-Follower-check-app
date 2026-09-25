from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import logging
import asyncio
from config import Config
from oauth import OAuthManager

logger = logging.getLogger("bot.web")
app = FastAPI()

# A hook to pass bot instances back
bot_ref = {}

@app.get("/callback")
async def oauth_callback(request: Request):
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    
    if not code or not state:
        return HTMLResponse("Invalid request: Missing code or state", status_code=400)
        
    discord_id = OAuthManager.verify_state(state)
    if not discord_id:
        return HTMLResponse("Invalid or expired OAuth state. Please try again from Discord.", status_code=400)
        
    access_token = await OAuthManager.exchange_code(code)
    if not access_token:
        return HTMLResponse("Failed to obtain access token from GitHub.", status_code=400)
        
    gh = bot_ref.get("github_api")
    verify_mgr = bot_ref.get("verification_mgr")
    bot = bot_ref.get("bot")
    
    if not all([gh, verify_mgr, bot]):
        return HTMLResponse("Bot is not fully initialized. Try again later.", status_code=500)
        
    user_data = await gh.get_user_by_token(access_token)
    if "error" in user_data:
        return HTMLResponse("Failed to fetch GitHub profile information.", status_code=400)
        
    github_id = user_data.get("id")
    actual_username = user_data.get("login")
    
    guild = bot.get_guild(Config.GUILD_ID)
    if not guild:
        return HTMLResponse("Bot is not in the configured server.", status_code=500)
        
    member = guild.get_member(discord_id)
    if not member:
        return HTMLResponse("You are not in the Discord server.", status_code=400)
        
    # Process asynchronously to return response fast
    asyncio.create_task(verify_mgr.verify_user(
        member=member,
        github_username=actual_username,
        github_id=github_id,
        method="oauth"
    ))
    
    return HTMLResponse(f"""
    <html>
        <head><title>Success</title></head>
        <body style="font-family: sans-serif; text-align: center; padding: 50px;">
            <h2>✅ GitHub Connected!</h2>
            <p>Your GitHub account <b>{actual_username}</b> was linked.</p>
            <p>You can close this window and return to Discord.</p>
        </body>
    </html>
    """)

def start_server():
    import uvicorn
    uvicorn.run(app, host=Config.OAUTH_SERVER_HOST, port=Config.OAUTH_SERVER_PORT, log_level="warning")
