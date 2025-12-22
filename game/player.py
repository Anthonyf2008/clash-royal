class Player:
    """
    Represents a player in the grid-based Clash Royale-style game.
    Handles elixir, cooldowns, deck, and progression.
    """

    def __init__(self, user, starter_cards, is_ai=False):
        self.user = user
        self.is_ai = is_ai

        # ---------------------------
        # Match stats (Elixir system)
        # ---------------------------
        self.energy = 5            # start at 5 elixir like Clash Royale
        self.max_energy = 10
        self.energy_regen = 1      # regen per turn

        # Cooldowns for cards
        self.cooldowns = {}  # {card_name: turns_remaining}

        # ---------------------------
        # Progression
        # ---------------------------
        self.cards = starter_cards.copy()   # unlocked cards
        self.deck = starter_cards.copy()    # active deck
        self.coins = 0
        self.wins = 0
        self.trophies = 0
        self.arena = 1

    # -----------------------------------------------------
    # Elixir (energy)
    # -----------------------------------------------------

    @property
    def elixir(self):
        """UI-friendly alias for energy."""
        return self.energy

    @property
    def max_elixir(self):
        return self.max_energy

    def regen_energy(self):
        """Regenerate elixir each turn."""
        self.energy = min(self.max_energy, self.energy + self.energy_regen)

    # -----------------------------------------------------
    # Cooldowns
    # -----------------------------------------------------

    def add_cooldown(self, card_name, turns=2):
        """Put a card on cooldown."""
        self.cooldowns[card_name] = turns

    def tick_cooldowns(self):
        """Reduce cooldown timers each turn."""
        for name in list(self.cooldowns.keys()):
            self.cooldowns[name] -= 1
            if self.cooldowns[name] <= 0:
                del self.cooldowns[name]

    # -----------------------------------------------------
    # Deck helpers
    # -----------------------------------------------------

    def has_card(self, card_name):
        return card_name in self.deck


# ---------------------------------------------------------
# PLAYER REGISTRY
# ---------------------------------------------------------

def get_player(user, players):
    """
    Retrieve or create a Player object for a Discord user.
    """
    if user.id not in players:
        starter = [
            "knight", "archer", "giant", "fireball",
            "valkyrie", "musketeer", "mini_pekka", "baby_dragon"
        ]
        p = Player(user, starter)
        p.deck = starter.copy()
        players[user.id] = p

    return players[user.id]


