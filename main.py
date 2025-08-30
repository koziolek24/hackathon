from lib.Player import Player, Perspective
from lib.Poker import Poker
from lib.Round import Round
import logging
import os

def setup_logging():
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level_name, logging.INFO),
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )


if __name__ == "__main__":
    # Players creation
    p1 = Player(name="Alice", history=[], money=1000, hand=None, perspective=Perspective([], 0, []))
    p2 = Player(name="Bob", history=[], money=1000, hand=None, perspective=Perspective([], 0, []))
    players = [p1, p2]

    # Poker init
    poker = Poker(players)
    poker.initializeDeck()
    poker.dealCards()

    # First round
    rnd = Round(poker, players, small_blind=10, big_blind=20)

    # Preflop
    rnd.bidding_run()

    # Flop
    poker.burn(1)
    poker.addCards(3)
    rnd.bidding_run()

    # Turn
    poker.burn(1)
    poker.addCards(1)
    rnd.bidding_run()

    # River
    poker.burn(1)
    poker.addCards(1)
    rnd.bidding_run()

    # Showdown
    evals = []
    for pl in players:
        he = poker.evaluateHand(pl.hand)
        evals.append((pl, he))
        print(f"{pl.name} hand: {pl.hand.cards} | best: {he}")

    winner = max(evals, key=lambda t: t[1].key())
    print(f"\nWinner: {winner[0].name} with {winner[1].hand_rank.name}")
