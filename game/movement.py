# game/movement.py
from __future__ import annotations

from game.combat import attack_unit, attack_tower


def step_movement(match) -> None:
    """
    Move units one step and trigger combat if blocked.
    Towers are copied unchanged.
    """
    arena = match.arena
    old_grid = arena.grid
    h, w = arena.height, arena.width

    new_grid = [[None for _ in range(w)] for _ in range(h)]

    # 1) Copy towers first (they never move)
    for r in range(h):
        for c in range(w):
            tile = old_grid[r][c]
            if isinstance(tile, dict) and tile.get("type") == "tower":
                new_grid[r][c] = tile

    # 2) Move units
    for r in range(h):
        for c in range(w):
            tile = old_grid[r][c]
            if not isinstance(tile, dict):
                continue
            if tile.get("type") == "tower":
                continue

            owner = tile.get("owner")
            if owner is None:
                continue

            # Direction: P1 → right, P2 → left
            direction = 1 if owner == arena.p1_id else -1
            nr, nc = r, c + direction

            # Out of bounds → stay
            if not arena.in_bounds(nr, nc):
                _stay(new_grid, r, c, tile)
                continue

            # Look ahead (prefer new_grid, fallback to old_grid)
            front = new_grid[nr][nc] or old_grid[nr][nc]

            # Empty → move
            if front is None:
                if new_grid[nr][nc] is None:
                    new_grid[nr][nc] = tile
                else:
                    _stay(new_grid, r, c, tile)
                continue

            # Tower → attack tower, stay
            if isinstance(front, dict) and front.get("type") == "tower":
                attack_tower(match, tile, front)
                _stay(new_grid, r, c, tile)
                continue

            # Unit → if enemy, attack, then stay
            if isinstance(front, dict) and front.get("type") != "tower":
                if front.get("owner") != owner:
                    # Materialize target into new_grid if needed
                    if new_grid[nr][nc] is None:
                        new_grid[nr][nc] = front
                    attack_unit(tile, nr, nc, new_grid)

                _stay(new_grid, r, c, tile)
                continue

            # Fallback → stay
            _stay(new_grid, r, c, tile)

    arena.grid = new_grid


def _stay(grid, r, c, tile) -> None:
    """Helper: keep unit in place if cell is free."""
    if grid[r][c] is None:
        grid[r][c] = tile
