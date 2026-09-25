# GitHub Verification Bot

A complete Discord bot that verifies whether users follow a specific GitHub account and manages a Discord role accordingly. It uses Discord messages as its persistent database.

## Setup

1. Check `.env` and fill in any missing values:
   - `DISCORD_TOKEN`: Your bot token
   - `GUILD_ID`: The server ID
   - `VERIFIED_ROLE_ID`: The ID of the role to assign to verified users
   - `DATABASE_CHANNEL_ID`: The ID of the private channel to store JSON records in
   - `GITHUB_TARGET_USERNAME`: The GitHub username users need to follow (e.g. `dapower99`)
   - `GITHUB_CLIENT_ID` & `GITHUB_CLIENT_SECRET`: Create an OAuth app in GitHub settings
   - `GITHUB_REDIRECT_URI`: The callback URL for OAuth (e.g., `http://127.0.0.1:8000/callback`)

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the bot:
   ```bash
   python bot.py
   ```

## Discord as Database
The bot uses a specific channel (`DATABASE_CHANNEL_ID`) to persist user verification data. Each user gets their own JSON message.
Do NOT manually edit these messages unless you are sure of the format.

## OAuth Setup
1. Go to your GitHub account -> Developer settings -> OAuth Apps.
2. Create a new OAuth App.
3. Set the Authorization callback URL to match your `GITHUB_REDIRECT_URI` (must be exact).
4. Save the Client ID and generate a Client Secret.

## Commands (Admin Only)
- `/setup-verification`: Spawns the verification panel UI in the current channel.
- `/verify-user`: Force verify a user by providing their discord member, github username, and ID.
- `/unverify-user`: Manually remove verification from a user.
- `/reset-user`: Delete a user's record from the database.
- `/check-user`: View a user's JSON record.
- `/recheck-all`: Manually trigger the follow check for all verified users.
- `/database-stats`: View database statistics.
