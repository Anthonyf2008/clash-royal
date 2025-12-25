# game/match.py
from __future__ import annotations
from typing import List, Optional, Tuple
import random
from game.arena import Arena
from game.player import Player
from game.card import Card, cards
from game.visuals import render_arena_emoji
from game.coords import coord_to_rc, rc_to_coord
import asyncio
import time

async def elixir_loop(ctx, match):
    while match.active:
        for p in match.players:
            p.regen_energy()
            p.tick_cooldowns()

        # (optional) if you want: show elixir sometimes, not every second
        # await ctx.send(render_arena_emoji(match.arena, match))

        await asyncio.sleep(1)


# =========================================================
# MATCH CLASS (FINAL, CLEAN, FULLY FUNCTIONAL)
# =========================================================

class Match:
    def __init__(self, p1: Player, p2: Player):
        self.players = [p1, p2]
        self.active = True
        self.turn_index = 0  # you can delete later

        self.arena = Arena(width=16, height=10, p1_id=p1.user.id, p2_id=p2.user.id)
        import asyncio
        self.lock = asyncio.Lock()
        self.loop_task = None


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
        # bounds + empty
        if not self.arena.in_bounds(row, col):
            return False
        if self.arena.get(row, col) is not None:
            return False

        # can't place on river columns (water OR bridge)
        if hasattr(self.arena, "is_river_column") and self.arena.is_river_column(col):
            return False

        # can't place on towers
        if hasattr(self.arena, "is_tower_cell") and self.arena.is_tower_cell(row, col):
            return False

        # must place on your side (HORIZONTAL)
        # P1 = left side, P2 = right side
        left_river = self.arena.river_left_col() if hasattr(self.arena, "river_left_col") else (
                    self.arena.width // 2 - 1)
        right_river = self.arena.river_right_col() if hasattr(self.arena, "river_right_col") else (
                    self.arena.width // 2)

        if owner_id == self.arena.p1_id:
            # left player can only place left of the river
            if col >= left_river:
                return False
        else:
            # right player can only place right of the river
            if col <= right_river:
                return False

        # store unit data (defaults)
        unit["owner"] = owner_id
        unit.setdefault("hp", 100)
        unit.setdefault("damage", 50)
        unit.setdefault("range", 1)
        unit.setdefault("emoji", "🤺")
        unit.setdefault("speed", 1)

        self.arena.set(row, col, unit)
        return True

    # -----------------------------------------------------
    # MOVEMENT + COMBAT
    # -----------------------------------------------------

    def step_units(self) -> None:
        new_grid = [[None for _ in range(self.arena.width)] for _ in range(self.arena.height)]

        for r in range(self.arena.height):
            for c in range(self.arena.width):
                tile = self.arena.grid[r][c]
                if not isinstance(tile, dict):
                    continue

                if tile.get("type") == "tower":
                    new_grid[r][c] = tile
                    continue

                owner = tile["owner"]
                direction = 1 if owner == self.arena.p1_id else -1  # P1 goes RIGHT, P2 goes LEFT

                target_r = r
                target_c = c + direction

                if not self.arena.in_bounds(target_r, target_c):
                    new_grid[r][c] = tile
                    continue

                target_tile = self.arena.get(target_r, target_c)

                if target_tile is None:
                    if new_grid[target_r][target_c] is None:
                        new_grid[target_r][target_c] = tile
                    else:
                        new_grid[r][c] = tile
                    continue

                if isinstance(target_tile, dict):
                    if target_tile.get("type") == "tower":
                        self.attack_tower(tile, target_tile)
                    else:
                        if target_tile.get("owner") != owner:
                            self.attack_unit(tile, target_r, target_c)

                if new_grid[r][c] is None:
                    new_grid[r][c] = tile

        self.arena.grid = new_grid

    def attack_unit(self, attacker: dict, r: int, c: int) -> None:
        target = self.arena.get(r, c)
        if not target:
            return
        target["hp"] -= attacker["damage"]
        if target["hp"] <= 0:
            self.arena.set(r, c, None)

    def attack_tower(self, attacker: dict, tower_tile: dict) -> None:
        owner = tower_tile["owner"]
        name = tower_tile["name"]

        if name == "king":
            self.arena.towers[owner]["king"]["active"] = True

        self.arena.damage_tower(owner, name, attacker["damage"])

    # -----------------------------------------------------
    # TOWER ATTACKS
    # -----------------------------------------------------

    def tower_attacks(self) -> None:
        if not self.arena.towers:
            return

        for owner_id, tower_set in self.arena.towers.items():
            for name, t in tower_set.items():
                if t.get("hp", 0) <= 0:
                    continue
                if name == "king" and not t.get("active", False):
                    continue

                # ✅ NEW: towers use "cells": [(r,c), ...]
                cells = t.get("cells") or []
                if not cells:
                    continue

                # Use the first cell as the firing origin
                tr, tc = cells[0]

                dmg = 120 if name == "king" else 90
                rng = 7 if name == "king" else 6

                target_pos = self.find_nearest_enemy(owner_id, tr, tc, rng)
                if not target_pos:
                    continue

                r, c = target_pos
                target = self.arena.get(r, c)
                if not target or not isinstance(target, dict):
                    continue

                # Don't let towers shoot towers (optional safety)
                if target.get("type") == "tower":
                    continue

                target["hp"] -= dmg
                if target["hp"] <= 0:
                    self.arena.set(r, c, None)

    def find_nearest_enemy_in_range(
            self,
            owner_id: int,
            row: int,
            col: int,
            max_range: int,
            include_towers: bool = False
    ):
        best = None
        best_dist = 999

        for r in range(self.arena.height):
            for c in range(self.arena.width):
                tile = self.arena.get(r, c)
                if not isinstance(tile, dict):
                    continue

                # Skip friendly
                if tile.get("owner") == owner_id:
                    continue

                # Skip towers unless allowed
                if tile.get("type") == "tower" and not include_towers:
                    continue

                dist = abs(r - row) + abs(c - col)
                if dist <= max_range and dist < best_dist:
                    best_dist = dist
                    best = (r, c)

        return best

    # -----------------------------------------------------
    # TURN RESOLUTION
    # -----------------------------------------------------

    def step_turn(self) -> None:
        if not self.active:
            return
        self.step_units()
        self.tower_attacks()

    def check_win(self) -> Optional[Player]:
        dead_king_owner = self.arena.any_king_dead()
        if dead_king_owner is None:
            return None

        opp_id = self.opponent_id(dead_king_owner)
        if opp_id is None:
            return None
        return self.get_player_by_id(opp_id)


# =========================================================
# END MATCH
# =========================================================

async def end_match(channel, match, winner, loser):
    if not match.active:
        return

    match.active = False

    # stop realtime loop
    task = getattr(match, "loop_task", None)
    if task:
        task.cancel()

    await channel.send(f"🏆 **{winner.user.display_name} wins the match!**")


TICK_SECONDS = 0.25        # simulation tick rate
RENDER_EVERY = 1.0         # send board update at most once per second
ELIXIR_EVERY = 1.0         # +1 elixir every second (change later to 2.8 if you want)

async def realtime_loop(bot, channel_id: int, match):
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

            # Elixir + cooldowns
            if now - last_elixir >= ELIXIR_EVERY:
                last_elixir = now
                for p in match.players:
                    p.regen_energy()
                    p.tick_cooldowns()

            # Step simulation safely
            async with match.lock:
                match.step_turn()

                winner = match.check_win()
                if winner:
                    loser = match.get_player_by_id(match.opponent_id(winner.user.id)) or match.opponent()
                    await end_match(channel, match, winner, loser)  # we’ll patch end_match below
                    return

            # Render throttled
            if now - last_render >= RENDER_EVERY:
                last_render = now
                await channel.send(render_arena_emoji(match.arena, match))

            await asyncio.sleep(TICK_SECONDS)

    except asyncio.CancelledError:
        return

# =========================================================
# AI TURN LOGIC
# =========================================================

async def process_ai_turn(ctx, match):
    if not match.active:
        return

    ai = match.current_player()
    owner_id = ai.user.id

    # ---------- small helper to finish the turn ----------
    async def finish_turn():
        match.step_turn()
        await ctx.send(render_arena_emoji(match.arena, match))
        winner = match.check_win()
        if winner:
            await end_match(ctx, match, winner, match.opponent())
            return True
        match.next_turn()
        return False

    # ---------- gather playable cards ----------
    playable = []
    for name in ai.deck:
        data = cards.get(name)
        if not data:
            continue
        c = Card(name, data)
        if c.can_play(ai):
            playable.append(c)

    if not playable:
        await ctx.send("🤖 **ClashAI** has no playable cards (elixir/cooldown) and skips.")
        await finish_turn()
        return

    card = random.choice(playable)

    # ---------- HORIZONTAL placement rules ----------
    arena = match.arena

    # River columns (2 middle cols)
    river_cols = getattr(arena, "river_cols", [arena.width // 2 - 1, arena.width // 2])
    left_river = min(river_cols)
    right_river = max(river_cols)

    # AI deploy zone: stay 1 tile away from river
    if owner_id == arena.p1_id:
        possible_cols = list(range(0, max(0, left_river - 1)))
    else:
        possible_cols = list(range(min(arena.width - 1, right_river + 1), arena.width))

    possible_rows = list(range(0, arena.height))

    # ---------- try to place ----------
    placed = False
    for _ in range(60):
        r = random.choice(possible_rows)
        c = random.choice(possible_cols)

        # reject river
        if c in river_cols:
            continue

        # reject occupied
        if arena.get(r, c) is not None:
            continue

        unit = card.create_unit(owner_id)
        if match.place_unit_for_player(owner_id, r, c, unit):
            card.apply_cost(ai)
            ai.add_cooldown(card.name)

            # Prefer C4 style if available
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



