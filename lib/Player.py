from enum import Enum

class Command(Enum):
    FOLD = "fold"
    CALL = "call"
    RAISE = "raise"
    ALL_IN = "all_in"

class Action:
    def __init__(self, command_type: Command, raise_amount: int = 0):
        self.command_type = command_type
        self.raise_amount = raise_amount

class PlayerType(Enum):
    SMALL_BLIND = "small_blind"
    BIG_BLIND = "big_blind"
    REGULAR = "regular"

class CardRank(Enum):
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "10"
    JACK = "J"
    QUEEN = "Q"
    KING = "K"
    ACE = "A"

    @property
    def value(self):
        rank_values = {
            CardRank.TWO: 2, CardRank.THREE: 3, CardRank.FOUR: 4, CardRank.FIVE: 5,
            CardRank.SIX: 6, CardRank.SEVEN: 7, CardRank.EIGHT: 8, CardRank.NINE: 9,
            CardRank.TEN: 10, CardRank.JACK: 11, CardRank.QUEEN: 12, CardRank.KING: 13,
            CardRank.ACE: 14
        }
        return rank_values[self]

class CardSuit(Enum):
    HEARTS = "hearts"
    DIAMONDS = "diamonds"
    CLUBS = "clubs"
    SPADES = "spades"

class Card:
    def __init__(self, rank: CardRank, suit: CardSuit):
        self.rank = rank
        self.suit = suit

    def __str__(self):
        return f"{self.rank.value}{self.suit.value}"

    def __repr__(self):
        return self.__str__()

class HandRank(Enum):
    HIGH_CARD = 1
    PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_A_KIND = 8
    STRAIGHT_FLUSH = 9
    ROYAL_FLUSH = 10

class HandEvaluation:
    def __init__(self, hand_rank: HandRank, value_cards: list, kicker_cards: list = None):
        self.hand_rank = hand_rank
        self.value_cards = value_cards  # Cards that form the hand (e.g., the pair, three of a kind)
        self.kicker_cards = kicker_cards or []  # Remaining cards for tiebreaking

    def __lt__(self, other):
        if self.hand_rank.value != other.hand_rank.value:
            return self.hand_rank.value < other.hand_rank.value

        # Compare value cards first
        for my_card, other_card in zip(self.value_cards, other.value_cards):
            if my_card != other_card:
                return my_card < other_card

        # Compare kickers
        for my_kicker, other_kicker in zip(self.kicker_cards, other.kicker_cards):
            if my_kicker != other_kicker:
                return my_kicker < other_kicker

        return False  # Hands are equal

    def __str__(self):
        return f"{self.rank.value}{self.suit.value}"

    def __repr__(self):
        return self.__str__()

class HandRank(Enum):
    HIGH_CARD = 1
    PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_A_KIND = 8
    STRAIGHT_FLUSH = 9
    ROYAL_FLUSH = 10

class HandEvaluation:
    def __init__(self, hand_rank: HandRank, value_cards: list, kicker_cards: list = None):
        self.hand_rank = hand_rank
        self.value_cards = value_cards  # Cards that form the hand (e.g., the pair, three of a kind)
        self.kicker_cards = kicker_cards or []  # Remaining cards for tiebreaking

    def __lt__(self, other):
        if self.hand_rank.value != other.hand_rank.value:
            return self.hand_rank.value < other.hand_rank.value

        # Compare value cards first
        for my_card, other_card in zip(self.value_cards, other.value_cards):
            if my_card != other_card:
                return my_card < other_card

        # Compare kickers
        for my_kicker, other_kicker in zip(self.kicker_cards, other.kicker_cards):
            if my_kicker != other_kicker:
                return my_kicker < other_kicker

        return False  # Hands are equal

class Perspective:
    def __init__(self, stack: list[Card], stakes: int, action_log: list[Action]):
        self.stack = stack
        self.stakes = stakes
        self.action_log = action_log

    def __len__(self):
        return len(self.action_log)

    def add_action(self, action: Action):
        self.action_log.append(action)

    def remove_first_action(self):
        self.action_log = self.action_log[1:]

class Hand:
    def __init__(self, cards: list[Card]):
        self.cards = cards

class RoundResult:
    def __init__(self, winner: str, pot: int, hands: list[Hand], isCardReset: bool = False):
        self.winner = winner
        self.pot = pot
        self.hands = hands
        self.isCardReset = isCardReset

class Player:
    def __init__(self, name: str, history: list[RoundResult], money: int, hand: Hand, perspective: Perspective):
        self.name = name
        self.history = history
        self.money = money
        self.hand = hand
        self.perspective_log = []
        self.perspective_log.append(perspective)

    def setHand(self, hand: Hand):
        self.hand = hand

    def accept(self, perspective: Perspective) -> Action:
        self.perspective_log.append(perspective)
        return self.play()

    def play(self) -> Action:
        # Implement the logic for the player to make a move
        return Action(Command.CALL)