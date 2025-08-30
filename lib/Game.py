from Player import Player, Perspective, Hand, RoundResult
from Card import Card
from typing import List, Callable
from Poker import Poker


class Game:
    def __init__(self, player_factories: List[Callable[[], Player]], pot_per_player: int):
        self.pot_per_player = pot_per_player
        self.player_factories = player_factories
        self.active_players = list(range(len(player_factories)))
        self.deck = []

    def start_round(self, player_amount):
        for i in player_amount:
            self.add_player(Player(f"Player {i}"))
        self.deck.shuffle()
        self.deal_cards()
        self.betting_round()

    def deal_cards(self):
        for player in self.players:
            player.hand.add_card(self.deck.draw_card())
            player.hand.add_card(self.deck.draw_card())

    def reveal_community_cards(self, amount):
        self.community_cards = []
        for _ in range(amount):
            self.community_cards.append(self.deck.draw_card())

    def betting_round(self):
        for player in self.players:
            player_bet = player.make_bet()
            self.pot += player_bet

    def end_round(self):
        self.showdown()
        self.reset()

    def showdown(self):
        # Determine the winner and distribute the pot
        pass

    def reset(self):
        self.deck = Deck()
        self.pot = 0
        for player in self.players:
            player.hand.clear()