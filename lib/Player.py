from enum import Enum
from typing import List


class Command(Enum):
    FOLD = "fold"
    CALL = "call"
    RAISE = "raise"
    ALL_IN = "all_in"


class Action:
    def __init__(self, command_type: Command, raise_amount: int = 0):
        self.command_type = command_type
        self.raise_amount = raise_amount

    def __repr__(self):
        return f"Action({self.command_type.name}, {self.raise_amount})"


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
    def pips(self) -> int:
        mapping = {
            CardRank.TWO: 2, CardRank.THREE: 3, CardRank.FOUR: 4, CardRank.FIVE: 5,
            CardRank.SIX: 6, CardRank.SEVEN: 7, CardRank.EIGHT: 8, CardRank.NINE: 9,
            CardRank.TEN: 10, CardRank.JACK: 11, CardRank.QUEEN: 12, CardRank.KING: 13,
            CardRank.ACE: 14
        }
        return mapping[self]


class CardSuit(Enum):
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"
    SPADES = "♠"


class Card:
    def __init__(self, rank: CardRank, suit: CardSuit):
        self.rank = rank
        self.suit = suit

    def __repr__(self):
        return f"{self.rank.value}{self.suit.value}"


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
    """
    value_cards: lista wartości (int) istotnych dla układu
    kicker_cards: pozostałe „kikery” malejąco
    """
    def __init__(self, hand_rank: HandRank, value_cards: List[int], kicker_cards: List[int] | None = None):
        self.hand_rank = hand_rank
        self.value_cards = value_cards
        self.kicker_cards = kicker_cards or []

    def key(self):
        return (self.hand_rank.value, self.value_cards, self.kicker_cards)

    def __lt__(self, other: "HandEvaluation"):
        return self.key() < other.key()

    def __repr__(self):
        return f"HandEvaluation({self.hand_rank.name}, {self.value_cards}, {self.kicker_cards})"


# lib/Player.py

class Perspective:
    def __init__(
        self,
        stack: List[Card],
        stakes: int,
        action_log: List[Action],
        board: List["Card"] | None = None,
        to_call: int = 0,
        max_bet: int = 0,
        min_raise: int = 0,
        position: int = 0
    ):
        self.stack = stack
        self.stakes = stakes
        self.action_log = action_log

        self.board = board or []
        ## Dodaję je teraz:
        self.to_call = to_call           # how much the player needs to call
        self.max_bet = max_bet           # current max bet
        self.min_raise = min_raise       # minimum allowed raise
        self.position = position         # player index


    def __len__(self):
        return len(self.action_log)

    def add_action(self, action: Action):
        self.action_log.append(action)

    def remove_first_action(self):
        if self.action_log:
            self.action_log = self.action_log[1:]


class Hand:
    def __init__(self, cards: List[Card]):
        self.cards = cards

    def __repr__(self):
        return f"Hand({self.cards})"


class RoundResult:
    def __init__(self, winner: str, pot: int, hands: List[Hand], isCardReset: bool = False):
        self.winner = winner
        self.pot = pot
        self.hands = hands
        self.isCardReset = isCardReset


class Player:
    def __init__(self, name: str, history: List[RoundResult], money: int, hand: Hand | None, perspective: Perspective):
        self.name = name
        self.history = history
        self.money = money
        self.hand = hand
        self.perspective_log: List[Perspective] = [perspective]

    def setHand(self, hand: Hand):
        self.hand = hand

    def accept(self, perspective: Perspective) -> Action:
        self.perspective_log.append(perspective)
        return self.play()

    def play(self) -> Action:
        # Placeholder, bot będzie tutaj grał
        return Action(Command.CALL)
