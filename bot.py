import os
import discord
from discord.ext import commands

from game.storage import load_players
from game.commands import setup_all_commands
from game.arena import ARENAS

# ================== LOAD PLAYER DATA ==================
load_players()   # loads into storage.players

# ================== DISCORD SETUP ==================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Load all command modules
setup_all_commands(bot)

# ================== EVENTS ==================
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# ================== PLAYER UTILITY COMMANDS ==================
@bot.command()
async def show_arenas(ctx):
    msg = "🏟️ Arenas:\n"
    for arena_id, arena in ARENAS.items():
        msg += (
            f"- Arena {arena_id}: {arena['name']} "
            f"(Unlock at {arena['unlock_trophies']} trophies)\n"
            f"  Unlocks: {', '.join(arena['cards'])}\n"
        )
    await ctx.send(msg)

# ================== RUN BOT ==================
bot.run(os.getenv("DISCORD_TOKEN"))
