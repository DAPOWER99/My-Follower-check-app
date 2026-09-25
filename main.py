import threading
from web.oauth_server import start_server
from bot import bot
from config import Config

if __name__ == "__main__":
    # Start the fastAPI server in a background thread for OAuth
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Start the Discord bot
    bot.run(Config.DISCORD_TOKEN, log_handler=None)
