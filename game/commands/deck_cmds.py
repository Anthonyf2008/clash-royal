# game/commands/deck_cmds.py

from discord.ext import commands
from game.player import get_player
from game.card import cards
from game.visuals import make_deck_image
from game.storage import players   # ✅ import global players dict
import discord


def setup_deck_cmds(bot: commands.Bot):

    # ---------------------------------------------------------
    # BUILD / EDIT DECK
    # ---------------------------------------------------------
    @bot.command()
    async def deck_build(ctx, *card_names):
        player = get_player(ctx.author, players)

        # Validate deck size
        if len(card_names) < 5:
            await ctx.send("Deck must have at least 5 cards.")
            return
        if len(card_names) > 8:
            await ctx.send("Deck can have a maximum of 8 cards.")
            return

        # Validate card existence
        for c in card_names:
            if c not in cards:
                await ctx.send(f"❌ Unknown card: `{c}`")
                return

        # Validate unlocks
        if any(c not in player.cards for c in card_names):
            await ctx.send("❌ You tried to add cards you haven't unlocked yet.")
            return

        # ✅ Update deck
        player.deck = list(card_names)
        await ctx.send(f"✅ Deck updated: {', '.join(player.deck)}")

    # ---------------------------------------------------------
    # SHOW DECK (TEXT)
    # ---------------------------------------------------------
    @bot.command()
    async def deck(ctx):
        player = get_player(ctx.author, players)
        if not player.deck:
            await ctx.send("⚠️ No deck set. Use `!deck_build` first.")
            return

        await ctx.send(f"📦 Your deck: {', '.join(player.deck)}")

    # ---------------------------------------------------------
    # SHOW DECK (IMAGE)
    # ---------------------------------------------------------
    @bot.command()
    async def deck_show(ctx):
        player = get_player(ctx.author, players)
        if not player.deck:
            await ctx.send("⚠️ No deck set. Use `!deck_build` first.")
            return

        # Collect image paths
        card_files = []
        for c in player.deck:
            if c in cards and "image" in cards[c]:
                card_files.append(cards[c]["image"])

        deck_file = make_deck_image(card_files)

        if not deck_file:
            await ctx.send("⚠️ No images found for your deck.")
            return

        file = discord.File(deck_file, filename="deck.png")
        embed = discord.Embed(title=f"📦 {ctx.author.display_name}'s Deck")
        embed.set_image(url="attachment://deck.png")

        await ctx.send(file=file, embed=embed)
