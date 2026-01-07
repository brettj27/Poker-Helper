import tkinter as tk
from tkinter import simpledialog
from dataclasses import dataclass
from math import cos, sin, pi
from typing import Optional
from collections import defaultdict
import random

# -=x=- Player Classes -=x=- (We sync them up when we need the UI to update states)

# This is the class for the game logic 

@dataclass
class GamePlayer:
    name: str
    stack: int
    bet: int = 0
    made_decision_this_round: bool = False
    in_hand: bool = True
    cards_hidden: bool = True  # hole cards not shown
    cards: tuple[str, str] = ("??", "??")
    last_action: Optional[str] = None # "check", "call", "raise", "fold"

# This is the class for the UI

@dataclass
class UIPlayer:
    name: str
    stack: int
    bet: int = 0
    in_hand: bool = True
    cards_hidden: bool = True  # hole cards not shown
    cards: tuple[str, str] = ("??", "??")
    last_action: Optional[str] = None # "check", "call", "raise", "fold"

RANKS = "23456789TJQKA"
SUITS = "cdhs"  # clubs, diamonds, hearts, spades

def card_to_str(card_id: int) -> str:
    """
    This function computes our assigned card IDs (0-51) to a string representing the card such as "Ah", which is the ace of hearts
    INPUTS:
        - card_id is the card ID value (an integer between [0, 51])
    OUTPUTS:
        - a string such as "Ah" representing the card
    """
    rank = RANKS[card_id % 13]
    suit = SUITS[card_id // 13]
    return f"{rank}{suit}"  # like "Ah", "7d", etc

def parse_cards(cards: list[str]) -> list[tuple[int,str]]:
        """
        This function parses a list of string representations of cards such as ["Ah", "Kh", "Jh"]
        to a sortable tuple in order to compute hand types (Two pair, etc)
        EX: "Ah" -> (14, "h")
        INPUTS:
            cards is a list of strings which are of the form "{RANK}{SUIT}"
        OUTPUTS:
            returns a list of tuples of the form (RANK IDX, "{SUIT}")
        """
        new_list = []
        for card in cards:
            rank = RANKS.index(card[0]) + 2
            suit = card[1]
            new_list.append((rank, suit))
        return new_list

def score_five(cards: list[tuple[int,str]]) -> tuple[int, tuple]:
    """
    This function scores a five-card hand of Texas Hold'em by returning
    a tuple representing the hand of the form (Type, Kickers)
    EX: Two pair with 9s and 8s with an Ace kicker -> (2, (9, 8, 14))
    Because 2 is the ID of two-pair, and 9, 8, 14 are the card ranks

    0: high card
    1: one pair
    2: two pair
    3: three of a kind
    4: straight
    5: flush
    6: full house
    7: four of a kind
    8: straight flush
    9: royal flush

    INPUTS:
        - a list of tuples of the form (RANK IDX, "{SUIT}")
    """

    if len(cards) != 5:
        return
    ranks = sorted((r for r, _ in cards), reverse=True)
    suits = [s for _, s in cards]
    flush = len(set(suits)) == 1
    straight = straight_high(ranks) # None if no straight exists
    four_o_a_k = four_of_a_kind(get_pairs(ranks))
    full_h = full_house(get_pairs(ranks))
    three_o_a_k = three_of_a_kind(get_pairs(ranks))
    two_p = two_pair(get_pairs(ranks))
    one_p = one_pair(get_pairs(ranks))

    if straight == 14 and flush == True:
        return (9, ())
    elif straight != None and flush == True:
        return (8, (straight))
    elif four_o_a_k != None:
        rank_and_kickers = [four_o_a_k] + [rank for rank in ranks if rank != four_o_a_k]
        return (7, tuple(rank_and_kickers))
    elif full_h != None:
        return (6, (full_h[0], full_h[1]))
    elif flush == True:
        return (5, (ranks))
    elif straight != None:
        return (4, straight)
    elif three_o_a_k != None:
        ranks_and_kickers = [three_o_a_k] + [rank for rank in ranks if rank != three_o_a_k]
        return (3, tuple(ranks_and_kickers))
    elif two_p != None:
        ranks_and_kickers = [two_p] + [rank for rank in ranks if rank not in two_p]
        return (2, tuple(ranks_and_kickers))
    elif one_p != None:
        ranks_and_kickers = [one_p] + [rank for rank in ranks if rank != one_p]
        return (1, tuple(ranks_and_kickers))
    else:
        return (0, tuple(ranks))
    return ranks, suits

def straight_high(ranks: list[int]) -> int | None:
    """
    Returns the top rank of the straight if one exists,
    otherwise None
    """
    ranks = sorted(set(ranks), reverse=True)

    if len(ranks) != 5:
        return None
    
    # Normal straight
    if ranks[0] - ranks[4] == 4:
        return ranks[0]

    # Handle A, 5, 4, 3, 2
    if ranks == [14, 5, 4, 3, 2]:
        return 5

    return None

def four_of_a_kind(rank_counts: tuple[int]) -> int | None:
    if len(rank_counts) != 1:
        return None
    if rank_counts[0][1] == 4:
        return rank_counts[0][0]
    return None

def full_house(rank_counts: tuple[int]) -> tuple[int] | None:
    rank_counts = sorted(rank_counts, key=lambda x: x[1], reverse=True)
    if len(rank_counts) != 2:
        return None
    if rank_counts[0][1] == 3 and rank_counts[1][1] == 2:
        ranks = tuple(sorted([rank[0] for rank in rank_counts], reverse=True))
        return ranks
    return None

def three_of_a_kind(rank_counts: tuple[int]) -> int | None:
    if len(rank_counts) != 1:
        return None
    if rank_counts[0][1] == 3:
        return rank_counts[0][0]
    return None

def two_pair(rank_counts: tuple[int]) -> tuple[int] | None:
    if len(rank_counts) != 2:
        return None
    if rank_counts[0][1] == 2 and rank_counts[1][1] == 2:
        return (rank_counts[0][0], rank_counts[0][1])
    return None

def one_pair(rank_counts: tuple[int]) -> int | None:
    if len(rank_counts) != 1:
        return None
    if rank_counts[0][1] == 2:
        return rank_counts[0][0]
    return None

def get_pairs(ranks: list[int]) -> tuple[int] | None:
    rank_counts = defaultdict(int)
    pairs = []
    for rank in ranks:
        rank_counts[rank] += 1
    rank_counts = [(rank, count) for rank, count in rank_counts.items() if count != 1]
    rank_counts = sorted(rank_counts, key=lambda x: x[0], reverse=True)
    return rank_counts
    

class PokerHand:
    def __init__(self, players: list[GamePlayer], button_pos: int, big_blind: int):

        self.players = players
        self.n_seats = len(players)

        self.in_showdown = False # used to show all cards during showdown

        # Assigns blinds based on button position
        self.button_pos = button_pos
        self.bb_amount = big_blind
        self.sb_amount = big_blind // 2

        self.sb_pos = (self.button_pos + 1) % self.n_seats
        self.bb_pos = (self.button_pos + 2) % self.n_seats
        self.current_player_idx = (self.bb_pos + 1) % self.n_seats

        self.players[self.button_pos].name = f"Seat {self.button_pos + 1} (Button)"
        self.players[self.sb_pos].name = f"Seat {self.sb_pos + 1} (SB)"
        self.players[self.bb_pos].name = f"Seat {self.bb_pos + 1} (BB)"

        self.pot = 0
        self.board: list[str] = []  # will grow to 5

        # Fresh, shuffled deck for this hand
        self.deck = list(range(52))
        random.shuffle(self.deck)

        self.reset_players_for_hand()
        self.post_blinds()
        self.current_bet = max(p.bet for p in self.players) # in case big-blind is all-in for less
        self.deal_cards()

    def apply_action(self, seat_idx: int, action: str, raise_to: int | None = None):
        """
        This function applies the fold, check/call, or raise action 
        to the player at the specifed seat position
        INPUTS:
            - seat_idx is the index of the person you wish to apply the action to
            - action is a string containing either "fold", "check", or "raise", indiciating
            which action to apply to the player at seat_idx
            - raise_to is an integer representing how much to raise (can be 'None')
        OUTPUTS:
            - none
        """
        p = self.players[seat_idx]
        if not p.in_hand:
            return

        action = action.lower()

        if action == "fold":
            p.in_hand = False
            p.made_decision_this_round = True
            p.last_action = "FOLD"

        elif action == "check":
            # check if already matched, otherwise it's a call
            needed = max(0, self.current_bet - p.bet)
            pay = min(needed, p.stack)
            p.stack -= pay
            p.bet += pay
            self.pot += pay
            p.made_decision_this_round = True

            p.last_action = "CHECK" if needed == 0 else "CALL"

        elif action == "raise":
            if raise_to is None:
                return
            raise_to = max(raise_to, self.current_bet)
            needed = max(0, raise_to - p.bet)
            pay = min(needed, p.stack)
            p.stack -= pay
            p.bet += pay
            self.pot += pay

            if p.bet > self.current_bet:
                self.current_bet = p.bet
                for other in self.players:
                    if other.in_hand and other is not p:
                        other.made_decision_this_round = False

            p.made_decision_this_round = True

            p.last_action = f"RAISE {p.bet}"

    def betting_round_complete(self) -> bool:
        """
        This function returns True or False whether 
        the betting round is complete or not 
        
        - If there is only one player in the hand, returns true
        - If everybody has acted atleast once and all non-folded players
        have the same bet, returns true
        Otherwise: FALSE

        INPUTS:
            - none
        OUTPUTS:
            - True or False representing whether the 
            betting round is complete or not
        """
        in_hand_players = [p for p in self.players if p.in_hand]
        if len(in_hand_players) <= 1:
            return True  # hand effectively over / no betting needed

        all_acted = all(p.made_decision_this_round for p in in_hand_players)
        bets_equal = len({p.bet for p in in_hand_players}) <= 1
        return all_acted and bets_equal

    def start_new_betting_round(self):
        """
        This functons starts a new betting round by

        1. Resets everyones individual bets
        2. Resetting the T/F var representing whether everyone has made
        a decision

        INPUTS:
            - none
        OUTPUTS:
            - none
        """
        # everyone’s bet is now "in the pot" (you already added to pot as chips went in),
        # so for UI cleanliness, reset displayed street bets to 0.
        for p in self.players:
            p.bet = 0
            p.made_decision_this_round = False
            p.last_action = None

        self.current_bet = 0  # no one has bet yet this street

    def advance_to_next_in_hand(self):
        """
        This function advances to the next 
        non-folded player in the hand
        INPUTS:
            - none
        OUTPUTS:
            - none
        """
        for _ in range(self.n_seats):
            self.current_player_idx = (self.current_player_idx + 1) % self.n_seats
            if self.players[self.current_player_idx].in_hand:
                return

    def reset_players_for_hand(self):
        """
        This function resets player's bet, hand activity state, and cards to prepare for a new hand
        INPUTS:
            - none
        OUTPUTS:
            - none
        """
        for p in self.players:
            p.bet = 0
            p.in_hand = True
            p.made_decision_this_round = False
            p.cards = ("??", "??")
            p.last_action = None

    def post_blinds(self):
        """
        This function pushes the blind bets
        INPUTS:
            - none
        OUTPUTS:
            - none
        """
        sb_p = self.players[self.sb_pos]
        bb_p = self.players[self.bb_pos]

        sb = min(self.sb_amount, sb_p.stack)
        bb = min(self.bb_amount, bb_p.stack)

        sb_p.stack -= sb
        bb_p.stack -= bb

        sb_p.bet += sb
        bb_p.bet += bb

        self.pot += sb + bb

    def deal_cards(self):
        """
        This function deals random cards to each player
        INPUTS:
            - none
        OUTPUTS:
            - none
        """
        for i in range(self.n_seats):
            c1 = card_to_str(self.deck.pop())
            c2 = card_to_str(self.deck.pop())
            self.players[i].cards = (c1, c2)

    def deal_flop(self):
        """
        This function deals the flop
        INPUTS:
            - none
        OUTPUTS:
            - none
        """
        # optional burn: self.deck.pop()
        self.board = [card_to_str(self.deck.pop()) for _ in range(3)]

    def deal_turn(self):
        """
        This function deals the turn
        INPUTS:
            - none
        OUTPUTS:
            - none
        """
        # optional burn: self.deck.pop()
        self.board.append(card_to_str(self.deck.pop()))

    def deal_river(self):
        """
        This function deals the river
        INPUTS:
            - none
        OUTPUTS:
            - none
        """
        # optional burn: self.deck.pop()
        self.board.append(card_to_str(self.deck.pop()))

    def initiate_showdown(self):
        """
        This function initiates the showdown
        INPUTS:
            - none
        OUTPUTS:
            - none
        """
        self.in_showdown = True
        for i in range(self.n_seats):
            self.players[i].cards_hidden = False

class PokerGame:
    def __init__(self, n_seats: int, big_blind_amount: int):
        self.n_seats = n_seats
        self.big_blind_amount = big_blind_amount

        self.players = [GamePlayer(name="Seat 1 (Me)", stack=1500)]
        self.players += [GamePlayer(name=f"Seat {i+1}", stack=1500) for i in range(1, n_seats)]

        self.hand_number = 0

        # Randomly assigns button
        self.button_pos = random.randrange(n_seats)
        #self.current_player_idx = self.button_pos

        self.hand: Optional[PokerHand] = None

    def start_hand(self):
        """
        This function starts the hand by creating a new hand object, and updating the hand tracking variable
        INPUTS:
            - none
        OUTPUTS:
            - none
        """
        self.hand = PokerHand(self.players, self.button_pos, self.big_blind_amount)
        self.hand_number += 1

    def end_hand(self):
        """
        This function ends the hand, and updates the button position
        INPUTS:
            - none
        OUTPUTS:
            - none
        """
        # rotate button for next hand
        self.button_pos = (self.button_pos + 1) % self.n_seats
        self.hand = None

# -=x=- UI -=x=-
class PokerGameUI(tk.Tk):
    def __init__(self, n_seats=8):
        super().__init__()
        self.title("Poker Simulation")
        self.geometry("1000x650")

        self.game_running = False
        self.paused = False

        self.n_seats = n_seats

        self.game = PokerGame(n_seats=self.n_seats, big_blind_amount=50)

        self.players = [UIPlayer(name=f"Me (Seat 1)", stack=1500, bet=0, in_hand=True, cards_hidden=False)]
        self.players += [
            UIPlayer(name=f"Seat {i+1}", stack=1500, bet=0, in_hand=True, cards_hidden=True)
            for i in range(1, n_seats)
        ]

        self.pot = 0
        self.community = ["??"] * 5

        # Canvas for all drawing
        self.canvas = tk.Canvas(self, bg="#1f1f1f", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Redraw on resize
        self.canvas.bind("<Configure>", lambda e: self.redraw())

        # Simple demo controls
        bar = tk.Frame(self, bg="#111")
        bar.place(relx=0.5, rely=0.98, anchor="s")

        self.start_pause_btn = tk.Button(
            bar,
            text="Start Game",
            command=self.toggle_game
        )
        self.start_pause_btn.pack(side="left", padx=6)
        tk.Button(bar, text="Raise", command=self.ui_raise).pack(side="right", padx=6)
        tk.Button(bar, text="Check/Call", command=self.ui_check_call).pack(side="right", padx=6)
        tk.Button(bar, text="Fold", command=self.ui_fold).pack(side="right", padx=6)
        tk.Button(bar, text="Reset Game", command=self.reset_game).pack(side="right", padx=6)

        self.redraw()

    def after_action(self):
        """
        This function is executed after any player makes an action
        such as fold, check/call, raise
        This functions then initiates the next betting round if necessary
        INPUTS:
            - none
        OUTPUTS:
            - none
        """
        hand = self.game.hand
        if hand is None:
            return

        # If betting round complete, initiate next round
        if hand.betting_round_complete():
            # Super simple street progression for now:
            if len(hand.board) == 0:
                hand.deal_flop()
            elif len(hand.board) == 3:
                hand.deal_turn()
            elif len(hand.board) == 4:
                hand.deal_river()
            else:
                # River betting complete -> you'd go to showdown later
                hand.initiate_showdown()

            hand.start_new_betting_round()

        self.sync_from_game()


    def sync_from_game(self):
        """
        This function syncs the player data between the UIPlayer objects and GamePlayer objects
        INPUTS:
            - none
        OUTPUTS:
            - none
        """
        hand = self.game.hand
        if hand is None:
            return

        self.pot = hand.pot
        self.community = (hand.board + ["??"] * 5)[:5]

        for i in range(self.n_seats):
            gp = self.game.players[i]
            up = self.players[i]

            up.stack = gp.stack
            up.bet = gp.bet
            up.in_hand = gp.in_hand
            up.cards = gp.cards
            up.name = gp.name
            up.cards_hidden = gp.cards_hidden
            up.last_action = gp.last_action

            if self.game.hand.in_showdown == False:
                # Only you see your cards
                up.cards_hidden = (i != 0)

        self.redraw()

    # -=x=- Helper Functions for UI (Don't Modify) -=x=-
    def seat_positions(self, cx, cy, rx, ry):
        """
        Returns list of (x,y,angle) points around an ellipse.
        """
        pts = []
        # Put one seat at bottom center like most poker UIs
        start_angle = pi/2
        for i in range(self.n_seats):
            a = start_angle + i * 2*pi/self.n_seats
            x = cx + rx * cos(a)
            y = cy + ry * sin(a)
            pts.append((x, y, a))
        return pts

    # -=x=- Drawing (Don't Modify) -=x=-

    SUIT_SYMBOL = {"c": "♣", "d": "♦", "h": "♥", "s": "♠"}
    SUIT_COLOR  = {"c": "#111111", "s": "#111111", "d": "#c1121f", "h": "#c1121f"}

    def parse_card(self, code: str):
        """'Ah' -> ('A','h'). Returns ('?','?') for unknowns."""
        if not code or len(code) < 2 or code == "??":
            return "?", "?"
        return code[0], code[1]

    def rounded_rect(self, x1, y1, x2, y2, r=10, **kwargs):
        """Draw a rounded rectangle on a Tk canvas using a smoothed polygon."""
        c = self.canvas
        r = min(r, abs(x2-x1)/2, abs(y2-y1)/2)
        points = [
            x1+r, y1,
            x2-r, y1,
            x2, y1,
            x2, y1+r,
            x2, y2-r,
            x2, y2,
            x2-r, y2,
            x1+r, y2,
            x1, y2,
            x1, y2-r,
            x1, y1+r,
            x1, y1
        ]
        return c.create_polygon(points, smooth=True, splinesteps=20, **kwargs)

    def draw_card_front(self, x1, y1, w, h, code: str):
        """Draw a nicer playing card face (UI only)."""
        c = self.canvas
        rank, suit = self.parse_card(code)

        # Card base
        self.rounded_rect(x1, y1, x1+w, y1+h, r=10, fill="#ffffff", outline="#222222", width=2)

        # Unknown card
        if rank == "?" or suit == "?":
            c.create_text(x1+w/2, y1+h/2, text="?", fill="#111", font=("Helvetica", int(h*0.35), "bold"))
            return

        sym = self.SUIT_SYMBOL.get(suit, "?")
        col = self.SUIT_COLOR.get(suit, "#111111")

        # Corner indices
        corner_font = ("Helvetica", max(10, int(h*0.22)), "bold")
        c.create_text(x1+w*0.18, y1+h*0.16, text=rank, fill=col, font=corner_font)
        c.create_text(x1+w*0.18, y1+h*0.33, text=sym,  fill=col, font=corner_font)

        c.create_text(x1+w*0.82, y1+h*0.84, text=rank, fill=col, font=corner_font)
        c.create_text(x1+w*0.82, y1+h*0.67, text=sym,  fill=col, font=corner_font)

        # Center pip
        center_font = ("Helvetica", max(14, int(h*0.45)), "bold")
        c.create_text(x1+w/2, y1+h/2, text=sym, fill=col, font=center_font)

    def draw_card_back(self, x1, y1, w, h):
        """Draw a Bicycle-ish patterned back (UI only, no images), without spillover."""
        c = self.canvas

        # Outer card
        self.rounded_rect(x1, y1, x1+w, y1+h, r=10, fill="#0b2a6f", outline="#111111", width=2)

        # Inner border
        pad = max(3, int(min(w, h) * 0.08))
        ix1, iy1 = x1 + pad, y1 + pad
        ix2, iy2 = x1 + w - pad, y1 + h - pad
        self.rounded_rect(ix1, iy1, ix2, iy2, r=8, fill="#0b2a6f", outline="#ffffff", width=2)

        # --- Pattern: tiny diagonal stitches (stays inside the inner rectangle) ---
        step = max(6, int(min(w, h) * 0.12))
        seg = max(6, step)  # segment length

        y = iy1 + 2
        while y < iy2 - 2:
            x = ix1 + 2
            while x < ix2 - 2:
                # down-right stitch
                x_end = min(x + seg, ix2 - 2)
                y_end = min(y + seg, iy2 - 2)
                c.create_line(x, y, x_end, y_end, fill="#ffffff", width=1, stipple="gray50")

                # down-left stitch (adds the crosshatch look)
                x2s = min(x + seg, ix2 - 2)
                y2s = max(y - seg, iy1 + 2)
                c.create_line(x, y, x2s, y2s, fill="#ffffff", width=1, stipple="gray50")

                x += step
            y += step

        # Center emblem
        c.create_oval(x1+w*0.35, y1+h*0.35, x1+w*0.65, y1+h*0.65, outline="#ffffff", width=2)
        c.create_text(x1+w/2, y1+h/2, text="★", fill="#ffffff",
                    font=("Helvetica", max(12, int(h*0.25)), "bold"))

    def redraw(self):
        c = self.canvas
        c.delete("all")

        w = c.winfo_width()
        h = c.winfo_height()

        # Table center and radii (responsive)
        cx, cy = w * 0.5, h * 0.48
        table_rx, table_ry = w * 0.32, h * 0.22

        # Draw table (oval + inner felt)
        c.create_oval(cx-table_rx*1.15, cy-table_ry*1.15, cx+table_rx*1.15, cy+table_ry*1.15,
                    fill="#2a2a2a", outline="")
        c.create_oval(cx-table_rx, cy-table_ry, cx+table_rx, cy+table_ry,
                    fill="#1e7a4a", outline="")

        # Pot
        c.create_text(cx, cy - table_ry*0.65, text=f"Pot: {self.pot}",
                    fill="white", font=("Helvetica", 18, "bold"))

        # Community cards (UPDATED: nicer faces/backs)
        card_w, card_h, gap = 60, 84, 12
        start_x = cx - (5*card_w + 4*gap)/2
        y_cards = cy - card_h/2
        for i, card in enumerate(self.community):
            x1 = start_x + i*(card_w+gap)
            y1 = y_cards
            if card == "??":
                self.draw_card_back(x1, y1, card_w, card_h)
            else:
                self.draw_card_front(x1, y1, card_w, card_h, card)

        # Seats around table
        seat_rx, seat_ry = w * 0.43, h * 0.32
        seats = self.seat_positions(cx, cy, seat_rx, seat_ry)

        for i, (sx, sy, ang) in enumerate(seats):
            p = self.players[i]

            # Seat box
            box_w, box_h = 150, 60
            x1, y1 = sx - box_w/2, sy - box_h/2
            x2, y2 = sx + box_w/2, sy + box_h/2

            seat_color = "#2b2b2b" if p.in_hand else "#1b1b1b"
            c.create_rectangle(x1, y1, x2, y2, fill=seat_color, outline="#444", width=2)

            c.create_text(sx, sy-10, text=p.name, fill="white", font=("Helvetica", 12, "bold"))
            c.create_text(sx, sy+12, text=f"Stack: {p.stack}", fill="#cfcfcf", font=("Helvetica", 11))

            # --- Action/bet badge pinned to top-left of seat tag (outside the box) ---
            badge_r = 14
            badge_x = x1 + badge_r + 6
            badge_y = y1 - badge_r - 6

            if (p.last_action or "").upper() == "CHECK":
                # CHECK badge (same style as chip, different color)
                c.create_oval(
                    badge_x - badge_r, badge_y - badge_r,
                    badge_x + badge_r, badge_y + badge_r,
                    fill="#67c8ff", outline="#1b6a8d", width=2
                )
                c.create_text(
                    badge_x, badge_y,
                    text="CHK",   # or "CHK" if you want it cleaner
                    fill="black",
                    font=("Helvetica", 7, "bold")  # small enough to fit in the circle
                )

            elif p.bet > 0:
                # Bet chip (your original)
                c.create_oval(
                    badge_x - badge_r, badge_y - badge_r,
                    badge_x + badge_r, badge_y + badge_r,
                    fill="#d4af37", outline="#8c6b1f", width=2
                )
                c.create_text(
                    badge_x, badge_y,
                    text=str(p.bet),
                    fill="black",
                    font=("Helvetica", 9, "bold")
                )




            # Hold cards near seat (UPDATED: nicer faces/backs)
            if p.in_hand:
                hold_w, hold_h = 46, 64
                cards_x, cards_y = sx, sy - 62
                for k in range(2):
                    offset = (k - 0.5) * (hold_w * 0.55)
                    hx1 = (cards_x + offset) - hold_w/2
                    hy1 = cards_y - hold_h/2

                    if p.cards_hidden:
                        self.draw_card_back(hx1, hy1, hold_w, hold_h)
                    else:
                        self.draw_card_front(hx1, hy1, hold_w, hold_h, p.cards[k])


    # -=x=- Button Functionality -=x=-
    def toggle_game(self):
        # This is the function for the Start / Pause / Resume button
        if not self.game_running and not self.paused:
            self.start_game()
        elif self.paused:
            self.resume_game()
        else:
            self.pause_game()

    def ui_raise(self):
        if self.game.hand is None or self.game.hand.in_showdown == True:
            return
        hand = self.game.hand
        current_player_idx = hand.current_player_idx

        raise_to = simpledialog.askinteger(
            "Raise",
            f"Raise to what total bet? (current bet = {hand.current_bet})",
            minvalue=hand.current_bet
        )
        if raise_to is None:
            return

        hand.apply_action(current_player_idx, "raise", raise_to=raise_to)
        hand.advance_to_next_in_hand()
        self.after_action()

    def ui_check_call(self):
        if self.game.hand is None or self.game.hand.in_showdown == True:
            return
        current_player_idx = self.game.hand.current_player_idx
        self.game.hand.apply_action(current_player_idx, "check")
        self.game.hand.advance_to_next_in_hand()
        self.after_action()

    def ui_fold(self):
        if self.game.hand is None or self.game.hand.in_showdown == True:
            return
        current_player_idx = self.game.hand.current_player_idx
        self.game.hand.apply_action(current_player_idx, "fold")
        self.game.hand.advance_to_next_in_hand()
        self.after_action()

    def reset_game(self):
        # reset game object state
        self.game = PokerGame(n_seats=self.n_seats, big_blind_amount=self.game.big_blind_amount)

        # reset UI state to initial
        self.players = [UIPlayer(name="Me (Seat 1)", stack=1500, bet=0, in_hand=True, cards_hidden=False)]
        self.players += [
            UIPlayer(name=f"Seat {i+1}", stack=1500, bet=0, in_hand=True, cards_hidden=True)
            for i in range(1, self.n_seats)
        ]

        self.pot = 0
        self.community = ["??"] * 5

        self.game_running = False
        self.paused = False
        self.start_pause_btn.config(text="Start Game")

        self.redraw()

    # Start / Resume / Pause Game Functionality

    def start_game(self):
        # This is called when the Start Game button is pressed
        self.game_running = True # Used so the start game button isn't shown again
        self.start_pause_btn.config(text="Pause Game")

        self.game.start_hand()
        self.sync_from_game()

    def pause_game(self):
        # This is called when the Pause Game button is pressed
        self.game_running = False
        self.paused = True # Used so the Resume Button is shown next time
        self.start_pause_btn.config(text="Resume Game")

    def resume_game(self):
        # This is called when the Resume Game button is pressed
        self.game_running = True
        self.paused = False
        self.start_pause_btn.config(text="Pause Game")

print(score_five(parse_cards(["Ah", "Kh", "Qh", "Jh", "Th"])))
print(score_five(parse_cards(["Th", "9h", "8h", "7h", "6h"])))
print(score_five(parse_cards(["Th", "Ts", "Tc", "Td", "9s"])))
print(score_five(parse_cards(["Th", "Ts", "Tc", "9h", "9s"])))
print(score_five(parse_cards(["Th", "3h", "5h", "8h", "7h"])))
print(score_five(parse_cards(["Th", "9s", "8c", "7h", "6s"])))
print(score_five(parse_cards(["Th", "Ts", "Tc", "9h", "8s"])))
print(score_five(parse_cards(["Th", "Ts", "5c", "9h", "9s"])))
print(score_five(parse_cards(["Th", "Ts", "6c", "9h", "4s"])))
print(score_five(parse_cards(["Th", "8s", "6c", "4h", "2s"])))
#PokerGameUI(n_seats=8).mainloop()