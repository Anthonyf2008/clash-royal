# game/commands/match_cmds.py

from __future__ import annotations
from game.storage import players
from game.visuals import render_arena_emoji
import random
from discord.ext import commands
from game.player import get_player
from game.match import Match, process_ai_turn, end_match
from game.arena import ARENAS
from game.card import Card, cards


# ✅ Only ONE match registry
matches: dict[int, Match] = {}
def setup_match_cmds(bot: commands.Bot):

    # ---------------------------------------------------------
    # START MATCH VS AI
    # ---------------------------------------------------------
    @bot.command()
    async def cr_start_ai(ctx):
        if ctx.channel.id in matches:
            await ctx.send("⚠️ A match already exists in this channel.")
            return

        human = get_player(ctx.author, players)

        # Fake AI user
        ai_user = type("AIUser", (), {})()
        ai_user.id = 999999999999
        ai_user.display_name = "ClashAI"
        ai_player = get_player(ai_user, players)

        # 🔥 THIS LINE IS REQUIRED
        ai_player.is_ai = True

        ai_player.cards = ARENAS[1]["cards"]
        ai_player.deck = ai_player.cards[:5]
        match = Match(human, ai_player)
        matches[ctx.channel.id] = match

        await ctx.send(
            f"🤖 {ctx.author.mention} started a match against {ai_player.user.display_name}!\n"
            f"Your turn first. Play a card with `!cr_play <card> <row> <col>`."
        )

    # ---------------------------------------------------------
    # PLAY A CARD
    # ---------------------------------------------------------
    @bot.command()
    async def cr_play(ctx, card_name: str, row: int, col: int):
        match = matches.get(ctx.channel.id)
        if not match or not match.active:
            await ctx.send("❌ No active match.")
            return

        player = match.current_player()
        if ctx.author.id != player.user.id:
            await ctx.send("⏳ Not your turn.")
            return

        # ✅ Removed old is_disabled() logic

        if card_name not in player.deck:
            await ctx.send("❌ Card not in your deck.")
            return

        if card_name not in cards:
            await ctx.send("❌ Unknown card.")
            return

        card = Card(card_name, cards[card_name])

        if not card.can_play(player):
            await ctx.send("❌ Can't play this card (energy or cooldown).")
            return

        # ✅ Create unit using new system
        unit = card.create_unit(player.user.id)

        # ✅ Place unit
        if not match.place_unit_for_player(player.user.id, row, col, unit):
            await ctx.send("❌ Invalid placement (out of bounds or occupied).")
            return

        card.apply_cost(player)
        player.add_cooldown(card.name)

        await ctx.send(
            f"🎮 {player.user.mention} played **{card.name}** at ({row}, {col})"
        )

        # ✅ Show updated grid
        await ctx.send(render_arena_emoji(match.arena))

        # ✅ Check win
        winner = match.check_win()
        if winner:
            await end_match(ctx, match, winner, match.opponent())
            return

        match.next_turn()

        if match.current_player().is_ai:
            await process_ai_turn(ctx, match)

    # ---------------------------------------------------------
    # MATCH STATUS
    # ---------------------------------------------------------
    @bot.command()
    async def cr_status(ctx):
        match = matches.get(ctx.channel.id)
        if not match or not match.active:
            await ctx.send("No active match.")
            return

        p1, p2 = match.players

        await ctx.send(
            f"⚔️ Match Status:\n"
            f"{p1.user.display_name}: {p1.energy} Energy\n"
            f"{p2.user.display_name}: {p2.energy} Energy"
        )

    # ---------------------------------------------------------
    # LEADERBOARD
    # ---------------------------------------------------------
    @bot.command()
    async def cr_leaderboard(ctx):
        from game.storage import load_players
        loaded = load_players()

        if not loaded:
            await ctx.send("No players yet.")
            return

        leaderboard = sorted(
            loaded.values(),
            key=lambda p: (-p.trophies, -p.wins, -p.coins)
        )

        msg = "🏆 Leaderboard:\n"
        for i, p in enumerate(leaderboard[:10], 1):
            msg += f"{i}. {p.user.display_name} — {p.trophies} trophies | {p.wins} wins | {p.coins} coins (Arena {p.arena})\n"

        await ctx.send(msg)

