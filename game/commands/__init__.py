# game/commands/__init__.py

def setup_all_commands(bot):
    from .deck_cmds import setup_deck_cmds
    from .player_cmds import setup_player_cmds
    from .match_cmds import setup_match_cmds

    setup_deck_cmds(bot)
    setup_player_cmds(bot)
    setup_match_cmds(bot)
