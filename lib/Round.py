from typing import List
import logging

from .Player import Player, Perspective, Command, Action
from .Poker import Poker

log = logging.getLogger(__name__)

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
        board = self.poker.getCards()
        street = {0: "preflop", 3: "flop", 4: "turn"}.get(len(board), "river")

        self.max_bet = 0
        self.bets = [0 for _ in self.players]

        if street == "preflop":
            self.bets[0] = self.small_blind
            self.bets[1] = self.big_blind
            self.max_bet = self.big_blind
            log.info("Post blinds: %s(SB)=%d, %s(BB)=%d",
                     self.players[0].name, self.small_blind,
                     self.players[1].name, self.big_blind)

        log.info("Licytacja: %s | start: pot=%d, max_bet=%d", street, sum(self.bets), self.max_bet)

        for idx, player in enumerate(self.players):
            pot = sum(self.bets)
            board = self.poker.getCards()

            to_call = self.max_bet - self.bets[idx]
            if to_call < 0:
                to_call = 0

            min_raise = self.big_blind

            persp = Perspective(
                stack=[],
                stakes=pot,
                action_log=[],
                board=board,
                to_call=to_call,
                max_bet=self.max_bet,
                min_raise=min_raise,
                position=idx
            )

            log.info("Gracz %s: to_call=%d, pot=%d, max_bet=%d, bets=%s, board=%s",
                     player.name, to_call, pot, self.max_bet, self.bets, board)

            action_done: Action = player.accept(persp)
            log.info("Gracz %s zagrywa: %s", player.name, action_done)

            if action_done.command_type == Command.FOLD:
                log.info("Gracz %s folduje (bez zmiany stawek).", player.name)
                continue
            elif action_done.command_type in (Command.CALL, Command.ALL_IN):
                to_call_now = self.max_bet - self.bets[idx]
                if to_call_now < 0:
                    to_call_now = 0
                self.bets[idx] += to_call_now
                log.info("CALL/ALL_IN: %s dopłaca %d -> bets=%s (max_bet=%d)",
                         player.name, to_call_now, self.bets, self.max_bet)
            elif action_done.command_type == Command.RAISE:
                self.max_bet += action_done.raise_amount
                self.bets[idx] = self.max_bet
                log.info("RAISE: %s podbija o +%d -> max_bet=%d, bets=%s",
                         player.name, action_done.raise_amount, self.max_bet, self.bets)

        log.info("Koniec licytacji %s: pot=%d, max_bet=%d, bets=%s",
                 street, sum(self.bets), self.max_bet, self.bets)