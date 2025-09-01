# cfrplus.py
# CFR+ kompatybilny z obecnym silnikiem — bez modyfikacji silnika gry
# ---------------------------------------------------------------
# Założenia:
# 1) W pełni zvibecodowany

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import math
import random
import pickle

# Reużyjemy typów tylko w miejscu integracji z Piwo1, aby nie zależeć twardo od lib.*
try:
    from lib.Player import Action, Command, Card, CardRank, CardSuit, Hand
    from lib.Poker import Poker
except Exception:
    Action = object  # type: ignore
    Command = object  # type: ignore
    Card = object  # type: ignore
    CardRank = object  # type: ignore
    CardSuit = object  # type: ignore
    Hand = object  # type: ignore
    Poker = object  # type: ignore

# ---------- Abstrakcja akcji ----------

ACTION_FOLD = 0
ACTION_CALL = 1
ACTION_RAISE_MIN = 2
ACTION_RAISE_2X = 3
ACTION_RAISE_3X = 4
ALL_ACTIONS = [ACTION_FOLD, ACTION_CALL, ACTION_RAISE_MIN, ACTION_RAISE_2X, ACTION_RAISE_3X]
N_ACTIONS = len(ALL_ACTIONS)

def action_label(a: int) -> str:
    return ["F","C","Rmin","R2x","R3x"][a]

# ---------- Klucz infosetu ----------

@dataclass(frozen=True)
class InfosetKey:
    street: int           # 0,3,4,5 (pre,flop,turn,river)
    pos: int              # 0/1
    tier: int             # 0=air,1=pair,2=top,3=two_plus
    fd: int               # 0/1
    to_call_bucket: int   # 0..3 (0=0, 1=<=1/3 pot, 2<=2/3, 3>2/3)
    history_code: int     # skompresowana historia akcji w tej ulicy (0..K)

# prosty kod historii: wewnątrzusticowy pojedynczy ruch przeciwnika: F,C,Rmin,R2x,R3x -> 0..4
# jeśli ruchu jeszcze nie było: 5
H_EMPTY = 5

# ---------- Węzeł CFR+ ----------

@dataclass
class CFRNode:
    regret: List[float] = field(default_factory=lambda: [0.0]*N_ACTIONS)
    strategy_sum: List[float] = field(default_factory=lambda: [0.0]*N_ACTIONS)

    def current_strategy(self, realization_weight: float) -> List[float]:
        # Regret-matching+
        pos = [max(r, 0.0) for r in self.regret]
        s = sum(pos)
        if s <= 1e-12:
            strat = [1.0/N_ACTIONS]*N_ACTIONS
        else:
            strat = [p/s for p in pos]
        # akumuluj do średniej
        for i in range(N_ACTIONS):
            self.strategy_sum[i] += realization_weight * strat[i]
        return strat

    def average_strategy(self) -> List[float]:
        s = sum(self.strategy_sum)
        if s <= 1e-12:
            return [1.0/N_ACTIONS]*N_ACTIONS
        return [x/s for x in self.strategy_sum]

# ---------- Narzędzia do bucketyzacji ----------

def street_from_board_len(n: int) -> int:
    if n==0: return 0
    if n==3: return 3
    if n==4: return 4
    return 5

# mapowanie z piwo1._postflop_tier
TIER_MAP = {"air":0, "pair":1, "top_pair":2, "two_pair_plus":3}

# ---------- ToyGame: symulacja rozdania jak obecny silnik ----------

@dataclass
class ToyState:
    player: int                 # kto na ruchu (0/1)
    board_len: int              # 0,3,4,5
    pos_in_street: int          # 0 lub 1 — bo każdy gra max raz na ulicę
    to_call: int
    min_raise: int
    pot: int
    history_code: int           # H_EMPTY gdy nikt jeszcze nie zagrał w tej ulicy
    tiers: Tuple[int,int]       # tiers obu graczy dla tej ulicy
    fds: Tuple[int,int]         # flush draw flags obu graczy
    street_order: List[int]     # kolejność ulic do przejścia (0->3->4->5)

class ToyGame:
    """Uproszczona gra zgodna z obecnym Round.bidding_run():
       - na każdej ulicy każdy gracz ma co najwyżej **jedną decyzję** w kolejności [0,1]
       - min_raise jest stałe i równe BB (param), raise to delta do max_bet
       - przechodzimy przez ulice preflop->flop->turn->river bez sub-pętli
       - fold kończy natychmiast (przeciwnik wygrywa pulę)
    """
    def __init__(self, big_blind: int = 20):
        self.big_blind = big_blind

    def initial_state(self) -> ToyState:
        # Preflop: SB=10, BB=20 w puli; na ruchu gracz 0 (SB)
        pot = 10 + 20
        return ToyState(player=0, board_len=0, pos_in_street=0,
                        to_call=0, min_raise=self.big_blind, pot=pot,
                        history_code=H_EMPTY, tiers=(0,0), fds=(0,0),
                        street_order=[0,3,4,5])

    def next_street(self, s: ToyState) -> Optional[ToyState]:
        order = s.street_order
        if s.board_len == order[-1]:
            return None  # river -> terminal (showdown)
        idx = order.index(s.board_len)
        nb = order[idx+1]
        # na nowej ulicy reset historii i to_call=0
        return ToyState(player=0, board_len=nb, pos_in_street=0,
                        to_call=0, min_raise=self.big_blind, pot=s.pot,
                        history_code=H_EMPTY, tiers=s.tiers, fds=s.fds,
                        street_order=order)

