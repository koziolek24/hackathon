import logging
from typing import List
from lib.Player import Player, Action, Command, Card, CardRank

log = logging.getLogger(__name__)

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

def _preflop_score(hole: List[Card]) -> int:
    r1, r2 = hole[0].rank.pips, hole[1].rank.pips
    suited = hole[0].suit == hole[1].suit
    pair = r1 == r2
    hi, lo = (r1, r2) if r1 >= r2 else (r2, r1)
    connected = abs(r1 - r2) == 1

    s = 0
    if pair: s += 6 + (hi >= CardRank.TEN.pips)
    if hi >= CardRank.ACE.pips: s += 3
    if hi >= 13: s += 2
    if lo >= 10: s += 1
    if suited: s += 1
    if connected: s += 1
    return s

def _postflop_tier(hole: List[Card], board: List[Card]) -> str:
    if not board:
        return "air"

    all_cards = hole + board
    counts = _rank_counts(all_cards)

    if any(v >= 3 for v in counts.values()):
        return "two_pair_plus"

    pair_vals = [r for r, v in counts.items() if v >= 2]
    if len(pair_vals) >= 2:
        return "two_pair_plus"

    if pair_vals:
        board_top = max(c.rank.pips for c in board)
        hole_pair = hole[0].rank.pips == hole[1].rank.pips
        overpair = hole_pair and (hole[0].rank.pips > board_top)
        top_pair = any(c.rank.pips == board_top for c in hole)
        if overpair or top_pair:
            return "top_pair"
        return "pair"

    return "air"

def _bet_delta_simple(street: str, min_raise: int) -> int:
    table = {"flop": 20, "turn": 30, "river": 40}
    return max(table.get(street, 20), min_raise)

def _has_flush_draw(hole: List[Card], board: List[Card]) -> bool:
    if len(board) < 3:
        return False
    suit_counts = {}
    for c in hole + board:
        suit_counts[c.suit] = suit_counts.get(c.suit, 0) + 1
    for suit, cnt in suit_counts.items():
        if cnt >= 4 and any(h.suit == suit for h in hole):
            return True
    return False

class Piwo1(Player):
    _BB = 20

    def play(self) -> Action:
        p = self.perspective_log[-1]
        hole = self.hand.cards if self.hand else []
        board = p.board
        pot = p.stakes
        to_call = p.to_call
        min_raise = max(p.min_raise, self._BB)

        st = _street(len(board))
        log.debug("[Piwo1] %s | hole=%s | board=%s | pot=%d | to_call=%d | min_raise=%d",
                  st, hole, board, pot, to_call, min_raise)

        if st == "preflop":
            s = _preflop_score(hole)
            log.debug("[Piwo1] Preflop score=%d", s)

            if to_call == 0:
                if s >= 5:
                    a = Action(Command.RAISE, max(2 * self._BB, min_raise))
                    log.info("[Piwo1] Preflop open-raise: %s", a)
                    return a
                elif s >= 3:
                    a = Action(Command.CALL)
                    log.info("[Piwo1] Preflop limp/check: %s", a)
                    return a
                else:
                    log.info("[Piwo1] Preflop fold.")
                    return Action(Command.FOLD)

            if s >= 7:
                a = Action(Command.RAISE, max(3 * self._BB, min_raise))
                log.info("[Piwo1] Preflop 3-bet (value): %s", a)
                return a
            elif s >= 4:
                a = Action(Command.CALL)
                log.info("[Piwo1] Preflop call vs raise: %s", a)
                return a
            else:
                log.info("[Piwo1] Preflop fold vs raise.")
                return Action(Command.FOLD)

        tier = _postflop_tier(hole, board)
        has_fd = _has_flush_draw(hole, board)
        log.debug("[Piwo1] Postflop tier=%s | flush_draw=%s", tier, has_fd)

        if to_call == 0:
            if tier == "air":
                if has_fd and st in ("flop", "turn"):
                    a = Action(Command.RAISE, _bet_delta_simple(st, min_raise))
                    log.info("[Piwo1] %s semiblef (flush draw): %s", st, a)
                    return a
                log.info("[Piwo1] %s check (brak value).", st)
                return Action(Command.CALL)

            if tier == "pair":
                a = Action(Command.RAISE, _bet_delta_simple(st, min_raise))
                log.info("[Piwo1] %s value bet (para): %s", st, a)
                return a

            if tier == "top_pair":
                base = _bet_delta_simple(st, min_raise)
                a = Action(Command.RAISE, max(base, int(1.5 * base)))
                log.info("[Piwo1] %s value bet (top pair): %s", st, a)
                return a

            base = _bet_delta_simple(st, min_raise)
            a = Action(Command.RAISE, max(base, 2 * base))
            log.info("[Piwo1] %s value bet (two pair+): %s", st, a)
            return a

        if tier == "air":
            if has_fd and st in ("flop", "turn"):
                threshold = 0.6 * (pot + to_call)
                if to_call <= threshold:
                    log.info("[Piwo1] %s call (flush draw).", st)
                    return Action(Command.CALL)
            log.info("[Piwo1] %s fold vs bet (air).", st)
            return Action(Command.FOLD)

        if tier == "pair":
            if st == "river":
                log.info("[Piwo1] River fold (sama para bez top).")
                return Action(Command.FOLD)
            log.info("[Piwo1] %s call (para).", st)
            return Action(Command.CALL)

        if tier == "top_pair":
            log.info("[Piwo1] %s call (top pair).", st)
            return Action(Command.CALL)

        base = _bet_delta_simple(st, min_raise)
        a = Action(Command.RAISE, max(base, int(1.5 * base)))
        log.info("[Piwo1] %s raise (two pair+): %s", st, a)
        return a
