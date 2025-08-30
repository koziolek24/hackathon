from typing import List

from .Player import Player, Perspective, Command, Action
from .Poker import Poker


class Round:
    def __init__(self, poker: Poker, players: List[Player], small_blind: int = 10, big_blind: int = 20):
        self.poker = poker
        self.players = players
        self.round_number = 1
        self.bets = [0 for _ in players]
        self.max_bet = 0
        self.small_blind = small_blind
        self.big_blind = big_blind

    def bidding_run(self):
        perspective = Perspective(stack=[], stakes=sum(self.bets), action_log=[])

        for idx, player in enumerate(self.players):
            action_done: Action = player.accept(perspective)
            perspective.add_action(action_done)

            if action_done.command_type == Command.FOLD:
                # w tej wersji fold usuwa playera z rundy
                continue
            elif action_done.command_type in (Command.CALL, Command.ALL_IN):
                to_call = self.max_bet - self.bets[idx]
                if to_call < 0:
                    to_call = 0
                self.bets[idx] += to_call
            elif action_done.command_type == Command.RAISE:
                self.max_bet += action_done.raise_amount
                self.bets[idx] = self.max_bet

            perspective.stakes = sum(self.bets)
