import discord
from discord.ext import commands
from discord import app_commands
import logging
import threading
import sys
from config import Config
from database import DiscordDatabase
from github import GitHubAPI
from verification import VerificationManager
from ui import VerificationView
from tasks import VerificationTasks
from web.oauth_server import start_server, bot_ref

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("bot.main")

class GitHubBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        
        self.db = None
        self.gh = GitHubAPI()
        self.verify_mgr = None
        self.tasks_runner = None
        
    async def setup_hook(self):
        self.db = DiscordDatabase(self, Config.DATABASE_CHANNEL_ID)
        await self.db.initialize()
        
        self.verify_mgr = VerificationManager(self, self.db, self.gh)
        self.tasks_runner = VerificationTasks(self.db, self.gh, self.verify_mgr)
        
        bot_ref["github_api"] = self.gh
        bot_ref["verification_mgr"] = self.verify_mgr
        bot_ref["bot"] = self
        
        self.add_view(VerificationView(self.verify_mgr, self.gh))
        self.tasks_runner.recheck_all_users.start()
        
        await self.tree.sync()
        logger.info("Setup hook completed.")

bot = GitHubBot()

@bot.event
async def on_ready():
    logger.info(f"Bot logged in as {bot.user}")

@bot.tree.command(name="setup-verification", description="Admin: Spawn the verification panel")
@app_commands.default_permissions(administrator=True)
async def setup_verification(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🐉 GitHub Verification",
        description=(
            f"Connect your GitHub account and verify that you follow **@{Config.GITHUB_TARGET_USERNAME}**.\n\n"
            "Choose a verification method below:"
        ),
        color=discord.Color.blurple()
    )
    view = VerificationView(bot.verify_mgr, bot.gh)
    await interaction.channel.send(embed=embed, view=view)
    await interaction.response.send_message("Panel created.", ephemeral=True)

@bot.tree.command(name="verify-user", description="Admin: Force verify a user")
@app_commands.default_permissions(administrator=True)
async def verify_user(interaction: discord.Interaction, member: discord.Member, github_username: str, github_id: int):
    await interaction.response.defer(ephemeral=True)
    result = await bot.verify_mgr.verify_user(member, github_username, github_id, method="admin")
    await interaction.followup.send(result)

@bot.tree.command(name="unverify-user", description="Admin: Unverify a user")
@app_commands.default_permissions(administrator=True)
async def unverify_user(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.defer(ephemeral=True)
    record = await bot.db.get_by_discord_id(member.id)
    if not record:
        await interaction.followup.send("User has no record.")
        return
    await bot.verify_mgr.process_unfollow(record)
    await interaction.followup.send("User unverified and role removed.")

@bot.tree.command(name="reset-user", description="Admin: Delete user record")
@app_commands.default_permissions(administrator=True)
async def reset_user(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.defer(ephemeral=True)
    success = await bot.db.delete(member.id)
    if success:
        await interaction.followup.send("User record deleted.")
    else:
        await interaction.followup.send("No record found to delete.")

@bot.tree.command(name="check-user", description="Admin: Check user status")
@app_commands.default_permissions(administrator=True)
async def check_user(interaction: discord.Interaction, member: discord.Member):
    record = await bot.db.get_by_discord_id(member.id)
    if not record:
        await interaction.response.send_message("User has no record.", ephemeral=True)
        return
    await interaction.response.send_message(f"```json\n{record}\n```", ephemeral=True)

@bot.tree.command(name="recheck-all", description="Admin: Force a recheck of all verified users")
@app_commands.default_permissions(administrator=True)
async def recheck_all(interaction: discord.Interaction):
    await interaction.response.send_message("Starting recheck of all users...", ephemeral=True)
    await bot.tasks_runner.recheck_all_users()
    await interaction.followup.send("Recheck completed.", ephemeral=True)

@bot.tree.command(name="database-stats", description="Admin: Show database stats")
@app_commands.default_permissions(administrator=True)
async def database_stats(interaction: discord.Interaction):
    records = bot.db.get_all_records()
    total = len(records)
    verified = sum(1 for r in records if r.get("verified"))
    unverified = total - verified
    
    msg = (
        f"**Database Stats**\n"
        f"Total records: {total}\n"
        f"Verified: {verified}\n"
        f"Unverified: {unverified}"
    )
    await interaction.response.send_message(msg, ephemeral=True)

if __name__ == "__main__":
    # Start the fastAPI server in a background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    bot.run(Config.DISCORD_TOKEN, log_handler=None)
