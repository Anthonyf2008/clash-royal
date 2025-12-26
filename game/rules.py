# game/rules.py
from __future__ import annotations
from typing import Optional


# -----------------------------
# Ownership / sides
# -----------------------------

def is_enemy(owner_a: Optional[int], owner_b: Optional[int]) -> bool:
    if owner_a is None or owner_b is None:
        return False
    return owner_a != owner_b


def is_player1(arena, owner_id: int) -> bool:
    return owner_id == arena.p1_id


def is_player2(arena, owner_id: int) -> bool:
    return owner_id == arena.p2_id


# -----------------------------
# River helpers (arena already has these, but this keeps rules safe)
# -----------------------------

def river_cols(arena) -> tuple[int, int]:
    cols = getattr(arena, "river_cols", [arena.width // 2 - 1, arena.width // 2])
    left = min(cols)
    right = max(cols)
    return left, right


def is_river_column(arena, col: int) -> bool:
    left, right = river_cols(arena)
    return col == left or col == right


# -----------------------------
# Deploy rules
# -----------------------------

def is_on_owner_side(arena, owner_id: int, col: int) -> bool:
    """
    Your game is horizontal:
      - P1 owns LEFT side
      - P2 owns RIGHT side
    River is 2 columns wide; players cannot deploy on river columns.
    """
    left, right = river_cols(arena)

    if owner_id == arena.p1_id:
        return col < left
    if owner_id == arena.p2_id:
        return col > right

    # unknown owner -> deny
    return False


def is_valid_deploy(arena, owner_id: int, row: int, col: int) -> bool:
    """
    True if a unit/building can be deployed here.
    - inside bounds
    - empty
    - not on river columns
    - not on a tower cell
    - on the owner's side
    """
    if not arena.in_bounds(row, col):
        return False

    if arena.get(row, col) is not None:
        return False

    if hasattr(arena, "is_river_column"):
        if arena.is_river_column(col):
            return False
    else:
        if is_river_column(arena, col):
            return False

    if hasattr(arena, "is_tower_cell"):
        if arena.is_tower_cell(row, col):
            return False

    if not is_on_owner_side(arena, owner_id, col):
        return False

    return True
