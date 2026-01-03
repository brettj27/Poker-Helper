import tkinter as tk
from tkinter import simpledialog
from dataclasses import dataclass
from math import cos, sin, pi
from typing import Optional
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

# This is the class for the UI

@dataclass
class UIPlayer:
    name: str
    stack: int
    bet: int = 0
    in_hand: bool = True
    cards_hidden: bool = True  # hole cards not shown
    cards: tuple[str, str] = ("??", "??")

RANKS = "23456789TJQKA"
SUITS = "cdhs"  # clubs, diamonds, hearts, spades

def card_to_str(card_id: int) -> str:
    """
    This function computes our assigned card IDs (0-51) to a tuple representing the card such as ('A', 'h'), which is the ace of hearts
    INPUTS:
        - card_id is the card ID value (an integer between [0, 51])
    OUTPUTS:
        - a tuple such as ('A', 'h') representing the card
    """
    rank = RANKS[card_id % 13]
    suit = SUITS[card_id // 13]
    return f"{rank}{suit}"  # like "Ah", "7d", etc

class PokerHand:
    def __init__(self, players: list[GamePlayer], button_pos: int, big_blind: int):

        self.players = players
        self.n_seats = len(players)

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
        self.current_bet = big_blind
        self.deal_cards()

    def apply_action(self, seat_idx: int, action: str, raise_to: int | None = None):
        p = self.players[seat_idx]
        if not p.in_hand:
            return

        action = action.lower()

        if action == "fold":
            p.in_hand = False
            p.made_decision_this_round = True

        elif action == "check":
            # check if already matched, otherwise it's a call
            needed = max(0, self.current_bet - p.bet)
            pay = min(needed, p.stack)
            p.stack -= pay
            p.bet += pay
            p.made_decision_this_round = True

        elif action == "raise":
            if raise_to is None:
                return
            raise_to = max(raise_to, self.current_bet)
            needed = max(0, raise_to - p.bet)
            pay = min(needed, p.stack)
            p.stack -= pay
            p.bet += pay

            if p.bet > self.current_bet:
                self.current_bet = p.bet
                for other in self.players:
                    if other.in_hand and other is not p:
                        other.made_decision_this_round = False

            p.made_decision_this_round = True


    def run_betting_round(self):
        while True:
            idx = next_player_to_act(
                self.players,
                self.current_player_idx,
                self.current_bet
            )

            if idx is None:
                break  # betting round complete

            self.current_player_idx = idx
            player = self.players[idx]

            self.prompt_player_action(player)

    def next_player_to_act(self, players, start_idx, current_bet):
        n = len(players)
        for i in range(n):
            idx = (start_idx + i) % n
            p = players[idx]
            if needs_action(p, current_bet):
                return idx
        return None  # betting round complete

    def needs_action(self, player: GamePlayer, current_bet: int) -> bool:
        # Returns T or F whether a player needs to act or not
        return (
            player.in_hand
            and (not player.made_decision_this_round or player.bet < current_bet)
        )

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
            p.cards = ("??", "??")

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
        tk.Button(bar, text="Check", command=self.ui_check).pack(side="right", padx=6)
        tk.Button(bar, text="Fold", command=self.ui_fold).pack(side="right", padx=6)

        self.redraw()

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

            # Only you see your cards
            up.cards_hidden = (i != 0)

        self.redraw()

    # -=x=- Helper Functions for UI -=x=-
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

        # Community cards (simple boxes)
        card_w, card_h, gap = 50, 70, 12
        start_x = cx - (5*card_w + 4*gap)/2
        y_cards = cy - card_h/2
        for i, card in enumerate(self.community):
            x1 = start_x + i*(card_w+gap)
            y1 = y_cards
            c.create_rectangle(x1, y1, x1+card_w, y1+card_h, fill="#0f0f0f", outline="#333")
            c.create_text(x1+card_w/2, y1+card_h/2, text=card, fill="#ddd", font=("Consolas", 14, "bold"))

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

            # Bets "in front" of the seat (toward center)
            # Vector from seat -> center, step inward
            dx, dy = (cx - sx), (cy - sy)
            mag = (dx*dx + dy*dy) ** 0.5 or 1.0
            ux, uy = dx/mag, dy/mag
            bet_x, bet_y = sx + ux*65, sy + uy*65

            if p.bet > 0:
                c.create_oval(bet_x-18, bet_y-18, bet_x+18, bet_y+18, fill="#d4af37", outline="")
                c.create_text(bet_x, bet_y, text=str(p.bet), fill="black", font=("Helvetica", 10, "bold"))

            # Hold cards near seat (hidden backs)
            card_back_w, card_back_h = 28, 40
            cards_x, cards_y = sx, sy - 55
            if p.in_hand:
                for k in range(2):
                    offset = (k - 0.5) * 18
                    x = cards_x + offset
                    c.create_rectangle(
                        x-card_back_w/2, cards_y-card_back_h/2,
                        x+card_back_w/2, cards_y+card_back_h/2,
                        fill="#0b2a6f" if p.cards_hidden else "#ffffff",
                        outline="#222"
                    )
                    card_text = "🂠" if p.cards_hidden else p.cards[k]
                    c.create_text(x, cards_y, text=card_text,
                                  fill="white" if p.cards_hidden else "black",
                                  font=("Helvetica", 12))

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
        if self.game.hand is None:
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
        hand.current_player_idx = (current_player_idx + 1) % self.n_seats
        self.sync_from_game()

    def ui_check(self):
        if self.game.hand is None:
            return
        current_player_idx = self.game.hand.current_player_idx
        self.game.hand.apply_action(current_player_idx, "check")
        self.game.hand.current_player_idx = (current_player_idx + 1) % self.n_seats
        self.sync_from_game()

    def ui_fold(self):
        if self.game.hand is None:
            return
        current_player_idx = self.game.hand.current_player_idx
        self.game.hand.apply_action(current_player_idx, "fold")
        self.game.hand.current_player_idx = (current_player_idx + 1) % self.n_seats
        self.sync_from_game()


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


PokerGameUI(n_seats=8).mainloop()