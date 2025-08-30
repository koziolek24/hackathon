from typing import List
from collections import Counter
from itertools import combinations

import numpy as np

from .Player import (
    Card, CardRank, CardSuit, Hand, HandRank, HandEvaluation, Player
)


class Poker:
    def __init__(self, players: List[Player]):
        self._available_deck: List[Card] = []
        self._initialized = False
        self._community_cards: List[Card] = []
        self._players = players

    def isInitialized(self):
        return self._initialized

    def initializeDeck(self):
        self._initialized = True
        self._available_deck = [Card(rank, suit) for rank in CardRank for suit in CardSuit]
        np.random.shuffle(self._available_deck)
        self._community_cards = []

    def dealCards(self):
        def drawCard():
            if not self._available_deck:
                raise ValueError("No cards left in the deck")
            return self._available_deck.pop()

        for player in self._players:
            player.setHand(Hand([drawCard() for _ in range(2)]))

    def burn(self, n=1):
        for _ in range(n):
            if self._available_deck:
                self._available_deck.pop()

    def addCards(self, num_cards=1):
        for _ in range(num_cards):
            if not self._available_deck:
                raise ValueError("Not enough cards in deck")
            self._community_cards.append(self._available_deck.pop())

    def getCards(self):
        return list(self._community_cards)

    def isFull(self):
        return len(self._community_cards) >= 5

    def evaluateHand(self, player_hand: Hand) -> HandEvaluation:
        all_cards = player_hand.cards + self._community_cards

        if len(all_cards) < 5:
            raise ValueError("Need at least 5 cards to evaluate hand")

        best_hand = None
        for five_cards in combinations(all_cards, 5):
            hand_eval = self._evaluate_five_cards(list(five_cards))
            if best_hand is None or best_hand < hand_eval:
                best_hand = hand_eval

        return best_hand

    def _evaluate_five_cards(self, cards: List[Card]) -> HandEvaluation:
        ranks = [c.rank.pips for c in cards]
        suits = [c.suit for c in cards]

        rank_counts = Counter(ranks)
        suit_counts = Counter(suits)

        sorted_ranks = sorted(ranks, reverse=True)
        is_flush = len(suit_counts) == 1
        straight_high = self._straight_high(sorted_ranks)

        # Royal / Straight Flush
        if is_flush and straight_high is not None:
            if straight_high == 14 and set(sorted_ranks) == {10, 11, 12, 13, 14}:
                return HandEvaluation(HandRank.ROYAL_FLUSH, [14, 13, 12, 11, 10], [])
            return HandEvaluation(
                HandRank.STRAIGHT_FLUSH,
                [straight_high, straight_high - 1, straight_high - 2, straight_high - 3, straight_high - 4],
                []
            )

        # Four of a kind
        if 4 in rank_counts.values():
            four = max([r for r, cnt in rank_counts.items() if cnt == 4])
            kicker = max([r for r, cnt in rank_counts.items() if cnt == 1])
            return HandEvaluation(HandRank.FOUR_OF_A_KIND, [four], [kicker])

        # Full house
        if 3 in rank_counts.values() and 2 in rank_counts.values():
            three = max([r for r, cnt in rank_counts.items() if cnt == 3])
            pair = max([r for r, cnt in rank_counts.items() if cnt == 2])
            return HandEvaluation(HandRank.FULL_HOUSE, [three, pair], [])

        # Flush
        if is_flush:
            return HandEvaluation(HandRank.FLUSH, sorted_ranks, [])

        # Straight
        if straight_high is not None:
            return HandEvaluation(
                HandRank.STRAIGHT,
                [straight_high, straight_high - 1, straight_high - 2, straight_high - 3, straight_high - 4],
                []
            )

        # Three of a kind
        if 3 in rank_counts.values():
            three = max([r for r, cnt in rank_counts.items() if cnt == 3])
            kickers = sorted([r for r, cnt in rank_counts.items() if cnt == 1], reverse=True)
            return HandEvaluation(HandRank.THREE_OF_A_KIND, [three], kickers)

        # Two pair
        pairs = sorted([r for r, cnt in rank_counts.items() if cnt == 2], reverse=True)
        if len(pairs) >= 2:
            pairs = pairs[:2]
            kicker = max([r for r, cnt in rank_counts.items() if cnt == 1])
            return HandEvaluation(HandRank.TWO_PAIR, pairs, [kicker])

        # Pair
        if 2 in rank_counts.values():
            pair = max([r for r, cnt in rank_counts.items() if cnt == 2])
            kickers = sorted([r for r, cnt in rank_counts.items() if cnt == 1], reverse=True)
            return HandEvaluation(HandRank.PAIR, [pair], kickers)

        # High card
        return HandEvaluation(HandRank.HIGH_CARD, [sorted_ranks[0]], sorted_ranks[1:])

    @staticmethod
    def _straight_high(sorted_desc_ranks: List[int]) -> int | None:
        """
        Zwraca najwyższą kartę strita w 5 kartach lub None.
        Obsługuje wheel (A-2-3-4-5): zwraca 5 jako high.
        """
        unique = sorted(set(sorted_desc_ranks), reverse=True)
        if len(unique) != 5:
            return None

        if all(unique[i] - 1 == unique[i + 1] for i in range(4)):
            return unique[0]

        if set(unique) == {14, 5, 4, 3, 2}:
            return 5
        return None
