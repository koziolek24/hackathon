# piwo1CFR.py
# Bot Piwo1 oparty o CFR+ — kompatybilny z obecnym silnikiem bez zmian

import logging
from typing import List
from lib.Player import Player, Action, Command, Card, CardRank
from cfrplus import CFRPlusPolicy, TIER_MAP

log = logging.getLogger(__name__)

# ===== POMOCNICZE (skopiowane minimalnie z piwo1, by nie mieć zależności) =====

def _street(board_len: int) -> str:
    if board_len == 0: return "preflop"
    if board_len == 3: return "flop"
    if board_len == 4: return "turn"
    return "river"


def _rank_counts(cards: List[Card]) -> dict[int, int]:
    counts = {}
    for c in cards:
        counts[c.rank.pips] = counts.get(c.rank.pips, 0) + 1
    return counts


def _postflop_tier(hole: List[Card], board: List[Card]) -> str:
    """
    'air' (brak pary), 'pair', 'top_pair' (w tym overpair), 'two_pair_plus' (2p+).
    Kopia logiki z piwo1.py, aby klasyfikacja była spójna z heurystyką.
    """
    if not board:
        return "air"

    all_cards = hole + board
    counts = _rank_counts(all_cards)

    # trips+ -> two_pair_plus
    if any(v >= 3 for v in counts.values()):
        return "two_pair_plus"

    # dwie różne pary wartości -> two_pair_plus
    pair_vals = [r for r, v in counts.items() if v >= 2]
    if len(pair_vals) >= 2:
        return "two_pair_plus"

    # jedna para: sprawdź top_pair/overpair
    if pair_vals:
        board_top = max(c.rank.pips for c in board)
        hole_pair = hole[0].rank.pips == hole[1].rank.pips
        overpair = hole_pair and (hole[0].rank.pips > board_top)
        top_pair = any(c.rank.pips == board_top for c in hole)
        if overpair or top_pair:
            return "top_pair"
        return "pair"

    return "air"


def _has_flush_draw(hole: List[Card], board: List[Card]) -> bool:
    """True, gdy mamy łącznie 4 karty w jednym kolorze i przynajmniej 1 nasza karta jest w tym kolorze."""
    if len(board) < 3:
        return False
    suit_counts = {}
    for c in hole + board:
        suit_counts[c.suit] = suit_counts.get(c.suit, 0) + 1
    for suit, cnt in suit_counts.items():
        if cnt >= 4 and any(h.suit == suit for h in hole):
            return True
    return False

# ===== BOT =====

class Piwo1CFR(Player):
    """
    Bot korzystający z policy CFR+ (średniej strategii) z pliku wygenerowanego przez cfrplus.py.
    Zwraca akcje kompatybilne z obecnym silnikiem:
      - RAISE interpretuje jako *delta* (Δ), używając wielokrotności `min_raise`.
      - FOLD przy to_call=0 zamieniany na CHECK (CALL bez dopłaty), by nie składać do pustej puli.
    """
    def __init__(self, *args, cfr_strategy_path: str | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._cfr = CFRPlusPolicy(cfr_strategy_path) if cfr_strategy_path else CFRPlusPolicy()

    def play(self) -> Action:
        p = self.perspective_log[-1]
        hole = self.hand.cards if self.hand else []
        board = p.board

        # Klasyfikacja siły ręki/układu zgodnie z piwo1
        tier_name = _postflop_tier(hole, board)
        tier = TIER_MAP.get(tier_name, 0)
        fd = 1 if _has_flush_draw(hole, board) else 0

        cmd, amount = self._cfr.decide(p, tier, fd)
        if cmd == "FOLD":
            return Action(Command.FOLD)
        if cmd == "CALL":
            return Action(Command.CALL)
        # RAISE: amount to delta zgodnie z silnikiem Round (self.max_bet += delta)
        return Action(Command.RAISE, amount)
