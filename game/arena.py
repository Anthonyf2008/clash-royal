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

# ---------------------------------------------------------
# Grid movement directions
# ---------------------------------------------------------

Direction = Literal["up", "down", "left", "right"]


# ---------------------------------------------------------
# Arena class (battlefield grid + towers)
# ---------------------------------------------------------

class Arena:
    """
    The battlefield grid.

    Coordinates:
        row: 0..height-1  (top → bottom)
        col: 0..width-1   (left → right)

    The grid stores:
        - None
        - dict objects for units and towers
          (match.py expects dicts with at least 'owner', 'hp', 'emoji')
    """

    def __init__(self, width: int = 16, height: int = 10,
                 p1_id: int | None = None, p2_id: int | None = None) -> None:
        self.width = width
        self.height = height

        # 2D grid: rows x cols
        self.grid: list[list[Optional[dict]]] = [
            [None for _ in range(width)] for _ in range(height)
        ]

        # Player IDs (needed for tower ownership)
        self.p1_id = p1_id
        self.p2_id = p2_id

        # Towers for both players
        # Princess towers in front, king tower behind
        self.towers: Dict[int, Dict[str, Dict[str, Any]]] = {
            p1_id: {
                "left": {
                    "hp": 1500,
                    "row": 1,
                    "col": 3,
                    "emoji": "🏰",
                    "active": True,   # always active
                },
                "right": {
                    "hp": 1500,
                    "row": 1,
                    "col": width - 4,
                    "emoji": "🏰",
                    "active": True,
                },
                "king": {
                    "hp": 3000,
                    "row": 2,
                    "col": width // 2,
                    "emoji": "👑",
                    "active": False,  # activates when hit or a princess dies
                },
            },
            p2_id: {
                "left": {
                    "hp": 1500,
                    "row": height - 3,
                    "col": 3,
                    "emoji": "🏰",
                    "active": True,
                },
                "right": {
                    "hp": 1500,
                    "row": height - 3,
                    "col": width - 4,
                    "emoji": "🏰",
                    "active": True,
                },
                "king": {
                    "hp": 3000,
                    "row": height - 2,
                    "col": width // 2,
                    "emoji": "👑",
                    "active": False,
                },
            },
        } if p1_id is not None and p2_id is not None else {}

    # -----------------------------------------------------
    # Basic grid helpers
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Generic placement (for units/buildings)
    # -----------------------------------------------------

    def place(self, row: int, col: int, obj: dict) -> bool:
        """
        Place an object on the grid.
        Returns True if successful.
        """
        if not self.is_empty(row, col):
            return False
        self.set(row, col, obj)
        return True

    # -----------------------------------------------------
    # Movement (1 tile)
    # -----------------------------------------------------

    def move(self, from_row: int, from_col: int, direction: Direction) -> bool:
        """
        Move an object 1 tile in a direction.
        Returns True if moved.
        """
        if not self.in_bounds(from_row, from_col):
            return False

        obj = self.get(from_row, from_col)
        if obj is None:
            return False

        d_row, d_col = 0, 0
        if direction == "up":
            d_row = -1
        elif direction == "down":
            d_row = 1
        elif direction == "left":
            d_col = -1
        elif direction == "right":
            d_col = 1

        to_row = from_row + d_row
        to_col = from_col + d_col

        if not self.is_empty(to_row, to_col):
            return False

        # Move the unit
        self.set(from_row, from_col, None)
        self.set(to_row, to_col, obj)
        return True

    # -----------------------------------------------------
    # Movement (multi-step, for fast units)
    # -----------------------------------------------------

    def move_steps(self, row: int, col: int,
                   direction: Direction, steps: int = 1) -> bool:
        """
        Move a unit multiple tiles (Hog Rider, Prince, etc.).
        Stops early if blocked.
        """
        for _ in range(steps):
            if not self.move(row, col, direction):
                return False

            # Update coordinates after each step
            if direction == "up":
                row -= 1
            elif direction == "down":
                row += 1
            elif direction == "left":
                col -= 1
            elif direction == "right":
                col += 1

        return True

    # -----------------------------------------------------
    # Utility
    # -----------------------------------------------------

    def all_positions(self) -> Iterator[Tuple[int, int, Optional[dict]]]:
        """Yield (row, col, obj) for every tile."""
        for r in range(self.height):
            for c in range(self.width):
                yield r, c, self.grid[r][c]

    def find_unit_position(self, unit_obj: dict) -> Optional[Tuple[int, int]]:
        """Return (row, col) of a specific unit object (by identity)."""
        for r in range(self.height):
            for c in range(self.width):
                if self.grid[r][c] is unit_obj:
                    return r, c
        return None

    # -----------------------------------------------------
    # Tower management
    # -----------------------------------------------------

    def place_towers_on_grid(self) -> None:
        """
        Inject tower objects into the grid before rendering.
        Called from visuals.render_arena_emoji().
        """
        if not self.towers:
            return

        for owner_id, tower_set in self.towers.items():
            for name, t in tower_set.items():
                if t["hp"] > 0:
                    self.grid[t["row"]][t["col"]] = {
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

        t["hp"] -= dmg
        if t["hp"] <= 0:
            t["hp"] = 0
            # Remove from grid
            self.grid[t["row"]][t["col"]] = None

            # If a princess dies => king activates
            if tower_name in ("left", "right"):
                self.towers[owner_id]["king"]["active"] = True

    def any_king_dead(self) -> Optional[int]:
        """
        Return owner_id of the dead king, or None if both alive.
        Used by Match.check_win().
        """
        if not self.towers:
            return None
        for owner_id, tower_set in self.towers.items():
            if tower_set["king"]["hp"] <= 0:
                return owner_id
        return None

