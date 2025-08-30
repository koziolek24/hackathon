from Player import Card, CardRank, CardSuit, Hand, HandRank, HandEvaluation, Player, Perspective
import numpy as np
from collections import Counter
from itertools import combinations
from typing import List

class Round:
    def __init__(self, poker: Poker, players: List[Player]):
        self.poker = poker
        self.players = players
        self.roundNumber = 1
        self.bets = []
        self.max_bet = 0


    def bidding_run(self):
        # wszyscy mają minimum jedną akcję
        # wszyscy postawili tyle samo albo foldowali
        while True:
            perspective = Perspective([], 0, [])
            for player in self.players:
                action_done = player.accept(perspective)
                # verify if action is valid
                perspective.add_action(action_done)
                if action_done == Command.RAISE:
                    self.bets.append(player.raise_amount)
                    self.max_bet = max(self.max_bet, player.raise_amount)
                if action_done == Command.CALL:
                    self.bets.append(self.max_bet)
                perspective.stakes += player.raise_amount
                if len(perspective) > len(self.players):
                    perspective.remove_first_action()
            if all(action.command_type in perspective.action_log for action in self.players if action.command_type == Command.FOLD or all(bet == self.bets[0] for bet in self.bets)):
                break

    def evaluateRound(self):
        pass