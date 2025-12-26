# game/unit.py
from __future__ import annotations

from typing import Any, Dict, Optional
from game.card import Card


# ---- Tile type constants (helps prevent bugs) ----
TILE_UNIT = "unit"
TILE_TOWER = "tower"


def is_unit(tile: object) -> bool:
    return isinstance(tile, dict) and tile.get("type") == TILE_UNIT


def is_tower(tile: object) -> bool:
    return isinstance(tile, dict) and tile.get("type") == TILE_TOWER


def make_unit_from_card(card: Card, owner_id: int) -> Dict[str, Any]:
    """
    Convert a Card into a GRID UNIT tile dict.

    IMPORTANT:
      - tile["type"] is ALWAYS "unit" (so movement/targeting/combat can rely on it)
      - card category (troop/building/spell) is stored in tile["kind"]
    """
    if card.type == "spell":
        raise ValueError("Spells do not create units. Handle spells separately.")

    return {
        "type": TILE_UNIT,        # <--- consistent grid marker
        "kind": card.type,        # troop | building
        "name": card.name,
        "owner": owner_id,
        "hp": card.hp,
        "damage": card.damage,
        "range": card.range,
        "speed": card.speed,
        "special": card.special,
        "emoji": card.emoji,
    }


def unit_owner(tile: Dict[str, Any]) -> Optional[int]:
    return tile.get("owner")


def unit_is_building(tile: Dict[str, Any]) -> bool:
    return tile.get("kind") == "building"


def unit_is_troop(tile: Dict[str, Any]) -> bool:
    return tile.get("kind") == "troop"
