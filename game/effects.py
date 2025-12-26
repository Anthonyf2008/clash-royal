# game/effects.py
from __future__ import annotations
from typing import Dict, Any


# ---- Effect keys (prevents typos) ----
EFFECT_FROZEN = "frozen"
EFFECT_STUNNED = "stunned"
EFFECT_RAGE = "rage"
EFFECT_SHIELD = "shield"
EFFECT_SLOW = "slow"


def apply_spell_effect(
    effect: str,
    *,
    caster,
    arena,
    center: tuple[int, int] | None = None,
) -> None:
    """
    Apply a spell effect to the arena or players.
    No direct damage here.
    """

    if effect == "freeze":
        _apply_freeze(arena, center)

    elif effect == "zap":
        _apply_stun(arena, center)

    elif effect == "rage":
        _apply_rage(arena, center)

    # Add more spells here


# -----------------------------
# Effect implementations
# -----------------------------

def _apply_freeze(arena, center: tuple[int, int] | None):
    """
    Freeze all enemy units in a small radius.
    """
    if center is None:
        return

    for r, c, tile in arena.all_positions():
        if not isinstance(tile, dict):
            continue
        if tile.get("type") != "unit":
            continue

        if _in_radius((r, c), center, radius=1):
            tile["status"] = tile.get("status", {})
            tile["status"][EFFECT_FROZEN] = 2  # ticks


def _apply_stun(arena, center: tuple[int, int] | None):
    if center is None:
        return

    for r, c, tile in arena.all_positions():
        if isinstance(tile, dict) and tile.get("type") == "unit":
            if _in_radius((r, c), center, radius=0):
                tile["status"] = tile.get("status", {})
                tile["status"][EFFECT_STUNNED] = 1


def _apply_rage(arena, center: tuple[int, int] | None):
    if center is None:
        return

    for r, c, tile in arena.all_positions():
        if isinstance(tile, dict) and tile.get("type") == "unit":
            if _in_radius((r, c), center, radius=1):
                tile["status"] = tile.get("status", {})
                tile["status"][EFFECT_RAGE] = 3


# -----------------------------
# Status ticking (called each game tick)
# -----------------------------

def tick_status_effects(arena) -> None:
    """
    Decrease status timers and remove expired effects.
    """
    for _, _, tile in arena.all_positions():
        if not isinstance(tile, dict):
            continue

        status: Dict[str, int] = tile.get("status", {})
        expired = []

        for name, turns in status.items():
            status[name] -= 1
            if status[name] <= 0:
                expired.append(name)

        for e in expired:
            del status[e]

        if not status:
            tile.pop("status", None)


# -----------------------------
# Helpers
# -----------------------------

def _in_radius(a: tuple[int, int], b: tuple[int, int], radius: int) -> bool:
    return abs(a[0] - b[0]) <= radius and abs(a[1] - b[1]) <= radius
