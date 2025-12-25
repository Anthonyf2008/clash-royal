# game/commands/match_cmds.py

from __future__ import annotations

import asyncio
from discord.ext import commands

from game.storage import players
from game.visuals import render_arena_emoji
from game.player import get_player
from game.match import Match, end_match, realtime_loop
from game.arena import ARENAS
from game.card import Card, cards
from game.coords import coord_to_rc, rc_to_coord





# ✅ Only ONE match registry
matches: dict[int, Match] = {}
def setup_match_cmds(bot: commands.Bot):

    # ---------------------------------------------------------
    # START MATCH VS AI
    # ---------------------------------------------------------
    @bot.command()
    async def cr_start_ai(ctx):
        if ctx.channel.id in matches and matches[ctx.channel.id].active:
            await ctx.send("⚠️ A match already exists in this channel.")
            return

        # Create human player
        human = get_player(ctx.author, players)

        # Create fake AI user + player
        ai_user = type("AIUser", (), {})()
        ai_user.id = 999999999999
        ai_user.display_name = "ClashAI"

        ai_player = get_player(ai_user, players)
        ai_player.is_ai = True
        ai_player.cards = ARENAS[1]["cards"]
        ai_player.deck = ai_player.cards[:5]

        # Create match ONCE
        match = Match(human, ai_player)
        matches[ctx.channel.id] = match

        # Start realtime loop
        match.loop_task = asyncio.create_task(realtime_loop(bot, ctx.channel.id, match))

        await ctx.send(
            f"🤖 {ctx.author.mention} started a real-time match vs **{ai_player.user.display_name}**!\n"
            f"Play anytime with `!cr_play <card> <pos>` (example: `!cr_play knight C4`)."
        )

        # Show initial arena
        await ctx.send(render_arena_emoji(match.arena, match))

    # ---------------------------------------------------------
    # PLAY A CARD
    # ---------------------------------------------------------
    @bot.command()
    async def cr_play(ctx, card_name: str, pos: str):
        match = matches.get(ctx.channel.id)
        if not match or not match.active:
            await ctx.send("❌ No active match.")
            return

        player = match.get_player_by_id(ctx.author.id)
        if not player:
            await ctx.send("❌ You are not in this match.")
            return

        parsed = coord_to_rc(pos)
        if not parsed:
            await ctx.send("❌ Invalid position. Use format like C4.")
            return

        row, col = parsed

        if card_name not in player.deck:
            await ctx.send("❌ Card not in your deck.")
            return

        if card_name not in cards:
            await ctx.send("❌ Unknown card.")
            return

        card = Card(card_name, cards[card_name])

        if not card.can_play(player):
            await ctx.send("❌ Can't play this card (elixir/cooldown).")
            return

        unit = card.create_unit(player.user.id)

        async with match.lock:
            if not match.place_unit_for_player(player.user.id, row, col, unit):
                await ctx.send("❌ Invalid placement.")
                return

            card.apply_cost(player)
            player.add_cooldown(card.name)

        await ctx.send(f"🎮 {ctx.author.mention} played **{card.name}** at {rc_to_coord(row, col)}")
        await ctx.send(render_arena_emoji(match.arena, match))

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