# ---------- CFR+ Trainer (outcome sampling w uproszczeniu) ----------

class CFRPlusTrainer:
    def __init__(self, rng_seed: int = 42, big_blind: int = 20):
        self.nodes: Dict[InfosetKey, CFRNode] = {}
        self.rng = random.Random(rng_seed)
        self.game = ToyGame(big_blind=big_blind)

    # --- Abstrakcja stanu do infosetu ---
    def make_key(self, s: ToyState) -> InfosetKey:
        street = s.board_len
        pos = s.player
        tier = s.tiers[pos]
        fd = s.fds[pos]
        # bucket to_call względem puli
        if s.to_call <= 0:
            tc = 0
        elif s.to_call <= s.pot/3:
            tc = 1
        elif s.to_call <= 2*s.pot/3:
            tc = 2
        else:
            tc = 3
        hist = s.history_code
        return InfosetKey(street, pos, tier, fd, tc, hist)

    def node(self, key: InfosetKey) -> CFRNode:
        n = self.nodes.get(key)
        if n is None:
            n = CFRNode()
            self.nodes[key] = n
        return n

    # --- Symulacja pojedynczego rozdania (abstr.) ---
    def play_hand(self) -> float:
        # Wylosuj cechy prywatne obu graczy na każdą ulicę (bardzo uproszczone):
        # preflop: tier=0 (ignorujemy siłę preflop w tej wersji), fd=0
        # flop/turn/river: tiers/fd losowane z rozkładu heur.
        tiers = [0,0]
        fds = [0,0]
        state = self.game.initial_state()
        state.tiers = (tiers[0], tiers[1])
        state.fds = (fds[0], fds[1])

        # prosty rozkład dla flop/turn/river, zastosujemy przy przejściu ulicy
        def sample_board_features():
            # w przybliżeniu: air ~50%, pair ~30%, top ~15%, 2p+ ~5%
            r = self.rng.random()
            if r < 0.50: t = 0
            elif r < 0.80: t = 1
            elif r < 0.95: t = 2
            else: t = 3
            fd = 1 if self.rng.random() < 0.12 else 0  # ~12% flush draw
            return t, fd

        # wartości wygranej na showdown (bardzo uproszczone): im wyższy tier, tym większa EV
        SHOWDOWN_VALUE = [0.0, 0.5, 1.0, 1.5]  # air/pair/top/2p+

        pot = state.pot
        max_bet = 50  # BB
        last_op_action = H_EMPTY

        total_utility = 0.0
        folded = False

        for board_len in state.street_order:
            if board_len == 0:
                # preflop: nic nie zmieniamy w tierach
                pass
            else:
                tiers[0], fds[0] = sample_board_features()
                tiers[1], fds[1] = sample_board_features()
            state.board_len = board_len
            state.tiers = (tiers[0], tiers[1])
            state.fds = (fds[0], fds[1])
            state.to_call = 0
            state.history_code = H_EMPTY
            last_op_action = H_EMPTY

            # jednorundowa sekwencja decyzji: gracz0, potem gracz1
            for turn in [0,1]:
                state.player = turn
                key = self.make_key(state)
                node = self.node(key)
                strat = node.current_strategy(1.0)
                a = self.sample_action(strat)

                # mapowanie na zmiany puli i to_call zgodne z uproszczonym silnikiem
                if a == ACTION_FOLD:
                    folded = True
                    # przeciwnik wygrywa aktualny pot; z perspektywy P0 utility dodatnie jeśli foldował P1
                    total_utility = (pot if turn==1 else -pot)
                    return total_utility
                elif a == ACTION_CALL:
                    # dopłata do_call (u nas to_call==0 prawie zawsze w tym modelu)
                    pot += state.to_call
                    state.to_call = 0
                    last_op_action = ACTION_CALL
                elif a in (ACTION_RAISE_MIN, ACTION_RAISE_2X, ACTION_RAISE_3X):
                    mult = {ACTION_RAISE_MIN:1, ACTION_RAISE_2X:2, ACTION_RAISE_3X:3}[a]
                    delta = mult * state.min_raise
                    max_bet += delta
                    pot += delta
                    state.to_call = 0 if turn==1 else delta  # drugi musi dopłacić
                    last_op_action = a

                # zaktualizuj regret na podstawie przybliżonego natychmiastowego cfv
                # (tu stosujemy bardzo uproszczone oszacowanie na podstawie tierów)
                # Idea: wartość akcji ~ (nasza siła - koszt), by kierować learning w stronę sensownych betów
                my_tier = tiers[turn]
                opp_tier = tiers[1-turn]
                strength_edge = SHOWDOWN_VALUE[my_tier] - SHOWDOWN_VALUE[opp_tier]
                cost = 0.0
                if a == ACTION_RAISE_MIN: cost = 0.1
                if a == ACTION_RAISE_2X: cost = 0.2
                if a == ACTION_RAISE_3X: cost = 0.35
                instant_value = strength_edge - cost

                # wyznacz counterfactual values dla wszystkich akcji przez heurystykę
                cf_values = [instant_value for _ in range(N_ACTIONS)]
                # FOLD ma bardzo niską wartość, chyba że jesteśmy słabsi
                cf_values[ACTION_FOLD] = -0.6 + (-strength_edge)
                # CALL ma mały koszt
                cf_values[ACTION_CALL] = strength_edge - 0.05
                # raises już ustawione przez cost powyżej

                best = max(cf_values)
                for i in range(N_ACTIONS):
                    node.regret[i] = max(0.0, node.regret[i] + (cf_values[i] - cf_values[a]))

            # koniec ulicy — przejście do następnej
            # (w modelu zawsze przechodzimy, bo nie ma pętli kontynuacyjnych)

        # showdown po riverze
        # przybliżona wartość = różnica siły * pot-multiplier
        final_edge = SHOWDOWN_VALUE[tiers[0]] - SHOWDOWN_VALUE[tiers[1]]
        total_utility = final_edge * 10.0  # skala
        return total_utility

    def sample_action(self, strat: List[float]) -> int:
        r = self.rng.random()
        acc = 0.0
        for i,p in enumerate(strat):
            acc += p
            if r <= acc:
                return i
        return N_ACTIONS-1

    def train(self, iterations: int = 100000):
        for _ in range(iterations):
            self.play_hand()

    def save(self, path: str):
        with open(path, "wb") as f:
            pickle.dump(self.nodes, f)

    def load(self, path: str):
        with open(path, "rb") as f:
            self.nodes = pickle.load(f)

