from Player import Card, CardRank, CardSuit, Hand, HandRank, HandEvaluation
import numpy as np
from collections import Counter
from itertools import combinations

class Game:
    def __init__(self):
        self._deck = []
        self._available_deck = []
        self._initialized = False
        self._community_cards = []

    def isInitialized(self):
        return self._initialized

    def initializeDeck(self):
        self._initialized = True
        self._available_deck = []
        for rank in CardRank:
            for suit in CardSuit:
                self._available_deck.append(Card(rank, suit))

    def addCards(self, num_cards=1):
        if len(self._available_deck) < num_cards:
            raise ValueError("Not enough cards in deck")

        for _ in range(num_cards):
            random_index = np.random.randint(0, len(self._available_deck))
            card = self._available_deck.pop(random_index)
            self._community_cards.append(card)

    def getCards(self):
        return self._community_cards

    def isFull(self):
        return len(self._community_cards) >= 5

    def deal(self):
        if not self.isInitialized():
            self.initializeDeck()

        if not self.isFull():
            cards_to_add = min(3, 5 - len(self._community_cards))
            self.addCards(cards_to_add)

        return self.getCards()

    def evaluateHand(self, player_hand: Hand) -> HandEvaluation:
        all_cards = player_hand.cards + self._community_cards

        if len(all_cards) < 5:
            raise ValueError("Need at least 5 cards to evaluate hand")

        best_hand = None

        for five_cards in combinations(all_cards, 5):
            hand_eval = self._evaluate_five_cards(list(five_cards))
            if best_hand is None or hand_eval.hand_rank.value > best_hand.hand_rank.value or \
               (hand_eval.hand_rank == best_hand.hand_rank and not (hand_eval < best_hand)):
                best_hand = hand_eval

        return best_hand

    def _evaluate_five_cards(self, cards: list[Card]) -> HandEvaluation:
        ranks = [card.rank.value for card in cards]
        suits = [card.suit for card in cards]

        rank_counts = Counter(ranks)
        suit_counts = Counter(suits)

        sorted_ranks = sorted(ranks, reverse=True)

        is_flush = len(suit_counts) == 1

        is_straight = self._is_straight(sorted_ranks)

        if is_flush and is_straight and sorted_ranks[0] == 14:
            return HandEvaluation(HandRank.ROYAL_FLUSH, sorted_ranks)

        if is_flush and is_straight:
            return HandEvaluation(HandRank.STRAIGHT_FLUSH, sorted_ranks)

        if 4 in rank_counts.values():
            four_kind = [rank for rank, count in rank_counts.items() if count == 4][0]
            kicker = [rank for rank, count in rank_counts.items() if count == 1][0]
            return HandEvaluation(HandRank.FOUR_OF_A_KIND, [four_kind], [kicker])

        if 3 in rank_counts.values() and 2 in rank_counts.values():
            three_kind = [rank for rank, count in rank_counts.items() if count == 3][0]
            pair = [rank for rank, count in rank_counts.items() if count == 2][0]
            return HandEvaluation(HandRank.FULL_HOUSE, [three_kind, pair])

        # Flush
        if is_flush:
            return HandEvaluation(HandRank.FLUSH, sorted_ranks)

        # Straight
        if is_straight:
            return HandEvaluation(HandRank.STRAIGHT, sorted_ranks)

        # Three of a Kind
        if 3 in rank_counts.values():
            three_kind = [rank for rank, count in rank_counts.items() if count == 3][0]
            kickers = sorted([rank for rank, count in rank_counts.items() if count == 1], reverse=True)
            return HandEvaluation(HandRank.THREE_OF_A_KIND, [three_kind], kickers)

        # Two Pair
        pairs = [rank for rank, count in rank_counts.items() if count == 2]
        if len(pairs) == 2:
            pairs.sort(reverse=True)
            kicker = [rank for rank, count in rank_counts.items() if count == 1][0]
            return HandEvaluation(HandRank.TWO_PAIR, pairs, [kicker])

        # Pair
        if 2 in rank_counts.values():
            pair = [rank for rank, count in rank_counts.items() if count == 2][0]
            kickers = sorted([rank for rank, count in rank_counts.items() if count == 1], reverse=True)
            return HandEvaluation(HandRank.PAIR, [pair], kickers)

        # High Card
        return HandEvaluation(HandRank.HIGH_CARD, [], sorted_ranks)

    def _is_straight(self, sorted_ranks):
        for i in range(4):
            if sorted_ranks[i] - sorted_ranks[i + 1] != 1:
                return False
        return True