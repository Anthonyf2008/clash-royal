# game/storage.py

from __future__ import annotations

import json
import os
from typing import Dict, Any

from game.player import Player
from game.card import cards  # current card database


STORAGE_FILE = "players.json"

# Global players dict accessible everywhere
players: Dict[int, Player] = {}


# -------------------------
# Defaults (safe fallbacks)
# -------------------------

DEFAULT_UNLOCKED = ["knight", "archer", "giant", "mini_pekka", "fireball", "zap"]
DEFAULT_DECK = ["knight", "archer", "giant", "mini_pekka", "fireball"]


def _filter_valid_card_list(card_list):
    """Keep only cards that still exist in the current cards database."""
    if not isinstance(card_list, list):
        return []
    return [c for c in card_list if c in cards]


def _ensure_min_deck(deck):
    """Ensure deck has at least 5 valid cards."""
    deck = _filter_valid_card_list(deck)

    # remove duplicates but keep order
    seen = set()
    deduped = []
    for c in deck:
        if c not in seen:
            seen.add(c)
            deduped.append(c)
    deck = deduped

    # fill if too small
    for c in DEFAULT_DECK:
        if len(deck) >= 5:
            break
        if c not in deck and c in cards:
            deck.append(c)

    # last-resort: any existing card
    if len(deck) < 5:
        for c in cards.keys():
            if len(deck) >= 5:
                break
            if c not in deck:
                deck.append(c)

    return deck


def _ensure_unlocked_cards(unlocked, deck):
    """Ensure unlocked list contains at least the deck cards + defaults."""
    unlocked = _filter_valid_card_list(unlocked)

    # Make sure deck cards are unlocked
    for c in deck:
        if c not in unlocked:
            unlocked.append(c)

    # Make sure defaults exist too (nice for progression)
    for c in DEFAULT_UNLOCKED:
        if c in cards and c not in unlocked:
            unlocked.append(c)

    return unlocked


# ---------------------------------------------------------
# SAVE PLAYERS
# ---------------------------------------------------------

def save_players():
    """
    Save the global players dict to a JSON file.
    Only saves persistent progression attributes.
    """
    data: Dict[str, Any] = {}

    for uid, p in players.items():
        data[str(uid)] = {
            "cards": list(getattr(p, "cards", [])),
            "deck": list(getattr(p, "deck", [])),
            "coins": int(getattr(p, "coins", 0)),
            "wins": int(getattr(p, "wins", 0)),
            "trophies": int(getattr(p, "trophies", 0)),
            "arena": int(getattr(p, "arena", 1)),
        }

    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


# ---------------------------------------------------------
# LOAD PLAYERS
# ---------------------------------------------------------

def load_players():
    """
    Load players from JSON file into the global dict.
    Cleans old saves so removed cards don't break the bot.
    """
    global players
    players = {}

    if not os.path.exists(STORAGE_FILE):
        return players

    try:
        with open(STORAGE_FILE, "r", encoding="utf-8") as f:
            raw = f.read().strip()
            if not raw:
                return players
            data = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        # corrupted file => start fresh
        return players

    if not isinstance(data, dict):
        return players

    for uid_str, p_data in data.items():
        try:
            uid = int(uid_str)
        except (TypeError, ValueError):
            continue

        if not isinstance(p_data, dict):
            continue

        # Dummy user object for Discord reference (until real user loads)
        user = type("User", (), {})()
        user.id = uid
        user.display_name = p_data.get("display_name", f"User{uid}")

        unlocked = _filter_valid_card_list(p_data.get("cards", []))
        deck = _ensure_min_deck(p_data.get("deck", []))
        unlocked = _ensure_unlocked_cards(unlocked, deck)

        p = Player(user, unlocked)
        p.deck = deck

        p.coins = int(p_data.get("coins", 0))
        p.wins = int(p_data.get("wins", 0))
        p.trophies = int(p_data.get("trophies", 0))
        p.arena = int(p_data.get("arena", 1))

        players[uid] = p

    return players
