# game/commands/player_cmds.py

from discord.ext import commands
from game.player import get_player
from game.arena import ARENAS
from game.storage import players   # ✅ import global players dict


def setup_player_cmds(bot: commands.Bot):

    @bot.command()
    async def myarena(ctx):
        player = get_player(ctx.author, players)   # ✅ fixed
        arena = ARENAS[player.arena]

        msg = (
            f"🏰 {ctx.author.display_name}'s Arena\n"
            f"- Arena: {arena['name']} (Level {player.arena})\n"
            f"- Trophies: {player.trophies}\n"
            f"- Unlocked cards: {', '.join(player.cards)}"
        )
        await ctx.send(msg)

    @bot.command()
    async def mycards(ctx):
        player = get_player(ctx.author, players)   # ✅ fixed
        await ctx.send(f"🃏 Your cards: {', '.join(player.cards)}")
