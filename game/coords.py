# game/coords.py
def coord_to_rc(pos: str):
    pos = pos.strip().upper()
    if len(pos) < 2:
        return None

    row_char = pos[0]
    col_part = pos[1:]

    if not row_char.isalpha() or not col_part.isdigit():
        return None

    row = ord(row_char) - ord("A")
    col = int(col_part) - 1  # 1-based -> 0-based
    return row, col


def rc_to_coord(row: int, col: int) -> str:
    return f"{chr(ord('A') + row)}{col + 1}"
