enum Command:
    FOLD = "fold"
    CALL = "call"
    RAISE = "raise"
    ALL_IN = "all_in"

class Action:
    def __init__(self, command_type: Command, raise_amount: int = 0):
        self.command_type = command_type
        self.raise_amount = raise_amount

enum PlayerType:
    SMALL_BLIND = "small_blind"
    BIG_BLIND = "big_blind"
    REGULAR = "regular"

enum CardRank:
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

enum CardSuit:
    HEARTS = "hearts"
    DIAMONDS = "diamonds"
    CLUBS = "clubs"
    SPADES = "spades"

class Card:
    def __init__(self, rank: CardRank, suit: CardSuit):
        self.rank = rank
        self.suit = suit

class Perspective:
    def __init__(self, stack: list[Card], stakes: list[int], command_log: list[Command]):
        self.stack = stack
        self.stakes = stakes
        self.command_log = command_log

class Hand:
    def __init__(self, cards: list[Card]):
        self.cards = cards

class RoundResult:
    def __init__(self, winner: string, pot: int, hands: list[Hand], isCardReset: bool = False):
        self.winner = winner
        self.pot = pot
        self.hands = hands
        self.isCardReset = isCardReset

class Player:
    def __init__(self, name: string, history: list[RoundResult], money: int, hand: Hand, perspective: Perspective):
        self.name = name
        self.history = history
        self.money = money
        self.hand = hand
        self.perspective_log = list()
        self.perspective_log.append(perspective)

    def accept(self, perspective: Perspective) -> Action:
        self.perspective_log.append(perspective)
        return self.play()

    def play(self) -> Action:
        # Implement the logic for the player to make a move
        return Action(Command.CALL)