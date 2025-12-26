# game/coords.py
from __future__ import annotations
from typing import Optional, Tuple


def coord_to_rc(pos: str) -> Optional[Tuple[int, int]]:
    """
    Convert board coordinate like 'A1', 'C4' into (row, col).
    Returns None if invalid format.
    """
    if not pos:
        return None

    pos = pos.strip().upper()
    if len(pos) < 2:
        return None

    row_char = pos[0]
    col_part = pos[1:]

    if not row_char.isalpha() or not col_part.isdigit():
        return None

    row = ord(row_char) - ord("A")
    col = int(col_part) - 1  # 1-based -> 0-based

    if row < 0 or col < 0:
        return None

    return row, col


def rc_to_coord(row: int, col: int) -> str:
    """
    Convert (row, col) into board coordinate like 'A1'.
    """
    return f"{chr(ord('A') + row)}{col + 1}"
