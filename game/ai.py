# game/ai.py
from __future__ import annotations

import random
from typing import Optional

from game.card import Card, cards
from game.rules import is_valid_deploy
from game.unit import make_unit_from_card
from game.coords import rc_to_coord
from game.visuals import render_arena_emoji


async def process_ai_turn(ctx, match) -> None:
    """
    Simple AI:
    - chooses a random playable NON-SPELL card
    - finds a random valid deploy tile on its side
    - plays it
    """
    if not match.active:
        return

    ai = match.current_player()
    owner_id = ai.user.id
    arena = match.arena

    # ----- gather playable NON-SPELL cards -----
    playable: list[Card] = []
    for name in ai.deck:
        data = cards.get(name)
        if not data:
            continue
        c = Card(name, data)
        if c.type == "spell":
            continue
        if c.can_play(ai):
            playable.append(c)

    # helper to advance sim + render + win check
    async def finish_turn() -> bool:
        match.step_turn()
        await ctx.send(render_arena_emoji(match.arena, match))

        winner = match.check_win()
        if winner:
            # if you have end_match_channel in match.py, import it here instead
            await ctx.send(f"🏆 **{winner.user.display_name} wins the match!**")
            match.active = False
            return True

        match.next_turn()
        return False

    if not playable:
        await ctx.send("🤖 **ClashAI** has no playable cards (elixir/cooldown) and skips.")
        await finish_turn()
        return

    card = random.choice(playable)

    # ----- try to find a valid tile -----
    placed = False
    for _ in range(80):
        r = random.randrange(0, arena.height)
        c = random.randrange(0, arena.width)

        if not is_valid_deploy(arena, owner_id, r, c):
            continue

        unit = make_unit_from_card(card, owner_id)

        if match.place_unit_for_player(owner_id, r, c, unit):
            card.apply_cost(ai)
            ai.add_cooldown(card.name)

            try:
                pos_txt = rc_to_coord(r, c)
            except Exception:
                pos_txt = f"({r}, {c})"

            await ctx.send(f"🤖 **ClashAI** played **{card.name}** at **{pos_txt}**")
            placed = True
            break

    if not placed:
        await ctx.send("🤖 **ClashAI** couldn't find a valid tile and skips.")

    await finish_turn()
