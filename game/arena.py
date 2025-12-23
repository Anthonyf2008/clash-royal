# game/arena.py
from __future__ import annotations
from typing import Optional, Literal, Iterator, Tuple, Dict, Any

# ---------------------------------------------------------
# Arena card pools
# ---------------------------------------------------------
ARENAS: Dict[int, Dict[str, Any]] = {
    1: {
        "name": "Training Camp 🏕️",
        "unlock_trophies": 0,
        "cards": [
            "knight", "archer", "giant", "fireball",
            "valkyrie", "musketeer", "mini_pekka", "baby_dragon",
            "skeletons", "bomber", "witch", "prince",
            "dark_prince", "hunter", "ice_spirit",
            "barbarians", "cannon", "wizard",
            "minions", "mega_minion", "golem", "rage", "tornado",
            "furnace", "guards", "hog_rider",
            "inferno_tower", "freeze", "poison",
            "lava_hound", "miner", "sparky", "electro_wizard",
            "royal_giant", "three_musketeers",
        ],
    }
}

Direction = Literal["up", "down", "left", "right"]

class Arena:
    """
    Horizontal arena (left vs right).

    Grid is 12x16 to match A-L and 1-16.

    River is 2 columns wide in the middle:
      cols 8 and 9 (1-indexed) -> col indexes 7 and 8 (0-indexed)

    Bridges at:
      row C and row J (1-indexed letters) -> indexes 2 and 9
      and on both river columns.
    """

    def __init__(self, width: int = 16, height: int = 12,
                 p1_id: int | None = None, p2_id: int | None = None) -> None:
        self.width = width
        self.height = height

        self.grid: list[list[Optional[dict]]] = [
            [None for _ in range(width)] for _ in range(height)
        ]

        self.p1_id = p1_id
        self.p2_id = p2_id

        # Tower layout (YOUR coordinates):
        # Princess towers at: C4, J4, C13, J13
        # Kings are 2x1 at: F2+G2 and F15+G15
        #
        # Convert to 0-index:
        # C -> 2, J -> 9, F -> 5, G -> 6
        # 4 -> col 3, 13 -> col 12, 2 -> col 1, 15 -> col 14

        if p1_id is not None and p2_id is not None:
            self.towers: Dict[int, Dict[str, Dict[str, Any]]] = {
                p1_id: {
                    "left":  {"hp": 1500, "cells": [(2, 3)],  "emoji": "🏰", "active": True},   # C4
                    "right": {"hp": 1500, "cells": [(9, 3)],  "emoji": "🏰", "active": True},   # J4
                    "king":  {"hp": 3000, "cells": [(5, 1), (6, 1)], "emoji": "👑", "active": False},  # F2+G2
                },
                p2_id: {
                    "left":  {"hp": 1500, "cells": [(2, 12)], "emoji": "🏰", "active": True},   # C13
                    "right": {"hp": 1500, "cells": [(9, 12)], "emoji": "🏰", "active": True},   # J13
                    "king":  {"hp": 3000, "cells": [(5, 14), (6, 14)], "emoji": "👑", "active": False},  # F15+G15
                },
            }
        else:
            self.towers = {}

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

    def river_left_col(self) -> int:
        river_cols = getattr(self, "river_cols", [self.width // 2 - 1, self.width // 2])
        return min(river_cols)

    def river_right_col(self) -> int:
        river_cols = getattr(self, "river_cols", [self.width // 2 - 1, self.width // 2])
        return max(river_cols)

    def is_river_column(self, col: int) -> bool:
        river_cols = getattr(self, "river_cols", [self.width // 2 - 1, self.width // 2])
        return col in river_cols

    def is_tower_cell(self, row: int, col: int) -> bool:
        """True if (row,col) is any tower tile (including 2x1 kings)."""
        if not getattr(self, "towers", None):
            return False

        for _, tower_set in self.towers.items():
            for _, t in tower_set.items():
                if t.get("hp", 0) <= 0:
                    continue

                # supports both styles: single (row/col) or multi-cell (cells/positions)
                if "cells" in t:
                    if (row, col) in t["cells"]:
                        return True
                elif "positions" in t:
                    if (row, col) in t["positions"]:
                        return True
                else:
                    if t.get("row") == row and t.get("col") == col:
                        return True

        return False

    def is_empty(self, row: int, col: int) -> bool:
        return self.in_bounds(row, col) and self.grid[row][col] is None

    def place(self, row: int, col: int, obj: dict) -> bool:
        if not self.is_empty(row, col):
            return False
        self.set(row, col, obj)
        return True

    def all_positions(self) -> Iterator[Tuple[int, int, Optional[dict]]]:
        for r in range(self.height):
            for c in range(self.width):
                yield r, c, self.grid[r][c]

    # -----------------------------
    # Towers on grid
    # -----------------------------
    def clear_towers_from_grid(self) -> None:
        # Remove tower tiles so they don’t duplicate
        for r in range(self.height):
            for c in range(self.width):
                tile = self.get(r, c)
                if isinstance(tile, dict) and tile.get("type") == "tower":
                    self.set(r, c, None)

    def place_towers_on_grid(self) -> None:
        if not self.towers:
            return

        for owner_id, tower_set in self.towers.items():
            for name, t in tower_set.items():
                if t["hp"] <= 0:
                    continue
                for (r, c) in t["cells"]:
                    if self.in_bounds(r, c):
                        self.grid[r][c] = {
                            "type": "tower",
                            "owner": owner_id,
                            "hp": t["hp"],
                            "emoji": t["emoji"],
                            "name": name,
                        }

    def damage_tower(self, owner_id: int, tower_name: str, dmg: int) -> None:
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
        if not self.towers:
            return None
        for owner_id, tower_set in self.towers.items():
            if tower_set["king"]["hp"] <= 0:
                return owner_id
        return None
