# game/combat.py
from __future__ import annotations
from typing import Optional, Tuple, List

from game.rules import is_enemy


# -----------------------------
# Generic helpers
# -----------------------------

def is_tower(tile: object) -> bool:
    return isinstance(tile, dict) and tile.get("type") == "tower"


def is_unit(tile: object) -> bool:
    return isinstance(tile, dict) and tile.get("type") != "tower"


def can_attack(attacker: dict, target: dict) -> bool:
    """
    Prevent friendly fire. This is the ONE place ownership rules live.
    """
    return is_enemy(attacker.get("owner"), target.get("owner"))


# -----------------------------
# Unit attacks
# -----------------------------

def attack_unit(attacker: dict, target_r: int, target_c: int, grid: list[list]) -> None:
    """
    Attack a unit at (target_r, target_c) on the provided grid (usually 'new_grid' for current tick).
    """
    target = grid[target_r][target_c]
    if not isinstance(target, dict) or is_tower(target):
        return

    if not can_attack(attacker, target):
        return

    dmg = int(attacker.get("damage", 0) or 0)
    target["hp"] = int(target.get("hp", 0) or 0) - dmg

    if target["hp"] <= 0:
        grid[target_r][target_c] = None


def attack_tower(match, attacker: dict, tower_tile: dict) -> None:
    """
    Damage a tower using Arena's single source of truth.
    """
    if not isinstance(tower_tile, dict) or tower_tile.get("type") != "tower":
        return

    if not can_attack(attacker, tower_tile):
        return

    owner = tower_tile["owner"]
    name = tower_tile["name"]

    dmg = int(attacker.get("damage", 0) or 0)
    match.arena.damage_tower(owner, name, dmg)


# -----------------------------
# Tower attacks (your logic, moved from match.py)
# -----------------------------

def tower_attacks(match) -> None:
    """
    Towers shoot nearest enemy unit in range.
    King shoots only when active.
    """
    arena = match.arena
    if not getattr(arena, "towers", None):
        return

    for owner_id, tower_set in arena.towers.items():
        if not isinstance(tower_set, dict):
            continue

        for name, t in tower_set.items():
            if not isinstance(t, dict):
                continue

            hp = int(t.get("hp", 0) or 0)
            if hp <= 0:
                continue

            # King only shoots when active
            if name == "king" and not bool(t.get("active", False)):
                continue

            cells = t.get("cells")
            if not isinstance(cells, list) or not cells:
                continue

            dmg = 120 if name == "king" else 90
            rng = 7 if name == "king" else 6

            # Pre-scan enemy units once
            enemies: List[Tuple[int, int]] = []
            for r in range(arena.height):
                for c in range(arena.width):
                    tile = arena.get(r, c)
                    if not isinstance(tile, dict):
                        continue
                    if tile.get("type") == "tower":
                        continue
                    if tile.get("owner") == owner_id:
                        continue
                    enemies.append((r, c))

            if not enemies:
                continue

            best_target: Optional[Tuple[int, int]] = None
            best_dist = 10**9

            # Use the closest tower cell as origin
            for (tr, tc) in cells:
                if not arena.in_bounds(tr, tc):
                    continue

                for (er, ec) in enemies:
                    dist = abs(er - tr) + abs(ec - tc)
                    if dist <= rng and dist < best_dist:
                        best_dist = dist
                        best_target = (er, ec)

            if best_target is None:
                continue

            r, c = best_target
            target = arena.get(r, c)
            if not isinstance(target, dict):
                continue
            if target.get("type") == "tower":
                continue

            # Friendly fire guard (should already be enemy, but keep safe)
            if not is_enemy(owner_id, target.get("owner")):
                continue

            target["hp"] = int(target.get("hp", 0) or 0) - dmg
            if target["hp"] <= 0:
                arena.set(r, c, None)
