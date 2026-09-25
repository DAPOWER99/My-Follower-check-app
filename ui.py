import discord
from discord.ui import View, Button, Modal, TextInput
from oauth import OAuthManager
from config import Config

class ManualVerificationModal(Modal, title="GitHub Verification"):
    username = TextInput(
        label="GitHub username",
        placeholder="Enter your GitHub username here",
        required=True,
        min_length=1,
        max_length=39
    )

    def __init__(self, verification_mgr, github_api):
        super().__init__()
        self.verification_mgr = verification_mgr
        self.github_api = github_api

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        username = self.username.value.strip()
        user_data = await self.github_api.get_user_by_username(username)
        
        if "error" in user_data:
            err = user_data["error"]
            if err == "not_found":
                await interaction.followup.send(f"❌ GitHub user **{username}** not found.", ephemeral=True)
            elif err == "rate_limited":
                await interaction.followup.send("⏳ GitHub API is currently rate limited.", ephemeral=True)
            else:
                await interaction.followup.send("⚠️ Error querying GitHub API.", ephemeral=True)
            return
            
        github_id = user_data.get("id")
        actual_username = user_data.get("login")
        
        result = await self.verification_mgr.verify_user(
            member=interaction.user,
            github_username=actual_username,
            github_id=github_id,
            method="manual"
        )
        
        await interaction.followup.send(result, ephemeral=True)

class VerificationView(View):
    def __init__(self, verification_mgr, github_api):
        super().__init__(timeout=None)
        self.verification_mgr = verification_mgr
        self.github_api = github_api

    @discord.ui.button(label="🔗 Auto Connect", style=discord.ButtonStyle.primary, custom_id="auto_connect_btn")
    async def auto_connect(self, interaction: discord.Interaction, button: Button):
        state = OAuthManager.generate_state(interaction.user.id)
        oauth_url = f"https://github.com/login/oauth/authorize?client_id={Config.GITHUB_CLIENT_ID}&redirect_uri={Config.GITHUB_REDIRECT_URI}&state={state}"
        
        view = View()
        view.add_item(discord.ui.Button(label="Authorize with GitHub", url=oauth_url))
        
        await interaction.response.send_message(
            "Click the button below to connect your GitHub account.",
            view=view,
            ephemeral=True
        )

    @discord.ui.button(label="⌨️ Enter Username", style=discord.ButtonStyle.secondary, custom_id="manual_username_btn")
    async def manual_username(self, interaction: discord.Interaction, button: Button):
        modal = ManualVerificationModal(self.verification_mgr, self.github_api)
        await interaction.response.send_modal(modal)
