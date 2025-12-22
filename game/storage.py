# game/storage.py

import json
import os
from game.player import Player

STORAGE_FILE = "players.json"

# Global players dict accessible everywhere
players = {}


# ---------------------------------------------------------
# SAVE PLAYERS
# ---------------------------------------------------------

def save_players():
    """
    Save the global players dict to a JSON file.
    Only saves persistent progression attributes.
    """
    data = {}

    for uid, p in players.items():
        data[str(uid)] = {
            "cards": p.cards,
            "deck": p.deck,
            "coins": p.coins,
            "wins": p.wins,
            "trophies": p.trophies,
            "arena": p.arena
        }

    with open(STORAGE_FILE, "w") as f:
        json.dump(data, f, indent=4)


# ---------------------------------------------------------
# LOAD PLAYERS
# ---------------------------------------------------------

def load_players():
    """
    Load players from JSON file into the global dict.
    """
    global players

    if not os.path.exists(STORAGE_FILE):
        players = {}
        return players

    with open(STORAGE_FILE, "r") as f:
        data = json.load(f)

    players = {}

    for uid, p_data in data.items():
        # Create a dummy user object for Discord reference
        user = type("User", (), {})()
        user.id = int(uid)
        user.display_name = f"User{uid}"

        # Rebuild Player object
        p = Player(user, p_data["cards"])
        p.deck = p_data.get("deck", [])
        p.coins = p_data.get("coins", 0)
        p.wins = p_data.get("wins", 0)
        p.trophies = p_data.get("trophies", 0)
        p.arena = p_data.get("arena", 1)

        players[int(uid)] = p

    return players

