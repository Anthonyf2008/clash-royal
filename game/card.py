# game/card.py

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
        self.hp = data.get("hp", 50)              # NEW: default HP
        self.range = data.get("range", 1)         # NEW: attack range
        self.speed = data.get("speed", 1)         # NEW: movement speed
        self.special = data.get("special", "")
        self.emoji = data.get("emoji", "🤺")      # NEW: emoji for grid
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

    def create_unit(self, owner_id: int):
        """
        Convert this card into a unit object for the grid.
        Buildings and troops both use this.
        Spells do NOT create units.
        """
        return {
            "name": self.name,
            "type": self.type,
            "owner": owner_id,
            "hp": self.hp,
            "damage": self.damage,
            "range": self.range,
            "speed": self.speed,
            "special": self.special,
            "emoji": self.emoji,
        }

    def __str__(self):
        return f"{self.name} (Cost: {self.cost})"


# ---------------------------------------------------------
# CARD DATABASE (updated for grid-based combat)
# ---------------------------------------------------------

cards = {
    # Troops
    "knight": {
        "type": "troop", "cost": 3, "damage": 10, "hp": 120,
        "emoji": "🤺"
    },
    "archer": {
        "type": "troop", "cost": 3, "damage": 8, "hp": 60,
        "range": 3, "emoji": "🏹"
    },
    "giant": {
        "type": "troop", "cost": 5, "damage": 20, "hp": 200,
        "emoji": "🧱"
    },
    "valkyrie": {
        "type": "troop", "cost": 4, "damage": 15, "hp": 150,
        "special": "splash", "emoji": "🪓"
    },
    "musketeer": {
        "type": "troop", "cost": 4, "damage": 18, "hp": 80,
        "range": 4, "emoji": "🔫"
    },
    "mini_pekka": {
        "type": "troop", "cost": 4, "damage": 30, "hp": 90,
        "emoji": "🤖"
    },
    "baby_dragon": {
        "type": "troop", "cost": 4, "damage": 20, "hp": 100,
        "special": "flying splash", "emoji": "🐉"
    },
    "skeletons": {
        "type": "troop", "cost": 1, "damage": 5, "hp": 20,
        "special": "swarm", "emoji": "💀"
    },
    "bomber": {
        "type": "troop", "cost": 3, "damage": 12, "hp": 50,
        "special": "splash", "emoji": "💣"
    },
    "witch": {
        "type": "troop", "cost": 5, "damage": 15, "hp": 100,
        "special": "spawns skeletons", "emoji": "🧙‍♀️"
    },
    "prince": {
        "type": "troop", "cost": 5, "damage": 25, "hp": 120,
        "special": "charge", "speed": 2, "emoji": "🐎"
    },
    "dark_prince": {
        "type": "troop", "cost": 4, "damage": 20, "hp": 110,
        "special": "splash charge", "speed": 2, "emoji": "⚔️"
    },
    "hunter": {
        "type": "troop", "cost": 4, "damage": 22, "hp": 90,
        "emoji": "🔫"
    },
    "ice_spirit": {
        "type": "troop", "cost": 1, "damage": 5, "hp": 20,
        "special": "freeze", "emoji": "❄️"
    },
    "barbarians": {
        "type": "troop", "cost": 5, "damage": 20, "hp": 100,
        "special": "swarm", "emoji": "🗡️"
    },
    "wizard": {
        "type": "troop", "cost": 5, "damage": 20, "hp": 80,
        "special": "splash", "emoji": "🔥"
    },
    "minions": {
        "type": "troop", "cost": 3, "damage": 10, "hp": 40,
        "special": "flying", "emoji": "🦇"
    },
    "mega_minion": {
        "type": "troop", "cost": 3, "damage": 15, "hp": 60,
        "special": "flying", "emoji": "🛡️"
    },
    "golem": {
        "type": "troop", "cost": 8, "damage": 40, "hp": 250,
        "special": "death damage", "emoji": "🪨"
    },
    "guards": {
        "type": "troop", "cost": 3, "damage": 12, "hp": 50,
        "special": "shields", "emoji": "🛡️"
    },
    "hog_rider": {
        "type": "troop", "cost": 4, "damage": 30, "hp": 90,
        "special": "fast", "speed": 2, "emoji": "🐗"
    },
    "lava_hound": {
        "type": "troop", "cost": 7, "damage": 20, "hp": 200,
        "special": "flying spawns pups", "emoji": "🔥"
    },
    "miner": {
        "type": "troop", "cost": 3, "damage": 25, "hp": 70,
        "special": "spawn anywhere", "emoji": "⛏️"
    },
    "sparky": {
        "type": "troop", "cost": 6, "damage": 50, "hp": 120,
        "special": "charge blast", "emoji": "⚡"
    },
    "electro_wizard": {
        "type": "troop", "cost": 4, "damage": 20, "hp": 80,
        "special": "stun", "emoji": "⚡"
    },
    "royal_giant": {
        "type": "troop", "cost": 6, "damage": 25, "hp": 150,
        "range": 5, "emoji": "🏹"
    },
    "three_musketeers": {
        "type": "troop", "cost": 9, "damage": 18, "hp": 80,
        "special": "spawns 3", "emoji": "🔫"
    },

    # Buildings
    "cannon": {
        "type": "building", "cost": 3, "damage": 15, "hp": 120,
        "range": 3, "emoji": "🏰"
    },
    "inferno_tower": {
        "type": "building", "cost": 5, "damage": 35, "hp": 150,
        "special": "scales damage", "range": 4, "emoji": "🔥"
    },
    "furnace": {
        "type": "building", "cost": 4, "hp": 100,
        "special": "spawns fire spirits", "emoji": "🔥"
    },

    # Spells (grid-based)
    "fireball": {
        "type": "spell", "cost": 4, "damage": 25,
        "special": "3x3", "emoji": "💥"
    },
    "zap": {
        "type": "spell", "cost": 2, "damage": 15,
        "special": "stun", "emoji": "⚡"
    },
    "lightning": {
        "type": "spell", "cost": 6, "damage": 35,
        "special": "targets 3", "emoji": "⚡"
    },
    "rage": {
        "type": "spell", "cost": 2,
        "special": "buff", "emoji": "💢"
    },
    "tornado": {
        "type": "spell", "cost": 3,
        "special": "pull", "emoji": "🌪️"
    },
    "freeze": {
        "type": "spell", "cost": 4,
        "special": "freeze", "emoji": "❄️"
    },
    "poison": {
        "type": "spell", "cost": 4, "damage": 20,
        "special": "aoe", "emoji": "☠️"
    },
    "goblin_barrel": {
        "type": "spell", "cost": 3,
        "special": "spawn goblins", "emoji": "🛢️"
    }
}
