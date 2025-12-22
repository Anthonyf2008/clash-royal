# game/match.py
from __future__ import annotations
from typing import List, Optional, Tuple
import random
from game.arena import Arena
from game.player import Player
from game.card import Card, cards
from game.visuals import render_arena_emoji


# =========================================================
# MATCH CLASS (FINAL, CLEAN, FULLY FUNCTIONAL)
# =========================================================

class Match:
    def __init__(self, p1: Player, p2: Player):
        self.players: List[Player] = [p1, p2]
        self.active: bool = True
        self.turn_index: int = 0  # 0 = p1, 1 = p2

        # Arena knows the two player IDs for tower ownership
        self.arena = Arena(width=16, height=10, p1_id=p1.user.id, p2_id=p2.user.id)

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
        if not self.arena.in_bounds(row, col):
            return False
        if self.arena.get(row, col) is not None:
            return False

        # store minimal required data on the unit
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
                direction = 1 if owner == self.arena.p1_id else -1

                target_r = r + direction
                target_c = c

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
                if t["hp"] <= 0:
                    continue
                if name == "king" and not t["active"]:
                    continue

                dmg = 120 if name == "king" else 90
                rng = 7 if name == "king" else 6

                target_pos = self.find_nearest_enemy(owner_id, t["row"], t["col"], rng)
                if not target_pos:
                    continue

                tr, tc = target_pos
                target = self.arena.get(tr, tc)
                if not target:
                    continue

                target["hp"] -= dmg
                if target["hp"] <= 0:
                    self.arena.set(tr, tc, None)

    def find_nearest_enemy(self, owner_id: int, row: int, col: int, max_range: int) -> Optional[Tuple[int, int]]:
        best = None
        best_dist = 999

        for r in range(self.arena.height):
            for c in range(self.arena.width):
                tile = self.arena.get(r, c)
                if not isinstance(tile, dict):
                    continue
                if tile.get("type") == "tower":
                    continue
                if tile.get("owner") == owner_id:
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

async def end_match(ctx, match, winner, loser):
    if not match.active:
        return

    match.active = False
    await ctx.send(f"🏆 **{winner.user.display_name} wins the match!**")


# =========================================================
# AI TURN LOGIC
# =========================================================

async def process_ai_turn(ctx, match):
    if not match.active:
        return

    ai = match.current_player()

    # 50% chance to play a card
    play_card = random.random() < 0.50

    if play_card and ai.deck:
        card_name = random.choice(ai.deck)
        card_data = cards.get(card_name)

        if card_data:
            card = Card(card_name, card_data)

            if card.can_play(ai):
                owner_id = ai.user.id
                direction = 1 if owner_id == match.arena.p1_id else -1

                if direction == -1:
                    possible_rows = list(range(match.arena.height - 4, match.arena.height - 1))
                else:
                    possible_rows = list(range(1, 4))

                placed = False
                attempts = 0

                while not placed and attempts < 20:
                    attempts += 1
                    r = random.choice(possible_rows)
                    c = random.randint(0, match.arena.width - 1)

                    if match.arena.get(r, c) is None:
                        unit = card.create_unit(owner_id)
                        if match.place_unit_for_player(owner_id, r, c, unit):
                            card.apply_cost(ai)
                            ai.add_cooldown(card.name)
                            await ctx.send(f"🤖 **ClashAI** played **{card.name}** at ({r}, {c})")
                            placed = True

    # Resolve movement + combat + towers
    match.step_turn()

    # Show updated grid
    await ctx.send(render_arena_emoji(match.arena))

    # Check win
    winner = match.check_win()
    if winner:
        loser = match.opponent()
        await end_match(ctx, match, winner, loser)
        return

    # Pass turn back to human
    match.next_turn()
