from lib.Player import Perspective
from lib.Poker import Poker
from lib.Round import Round
from piwo1 import Piwo1
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
    setup_logging()
    log = logging.getLogger("main")

    log.info("=== Start gry ===")

    # Players creation — ale zmieńcie na swoją nazwę botów, piwo1 wywalcie xD
    p1 = Piwo1(name="Alice", history=[], money=1000, hand=None, perspective=Perspective([], 0, []))
    p2 = Piwo1(name="Bob",   history=[], money=1000, hand=None, perspective=Perspective([], 0, []))
    players = [p1, p2]

    # Poker init
    poker = Poker(players)
    poker.initializeDeck()
    poker.dealCards()
    log.info("Karty rozdane graczom (szczegóły rąk w DEBUG).")

    # First round
    rnd = Round(poker, players, small_blind=10, big_blind=20)

    # Preflop
    log.info("— Preflop —")
    rnd.bidding_run()

    # Flop
    log.info("— Flop —")
    poker.burn(1)
    poker.addCards(3)
    rnd.bidding_run()

    # Turn
    log.info("— Turn —")
    poker.burn(1)
    poker.addCards(1)
    rnd.bidding_run()

    # River
    log.info("— River —")
    poker.burn(1)
    poker.addCards(1)
    rnd.bidding_run()

    # Showdown
    log.info("— Showdown —")
    evals = []
    for pl in players:
        he = poker.evaluateHand(pl.hand)
        evals.append((pl, he))
        log.info(f"{pl.name} hand: {pl.hand.cards} | best: {he}")
        print(f"{pl.name} hand: {pl.hand.cards} | best: {he}")

    winner = max(evals, key=lambda t: t[1].key())
    msg = f"Winner: {winner[0].name} with {winner[1].hand_rank.name}"
    log.info(msg)
    print(f"\n{msg}")