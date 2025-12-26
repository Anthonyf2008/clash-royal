## game/card.py

from __future__ import annotations


class Card:
    """
    Represents a Clash Royale–style card for a grid-based game.
    Cards no longer deal direct tower damage.
    They create units, buildings, or spells that act on the grid.
    """

    def __init__(self, name: str, data: dict):
        if not data:
            raise ValueError(f"Card data missing for '{name}'")

        self.name = name
        self.type = data.get("type")              # troop | spell | building
        self.cost = data.get("cost", 0)
        self.damage = data.get("damage", 0)
        self.hp = data.get("hp", 50)
        self.range = data.get("range", 1)
        self.speed = data.get("speed", 1)
        self.special = data.get("special", "")
        self.emoji = data.get("emoji", "🤺")
        self.image = data.get("image", None)

    # ---------------------------------------------------------
    # Playability
    # ---------------------------------------------------------

    def can_play(self, player) -> bool:
        """Check if the player can play this card."""
        if self.cost > player.energy:
            return False
        if self.name in player.cooldowns:
            return False
        return True

    def apply_cost(self, player):
        """Deduct elixir cost."""
        player.energy -= self.cost

    # ---------------------------------------------------------
    # Grid-based unit creation
    # ---------------------------------------------------------


    def __str__(self):
        return f"{self.name} (Cost: {self.cost})"


# =========================================================
# CORE CARD SET (small on purpose while building the engine)
# =========================================================

CORE_CARD_NAMES = [
    # Troops
    "knight",
    "archer",
    "giant",
    "mini_pekka",
    "hog_rider",
    "baby_dragon",
    "skeletons",

    # Buildings
    "cannon",
    "inferno_tower",

    # Spells
    "fireball",
    "zap",
    "freeze",
]

# ---------------------------------------------------------
# CARD DATABASE (CORE 12)
# ---------------------------------------------------------

cards = {
    # Troops
    "knight": {
        "type": "troop", "cost": 3, "damage": 10, "hp": 120,
        "range": 1, "speed": 1, "emoji": "🤺"
    },
    "archer": {
        "type": "troop", "cost": 3, "damage": 8, "hp": 60,
        "range": 3, "speed": 1, "emoji": "🏹"
    },
    "giant": {
        "type": "troop", "cost": 5, "damage": 20, "hp": 200,
        "range": 1, "speed": 1, "emoji": "🧱"
    },
    "mini_pekka": {
        "type": "troop", "cost": 4, "damage": 30, "hp": 90,
        "range": 1, "speed": 1, "emoji": "🤖"
    },
    "hog_rider": {
        "type": "troop", "cost": 4, "damage": 30, "hp": 90,
        "range": 1, "speed": 2, "special": "fast", "emoji": "🐗"
    },
    "baby_dragon": {
        "type": "troop", "cost": 4, "damage": 20, "hp": 100,
        "range": 2, "speed": 1, "special": "flying", "emoji": "🐉"
    },
    "skeletons": {
        "type": "troop", "cost": 1, "damage": 5, "hp": 20,
        "range": 1, "speed": 1, "special": "swarm", "emoji": "💀"
    },

    # Buildings
    "cannon": {
        "type": "building", "cost": 3, "damage": 15, "hp": 120,
        "range": 3, "speed": 0, "emoji": "🏰"
    },
    "inferno_tower": {
        "type": "building", "cost": 5, "damage": 35, "hp": 150,
        "range": 4, "speed": 0, "special": "scales damage", "emoji": "🔥"
    },

    # Spells
    "fireball": {
        "type": "spell", "cost": 4, "damage": 25,
        "special": "3x3", "emoji": "💥"
    },
    "zap": {
        "type": "spell", "cost": 2, "damage": 15,
        "special": "stun", "emoji": "⚡"
    },
    "freeze": {
        "type": "spell", "cost": 4,
        "special": "freeze", "emoji": "❄️"
    },
}
