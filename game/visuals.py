# game/visuals.py
from __future__ import annotations

from typing import Optional, Dict, Any, List, Tuple
from .arena import Arena
import os
from PIL import Image
import asyncio


# ---------------------------------------------------------
# DECK IMAGE (unchanged behavior)
# ---------------------------------------------------------

def make_deck_image(card_files, output_file="deck.png"):
    valid_files = [f for f in card_files if os.path.exists(f)]
    if not valid_files:
        return None

    target_size = (300, 400)
    images = [Image.open(f).resize(target_size) for f in valid_files]

    w, h = target_size
    cols, rows = 4, 2

    deck = Image.new("RGBA", (w * cols, h * rows), (0, 0, 0, 0))

    for i, img in enumerate(images[:8]):
        x = (i % cols) * w
        y = (i // cols) * h
        deck.paste(img, (x, y))

    deck.save(output_file)
    return output_file


# ---------------------------------------------------------
# TILE → EMOJI
# ---------------------------------------------------------

def tile_to_emoji(tile: Optional[dict]) -> str:
    if tile is None:
        return "⬜"

    if not isinstance(tile, dict):
        return "❓"

    # Terrain-only tiles (spell animation frames, etc.)
    if "type" not in tile and "emoji" in tile:
        return tile["emoji"]

    # Towers
    if tile.get("type") == "tower":
        if tile.get("name") == "king":
            return tile.get("emoji", "👑")
        return tile.get("emoji", "🏰")

    # Units (or anything else dict-like)
    return tile.get("emoji", "❓")


# ---------------------------------------------------------
# HP BARS
# ---------------------------------------------------------

def _hp_ratio(current: int, max_hp: int) -> float:
    if max_hp <= 0:
        return 0.0
    return max(0.0, min(1.0, current / max_hp))


def hp_bar_3(current: int, max_hp: int) -> str:
    ratio = _hp_ratio(current, max_hp)

    if ratio == 0:
        return "⬛⬛⬛"
    if ratio > 0.66:
        return "🟩🟩🟩"
    if ratio > 0.33:
        return "🟨🟨⬛"
    return "🟥⬛⬛"


def hp_bar_unit(current: int, max_hp: int) -> str:
    ratio = _hp_ratio(current, max_hp)
    if ratio == 0:
        return "⬛⬛"
    if ratio > 0.5:
        return "🟩🟩"
    if ratio > 0.25:
        return "🟨⬛"
    return "🟥⬛"


# ---------------------------------------------------------
# TOWER HP SUMMARY LINES
# ---------------------------------------------------------

def collect_tower_hp_lines(arena: Arena) -> list[str]:
    if not arena.towers:
        return []

    lines: list[str] = []

    p1_id = arena.p1_id
    p2_id = arena.p2_id

    def one_side(owner_id: int, label: str) -> str:
        tset: Dict[str, Dict[str, Any]] = arena.towers.get(owner_id, {})
        left = tset.get("left")
        right = tset.get("right")
        king = tset.get("king")

        def bar_or_empty(t: Optional[Dict[str, Any]], base_max: int) -> str:
            if not t:
                return "⬛⬛⬛"
            return hp_bar_3(int(t.get("hp", 0) or 0), base_max)

        return (
            f"{label} "
            f"L{bar_or_empty(left, 1500)} "
            f"K{bar_or_empty(king, 3000)} "
            f"R{bar_or_empty(right, 1500)}"
        )

    if p1_id is not None:
        lines.append(one_side(p1_id, "P1"))
    if p2_id is not None:
        lines.append(one_side(p2_id, "P2"))

    return lines


# ---------------------------------------------------------
# ELIXIR / ENERGY BARS
# ---------------------------------------------------------

def elixir_bar(current: int, max_elixir: int = 10) -> str:
    current = max(0, min(max_elixir, int(current)))
    return "🔮" * current + "⚫" * (max_elixir - current)


def collect_elixir_lines(match) -> list[str]:
    """
    Your Player currently uses energy, not elixir.
    We'll display energy as "Elixir" on-screen.
    """
    lines: list[str] = []
    for idx, p in enumerate(getattr(match, "players", []), start=1):
        value = getattr(p, "energy", getattr(p, "elixir", 0))
        lines.append(f"P{idx} Elixir: {elixir_bar(value)}")
    return lines


# ---------------------------------------------------------
# BUILD A TEMP GRID WITH TOWERS OVERLAID (NO STATE MUTATION)
# ---------------------------------------------------------

def _grid_with_towers(arena: Arena) -> list[list[Optional[dict]]]:
    """
    Returns a new grid that is arena.grid + tower markers overlaid.
    Does NOT modify arena.grid.
    """
    grid = [[arena.get(r, c) for c in range(arena.width)] for r in range(arena.height)]

    if not arena.towers:
        return grid

    for owner_id, tower_set in arena.towers.items():
        for name, t in tower_set.items():
            if int(t.get("hp", 0) or 0) <= 0:
                continue
            for (r, c) in t.get("cells", []):
                if arena.in_bounds(r, c):
                    grid[r][c] = {
                        "type": "tower",
                        "owner": owner_id,
                        "name": name,
                        "emoji": t.get("emoji", "🏰"),
                    }

    return grid


# ---------------------------------------------------------
# EMOJI GRID RENDERING (Clash Royale style)
# ---------------------------------------------------------

def render_arena_emoji(arena: Arena, match: Optional[object] = None) -> str:
    LEFT_PAD = "   "

    DIGIT_BOX = {
        "0": "0️⃣", "1": "1️⃣", "2": "2️⃣", "3": "3️⃣", "4": "4️⃣",
        "5": "5️⃣", "6": "6️⃣", "7": "7️⃣", "8": "8️⃣", "9": "9️⃣",
    }

    def col_header() -> str:
        digits = [str((i + 1) % 10) for i in range(arena.width)]
        return LEFT_PAD + "".join(DIGIT_BOX[d] for d in digits)

    def row_prefix(r: int) -> str:
        return f"{chr(ord('A') + r)}  "

    # Use a temp grid that includes towers, without mutating arena state
    grid = _grid_with_towers(arena)

    lines: list[str] = []

    river_cols = [arena.width // 2 - 1, arena.width // 2]

    bridge_centers = [arena.height // 4, arena.height - arena.height // 4 - 1]
    bridge_rows = set()
    for br in bridge_centers:
        for rr in (br - 1, br, br + 1):
            if 0 <= rr < arena.height:
                bridge_rows.add(rr)

    lines.append(col_header())
    border = LEFT_PAD + ("🟦" * arena.width)
    lines.append(border)

    for r in range(arena.height):
        row_tiles: list[str] = []

        for c in range(arena.width):
            tile = grid[r][c]

            # Base terrain
            if c in river_cols:
                base = "🟦"
            else:
                base = "🟩" if c < river_cols[0] else "🟪"

            # Bridge override
            if (r in bridge_rows) and (c in river_cols):
                base = "🟫"

            # Overlay unit/tower
            if tile is not None:
                base = tile_to_emoji(tile)

            row_tiles.append(base)

        lines.append(row_prefix(r) + "".join(row_tiles))

    lines.append(border)

    tower_hp_lines = collect_tower_hp_lines(arena)
    if tower_hp_lines:
        lines.append("")
        lines.extend(tower_hp_lines)

    if match is not None:
        elixir_lines = collect_elixir_lines(match)
        if elixir_lines:
            lines.append("")
            lines.extend(elixir_lines)

    return "```text\n" + "\n".join(lines) + "\n```"


def render_arena_ascii(arena: Arena) -> str:
    lines: list[str] = []

    border = "+" + ("-" * arena.width) + "+"
    lines.append(border)

    for r in range(arena.height):
        row_chars = []
        for c in range(arena.width):
            tile = arena.get(r, c)
            row_chars.append("." if tile is None else "X")
        lines.append("|" + "".join(row_chars) + "|")

    lines.append(border)

    return "```text\n" + "\n".join(lines) + "\n```"


# ---------------------------------------------------------
# SPELL ANIMATION (NO PERMANENT GRID MUTATION)
# ---------------------------------------------------------

async def animate_spell(ctx, arena: Arena, match, positions, effect: str):
    """
    Flash spell emojis on top of the rendered board.
    This temporarily overrides arena.grid for rendering only, then restores it.
    """
    # Snapshot current grid once
    base = [[arena.get(r, c) for c in range(arena.width)] for r in range(arena.height)]

    frames = []

    # Frame 1: flash effect
    temp = [[base[r][c] for c in range(arena.width)] for r in range(arena.height)]
    for r, c in positions:
        if arena.in_bounds(r, c):
            temp[r][c] = {"emoji": effect}
    frames.append(temp)

    # Frame 2: restore
    frames.append(base)

    for grid in frames:
        old = arena.grid
        arena.grid = grid
        await ctx.send(render_arena_emoji(arena, match))
        arena.grid = old
        await asyncio.sleep(0.3)

