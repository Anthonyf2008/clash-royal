# game/storage.py

from __future__ import annotations
import json
import os
from typing import Dict, Any

from game.player import Player
from game.card import cards as CARD_DB

STORAGE_FILE = "players.json"

# Global players dict accessible everywhere
players: Dict[int, Player] = {}


# -----------------------------
# Helpers
# -----------------------------

def _int(v, default=0) -> int:
    try:
        return int(v)
    except Exception:
        return default

def _valid_card_list(lst) -> list[str]:
    """Keep only card names that exist in CARD_DB."""
    if not isinstance(lst, list):
        return []
    return [c for c in lst if isinstance(c, str) and c in CARD_DB]


# -----------------------------
# SAVE
# -----------------------------

def save_players() -> None:
    """
    Save the global players dict to a JSON file.
    Only saves persistent progression attributes.
    Uses atomic write to avoid corruption.
    """
    data: Dict[str, Any] = {}

    for uid, p in players.items():
        data[str(uid)] = {
            "cards": _valid_card_list(getattr(p, "cards", [])),
            "deck": _valid_card_list(getattr(p, "deck", [])),
            "coins": _int(getattr(p, "coins", 0)),
            "wins": _int(getattr(p, "wins", 0)),
            "trophies": _int(getattr(p, "trophies", 0)),
            "arena": _int(getattr(p, "arena", 1)),
        }

    tmp_file = STORAGE_FILE + ".tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    # Atomic replace
    os.replace(tmp_file, STORAGE_FILE)


# -----------------------------
# LOAD
# -----------------------------

def load_players() -> Dict[int, Player]:
    """
    Load players from JSON file into the global dict.
    If file is missing or corrupted, returns empty dict safely.
    """
    global players

    if not os.path.exists(STORAGE_FILE):
        players = {}
        return players

    try:
        with open(STORAGE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        players = {}
        return players

    if not isinstance(data, dict):
        players = {}
        return players

    players = {}

    for uid_str, p_data in data.items():
        uid = _int(uid_str, None)
        if uid is None:
            continue
        if not isinstance(p_data, dict):
            continue

        # Dummy user object (you can later replace display_name with real Discord user)
        user = type("User", (), {})()
        user.id = uid
        user.display_name = p_data.get("display_name") or f"User{uid}"

        unlocked = _valid_card_list(p_data.get("cards", []))
        if not unlocked:
            # fallback so Player always has something valid
            unlocked = ["knight", "archer", "giant", "mini_pekka", "hog_rider", "baby_dragon", "fireball", "zap"]
            unlocked = _valid_card_list(unlocked)

        p = Player(user, unlocked)

        deck = _valid_card_list(p_data.get("deck", []))
        # ensure deck cards are unlocked
        deck = [c for c in deck if c in p.cards]
        if len(deck) < 5:
            deck = p.cards[:8]

        p.deck = deck
        p.coins = _int(p_data.get("coins", 0))
        p.wins = _int(p_data.get("wins", 0))
        p.trophies = _int(p_data.get("trophies", 0))
        p.arena = max(1, _int(p_data.get("arena", 1)))

        players[uid] = p

    return players
