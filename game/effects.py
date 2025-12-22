# game/effects.py

def apply_effect(card, player, opponent):
    """
    Applies special card effects.
    Supports single or multiple effects.
    """

    special = card.special
    if not special:
        return

    # Normalize to list
    specials = special if isinstance(special, list) else [special]

    for s in specials:
        if s == "freeze":
            # Opponent skips next turn
            opponent.cooldowns["frozen"] = 1

        elif s == "stun":
            # Opponent skips next turn (different label)
            opponent.cooldowns["stunned"] = 1

        elif s == "rage":
            # Boost energy
            player.energy = min(10, player.energy + 3)

        elif s == "swarm":
            # Extra chip damage
            opponent.tower_hp -= 5

        elif s == "death damage":
            # Extra damage on death
            opponent.tower_hp -= 10

        elif s == "heal":
            # Restore tower HP
            player.tower_hp = min(100, player.tower_hp + 10)

        elif s == "shield":
            # Reduce next damage (store flag in cooldowns)
            opponent.cooldowns["shielded"] = 1

        # Add more effects here as needed

        # Debugging/logging
        print(f"Effect applied: {s} by {player.user.display_name}")

