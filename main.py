from lib.Player import Perspective, Player
from lib.Poker import Poker
from lib.Round import Round
from piwo1cfr import Piwo1CFR
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

def rotate(lst, k):
    k = k % len(lst)
    return lst[k:] + lst[:k]

if __name__ == "__main__":
    setup_logging()
    log = logging.getLogger("main")

    NUM_HANDS = int(os.getenv("NUM_HANDS", "1000"))
    SMALL_BLIND = 10
    BIG_BLIND = 20

    log.info("=== Start symulacji (%d rozdań) ===", NUM_HANDS)

    players_all = [
        Piwo1CFR(
            name="Piwo1_CFR",
            history=[], money=1000, hand=None,
            perspective=Perspective([], 0, []),
            cfr_strategy_path=os.getenv("CFR_PATH", "cfrplus_strategy.pkl"),
        ),
        Player(
            name="Tylko_call",
            history=[], money=1000, hand=None,
            perspective=Perspective([], 0, [])
        ),
        Piwo1(
            name="Piwo1",
            history=[], money=1000, hand=None,
            perspective=Perspective([], 0, [])
        )
    ]

    wins = {pl.name: 0 for pl in players_all}
    wins["ties"] = 0
    net_result = {pl.name: 0 for pl in players_all}

    N = len(players_all)
    assert N >= 2, "Potrzeba co najmniej dwóch graczy."

    for hand_idx in range(1, NUM_HANDS + 1):
        players = rotate(players_all, hand_idx - 1)

        btn = players[-1].name
        sb = players[0].name
        bb = players[1].name
        log.info("=== Hand #%d | BTN=%s, SB=%s, BB=%s ===", hand_idx, btn, sb, bb)

        poker = Poker(players)
        poker.initializeDeck()
        poker.dealCards()
        log.info("Karty rozdane graczom (szczegóły rąk w DEBUG).")

        rnd = Round(poker, players, small_blind=SMALL_BLIND, big_blind=BIG_BLIND)

        hand_pot = 0
        hand_contrib = {pl.name: 0 for pl in players}

        # --- Preflop ---
        log.info("— Preflop —")
        rnd.bidding_run()
        hand_pot += sum(rnd.bets)
        for i, pl in enumerate(players):
            hand_contrib[pl.name] += rnd.bets[i]

        # --- Flop ---
        log.info("— Flop —")
        poker.burn(1)
        poker.addCards(3)
        rnd.bidding_run()
        hand_pot += sum(rnd.bets)
        for i, pl in enumerate(players):
            hand_contrib[pl.name] += rnd.bets[i]

        # --- Turn ---
        log.info("— Turn —")
        poker.burn(1)
        poker.addCards(1)
        rnd.bidding_run()
        hand_pot += sum(rnd.bets)
        for i, pl in enumerate(players):
            hand_contrib[pl.name] += rnd.bets[i]

        # --- River ---
        log.info("— River —")
        poker.burn(1)
        poker.addCards(1)
        rnd.bidding_run()
        hand_pot += sum(rnd.bets)
        for i, pl in enumerate(players):
            hand_contrib[pl.name] += rnd.bets[i]

        # Showdown
        log.info("— Showdown —")
        evals = []
        for pl in players:
            he = poker.evaluateHand(pl.hand)
            evals.append((pl, he))
            log.debug("%s hand: %s | best: %s", pl.name, pl.hand.cards, he)

        best_key = max(evals, key=lambda t: t[1].key())[1].key()
        winners = [pl for (pl, he) in evals if he.key() == best_key]
        winning_rank_name = next(he.hand_rank.name for (pl, he) in evals if he.key() == best_key)

        if len(winners) == 1:
            w = winners[0]
            wins[w.name] += 1
            gained = hand_pot
            net_result[w.name] += gained - hand_contrib[w.name]
            for pl in players:
                if pl.name != w.name:
                    net_result[pl.name] -= hand_contrib[pl.name]
            msg = f"Winner: {w.name} with {winning_rank_name} | pot={hand_pot}"
        else:
            wins["ties"] += 1
            k = len(winners)
            base = hand_pot // k
            rem = hand_pot % k
            order = [p for p in players if p in winners]
            paid = {w.name: base + (1 if i < rem else 0) for i, w in enumerate(order)}
            for pl in players:
                got = paid.get(pl.name, 0)
                net_result[pl.name] += got - hand_contrib[pl.name]
            msg = "Remis między: " + ", ".join(w.name for w in winners) + f" (układ: {winning_rank_name}) | pot={hand_pot}"

        log.info(msg)

        step = max(1, NUM_HANDS // 10)
        if hand_idx % step == 0:
            scoreboard = ", ".join(f"{pl.name}={wins[pl.name]}" for pl in players_all)
            log.info("Postęp: %d/%d | %s | ties=%d",
                     hand_idx, NUM_HANDS, scoreboard, wins["ties"])

    print("\n=== Podsumowanie ===")
    print(f"Rozegrane rozdania: {NUM_HANDS}")
    for pl in players_all:
        w = wins[pl.name]
        pct = w / NUM_HANDS if NUM_HANDS else 0.0
        net = net_result[pl.name]
        bb100 = (100.0 * net / BIG_BLIND / NUM_HANDS) if NUM_HANDS else 0.0
        print(f"{pl.name}: wygrane={w} ({pct:.1%}), netto={net} złotych, bb/100={bb100:.2f}")
    t = wins["ties"]
    print(f"Remisy: {t} ({t/NUM_HANDS:.1%})")
