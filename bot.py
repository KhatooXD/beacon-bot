import discord
from discord.ext import commands

import config
from utils.i18n import t


class Beacon(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True  # needed to read messages for transcripts
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
            activity=discord.CustomActivity(name=t("bot.status")),
        )

    async def setup_hook(self):
        await self.load_extension("cogs.tickets")
        # Sync slash commands to the configured guild so they show up instantly
        guild = discord.Object(id=config.GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        synced = await self.tree.sync(guild=guild)
        print(f"Synced {len(synced)} slash commands (language: {config.LANGUAGE})")

    async def on_ready(self):
        print(f"🔆 Beacon is online as {self.user} (ID: {self.user.id})")


if __name__ == "__main__":
    Beacon().run(config.TOKEN)