# ---------- Policy do użycia w Piwo1 ----------

class CFRPlusPolicy:
    def __init__(self, strategy_path: Optional[str] = None):
        self.nodes: Dict[InfosetKey, CFRNode] = {}
        if strategy_path:
            try:
                with open(strategy_path, "rb") as f:
                    self.nodes = pickle.load(f)
            except Exception:
                self.nodes = {}

    def _key_from_perspective(self, perspective, tier: int, fd: int) -> InfosetKey:
        street = street_from_board_len(len(perspective.board))
        pos = getattr(perspective, "position", 0) % 2
        pot = getattr(perspective, "stakes", 0)
        to_call = max(getattr(perspective, "to_call", 0), 0)
        if to_call <= 0:
            tc = 0
        elif to_call <= pot/3:
            tc = 1
        elif to_call <= 2*pot/3:
            tc = 2
        else:
            tc = 3
        hist = H_EMPTY  # silnik nie przekazuje nam historii streetu — trzymamy H_EMPTY
        return InfosetKey(street, pos, tier, fd, tc, hist)

    def _avg_strategy(self, key: InfosetKey) -> List[float]:
        node = self.nodes.get(key)
        if node is None:
            return [1.0/N_ACTIONS]*N_ACTIONS
        return node.average_strategy()

    def decide(self, perspective, tier: int, fd: int) -> Tuple[str, int]:
        key = self._key_from_perspective(perspective, tier, fd)
        strat = self._avg_strategy(key)
        # wybór argmax (eksploatacja). Możesz zmienić na sampling, jeśli chcesz losowości.
        a = max(range(N_ACTIONS), key=lambda i: strat[i])
        # mapowanie na (Command, raise_amount)
        to_call = max(getattr(perspective, "to_call", 0), 0)
        min_raise = max(getattr(perspective, "min_raise", 0), 0)
        if a == ACTION_FOLD and to_call == 0:
            # zamieniamy FOLD na CHECK w sytuacji bez betu
            return ("CALL", 0)
        if a == ACTION_FOLD:
            return ("FOLD", 0)
        if a == ACTION_CALL:
            return ("CALL", 0)
        mult = {ACTION_RAISE_MIN:1, ACTION_RAISE_2X:2, ACTION_RAISE_3X:3}[a]
        return ("RAISE", mult * max(min_raise, 1))

# ---------------------------------------------------------------
# train_cfr.py — prosty skrypt treningowy
# ---------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--iters", type=int, default=200000)
    parser.add_argument("--out", type=str, default="cfrplus_strategy.pkl")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--bb", type=int, default=20)
    args = parser.parse_args()

    trainer = CFRPlusTrainer(rng_seed=args.seed, big_blind=args.bb)
    trainer.train(iterations=args.iters)
    trainer.save(args.out)
    print(f"Zapisano strategię do {args.out}")
