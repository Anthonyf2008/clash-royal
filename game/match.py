# game/match.py
from __future__ import annotations

from typing import Optional
import asyncio
import time

from game.movement import step_movement
from game.arena import Arena
from game.player import Player
from game.combat import tower_attacks
from game.rules import is_valid_deploy
from game.visuals import render_arena_emoji



# ---------------------------------------------------------
# Tunables
# ---------------------------------------------------------
TICK_SECONDS = 0.25      # simulation tick rate (4 ticks/sec)
ELIXIR_EVERY = 1.0       # +1 elixir per second
RENDER_EVERY = 1.5       # send board every 1.5s (prevents spam)


class Match:
    """
    Match owns:
      - players + match lifecycle (active, winner)
      - calling step functions (movement/combat/towers)
      - thread safety lock for realtime loop + commands

    Match does NOT own (but may call):
      - deploy rules (rules.py)
      - combat rules (combat.py)
      - unit formatting (unit.py)
    """

    def __init__(self, p1: Player, p2: Player) -> None:
        self.players = [p1, p2]
        self.active = True

        # You can remove "turn_index" later; kept for compatibility with existing commands/AI
        self.turn_index = 0

        self.arena = Arena(width=16, height=10, p1_id=p1.user.id, p2_id=p2.user.id)

        self.lock = asyncio.Lock()
        self.loop_task: Optional[asyncio.Task] = None

    # -----------------------------------------------------
    # BASIC HELPERS
    # -----------------------------------------------------
    def current_player(self) -> Player:
        return self.players[self.turn_index]

    def opponent(self) -> Player:
        return self.players[1 - self.turn_index]

    def get_player_by_id(self, user_id: int) -> Optional[Player]:
        for p in self.players:
            if p.user.id == user_id:
                return p
        return None

    def opponent_id(self, user_id: int) -> Optional[int]:
        if self.players[0].user.id == user_id:
            return self.players[1].user.id
        if self.players[1].user.id == user_id:
            return self.players[0].user.id
        return None

    def next_turn(self) -> None:
        self.turn_index = 1 - self.turn_index

    # -----------------------------------------------------
    # UNIT PLACEMENT
    # -----------------------------------------------------
    def place_unit_for_player(self, owner_id: int, row: int, col: int, unit: dict) -> bool:
        """
        Place a unit/building tile on the grid if valid.
        Spells should be handled elsewhere (effects.py).
        """
        if not is_valid_deploy(self.arena, owner_id, row, col):
            return False

        # Ensure ownership & minimum defaults (until everything uses unit.py spawn)
        unit["owner"] = owner_id
        unit.setdefault("hp", 100)
        unit.setdefault("damage", 50)
        unit.setdefault("range", 1)
        unit.setdefault("speed", 1)
        unit.setdefault("emoji", "🤺")

        self.arena.set(row, col, unit)
        return True

    # -----------------------------------------------------
    # SIMULATION STEP
    # -----------------------------------------------------
    def step_units(self) -> None:
        step_movement(self)

    def step_turn(self) -> None:
        """
        One simulation step. (Name kept for compatibility)
        """
        if not self.active:
            return
        self.step_units()
        tower_attacks(self)

    def check_win(self) -> Optional[Player]:
        dead_king_owner = self.arena.any_king_dead()
        if dead_king_owner is None:
            return None

        winner_id = self.opponent_id(dead_king_owner)
        if winner_id is None:
            return None

        return self.get_player_by_id(winner_id)


# =========================================================
# END MATCH HELPERS
# =========================================================

async def end_match_channel(channel, match: Match, winner: Player, loser: Player) -> None:
    if not match.active:
        return
    match.active = False
    await channel.send(f"🏆 **{winner.user.display_name} wins the match!**")


# =========================================================
# REALTIME LOOP
# =========================================================

async def realtime_loop(bot, channel_id: int, match: Match) -> None:
    """
    Real-time loop:
    - steps the simulation on a fixed tick
    - regenerates elixir on a timer
    - renders occasionally (not every tick)
    """
    channel = bot.get_channel(channel_id)
    if channel is None:
        return

    last_render = 0.0
    last_elixir = 0.0

    try:
        while match.active:
            now = time.monotonic()

            async with match.lock:
                # Elixir + cooldowns
                if now - last_elixir >= ELIXIR_EVERY:
                    last_elixir = now
                    for p in match.players:
                        p.regen_energy()
                        p.tick_cooldowns()

                # Step simulation
                match.step_turn()

                # Win check
                winner = match.check_win()
                if winner:
                    loser_id = match.opponent_id(winner.user.id)
                    loser = match.get_player_by_id(loser_id) if loser_id else match.opponent()
                    await end_match_channel(channel, match, winner, loser)
                    return

            # Render throttled
            if now - last_render >= RENDER_EVERY:
                last_render = now
                await channel.send(render_arena_emoji(match.arena, match))

            await asyncio.sleep(TICK_SECONDS)

    except asyncio.CancelledError:
        return


