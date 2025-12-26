# game/arena.py
from __future__ import annotations

from typing import Optional, Iterator, Tuple, Dict, Any
from game.card import CORE_CARD_NAMES


# ---------------------------------------------------------
# Arena card pools
# ---------------------------------------------------------

ARENAS: Dict[int, Dict[str, Any]] = {
    1: {
        "name": "Training Camp 🏕️",
        "unlock_trophies": 0,
        "cards": CORE_CARD_NAMES,
    }
}


class Arena:
    """
    Arena owns:
      - grid storage (units + tower markers)
      - tower state (true HP/active lives in self.towers)
      - map geometry helpers (river columns)
    Arena does NOT own:
      - movement/pathfinding
      - targeting decisions
      - combat rules (who attacks who)
    """

    def __init__(
        self,
        width: int = 16,
        height: int = 12,
        p1_id: int | None = None,
        p2_id: int | None = None,
    ) -> None:
        self.width = width
        self.height = height

        # Grid stores ONLY markers:
        # - units: {"type":"unit", ...}
        # - towers: {"type":"tower","owner":id,"name":"left/right/king","emoji":"..."}
        self.grid: list[list[Optional[dict]]] = [[None for _ in range(width)] for _ in range(height)]

        self.p1_id = p1_id
        self.p2_id = p2_id

        # River is 2 columns wide in the middle (0-indexed)
        self.river_cols = [self.width // 2 - 1, self.width // 2]

        # Tower state lives here (single source of truth for HP/active)
        self.towers: Dict[int, Dict[str, Dict[str, Any]]] = {}
        if p1_id is not None and p2_id is not None:
            self._init_towers(p1_id, p2_id)
            self.place_towers_on_grid()

    # -----------------------------
    # Tower state (single source of truth)
    # -----------------------------
    def _init_towers(self, p1_id: int, p2_id: int) -> None:
        """
        Creates tower state in a consistent format:
          self.towers[owner_id][tower_name] = {"hp": int, "cells": [(r,c),...], "emoji": str, "active": bool}
        """
        self.towers = {
            p1_id: {
                "left":  {"hp": 1500, "cells": [(2, 3)],           "emoji": "🏰", "active": True},   # C4
                "right": {"hp": 1500, "cells": [(9, 3)],           "emoji": "🏰", "active": True},   # J4
                "king":  {"hp": 3000, "cells": [(5, 1), (6, 1)],   "emoji": "👑", "active": False},  # F2+G2
            },
            p2_id: {
                "left":  {"hp": 1500, "cells": [(2, 12)],          "emoji": "🏰", "active": True},   # C13
                "right": {"hp": 1500, "cells": [(9, 12)],          "emoji": "🏰", "active": True},   # J13
                "king":  {"hp": 3000, "cells": [(5, 14), (6, 14)], "emoji": "👑", "active": False},  # F15+G15
            },
        }

    # -----------------------------
    # Grid helpers
    # -----------------------------
    def in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.height and 0 <= col < self.width

    def get(self, row: int, col: int) -> Optional[dict]:
        if not self.in_bounds(row, col):
            return None
        return self.grid[row][col]

    def set(self, row: int, col: int, value: Optional[dict]) -> None:
        if not self.in_bounds(row, col):
            raise ValueError(f"Out of bounds: ({row}, {col})")
        self.grid[row][col] = value

    def is_empty(self, row: int, col: int) -> bool:
        return self.in_bounds(row, col) and self.grid[row][col] is None

    def place(self, row: int, col: int, obj: dict) -> bool:
        """Place an object if the cell is empty."""
        if not self.is_empty(row, col):
            return False
        self.grid[row][col] = obj
        return True

    def all_positions(self) -> Iterator[Tuple[int, int, Optional[dict]]]:
        for r in range(self.height):
            for c in range(self.width):
                yield r, c, self.grid[r][c]

    def iter_units(self) -> Iterator[Tuple[int, int, dict]]:
        """Iterate over all unit tiles on the grid."""
        for r in range(self.height):
            for c in range(self.width):
                tile = self.grid[r][c]
                if isinstance(tile, dict) and tile.get("type") == "unit":
                    yield r, c, tile

    # -----------------------------
    # River helpers
    # -----------------------------
    def river_left_col(self) -> int:
        return min(self.river_cols)

    def river_right_col(self) -> int:
        return max(self.river_cols)

    def is_river_column(self, col: int) -> bool:
        return col in self.river_cols

    # -----------------------------
    # Tower helpers (grid markers + state access)
    # -----------------------------
    def is_tower_cell(self, row: int, col: int) -> bool:
        tile = self.get(row, col)
        return isinstance(tile, dict) and tile.get("type") == "tower"

    def tower_at(self, row: int, col: int) -> Optional[Tuple[int, str]]:
        """
        If the cell contains a tower marker, return (owner_id, tower_name).
        Otherwise return None.
        """
        tile = self.get(row, col)
        if not isinstance(tile, dict) or tile.get("type") != "tower":
            return None
        return tile["owner"], tile["name"]

    def tower_state(self, owner_id: int, tower_name: str) -> Dict[str, Any]:
        """Convenience accessor for tower state (HP/active/cells/emoji)."""
        return self.towers[owner_id][tower_name]

    def clear_towers_from_grid(self) -> None:
        """Remove all tower markers from the grid."""
        for r in range(self.height):
            for c in range(self.width):
                tile = self.grid[r][c]
                if isinstance(tile, dict) and tile.get("type") == "tower":
                    self.grid[r][c] = None

    def place_towers_on_grid(self) -> None:
        """
        Place tower MARKERS on the grid.
        IMPORTANT: tower HP is NOT stored on the grid to avoid desync.
        """
        if not self.towers:
            return

        self.clear_towers_from_grid()

        for owner_id, tower_set in self.towers.items():
            for name, t in tower_set.items():
                if t["hp"] <= 0:
                    continue
                for (r, c) in t["cells"]:
                    if self.in_bounds(r, c):
                        self.grid[r][c] = {
                            "type": "tower",
                            "owner": owner_id,
                            "emoji": t["emoji"],
                            "name": name,
                        }

    def damage_tower(self, owner_id: int, tower_name: str, dmg: int) -> None:
        """
        Mutate tower HP in tower state (single source of truth).
        Also removes markers from grid when destroyed.
        """
        t = self.towers[owner_id][tower_name]
        if t["hp"] <= 0:
            return

        # If king is hit, activate it
        if tower_name == "king":
            t["active"] = True

        t["hp"] -= dmg
        if t["hp"] <= 0:
            t["hp"] = 0

            # Remove all its cells from the grid
            for (r, c) in t["cells"]:
                if self.in_bounds(r, c):
                    self.grid[r][c] = None

            # If a princess dies => king activates
            if tower_name in ("left", "right"):
                self.towers[owner_id]["king"]["active"] = True

    def any_king_dead(self) -> Optional[int]:
        """Return the owner_id whose king is dead, else None."""
        if not self.towers:
            return None
        for owner_id, tower_set in self.towers.items():
            if tower_set["king"]["hp"] <= 0:
                return owner_id
        return None
