import tkinter as tk
from dataclasses import dataclass
from math import cos, sin, pi
import random

# ---------- Data model ----------
@dataclass
class Player:
    name: str
    stack: int
    bet: int = 0
    in_hand: bool = True
    cards_hidden: bool = True  # hole cards not shown

# ---------- UI ----------
class PokerTableUI(tk.Tk):
    def __init__(self, n_seats=8):
        super().__init__()
        self.title("Poker Table")
        self.geometry("1000x650")

        self.n_seats = n_seats
        self.players = [Player(name=f"Me (Seat 1)", stack=1500, bet=0, in_hand=True, cards_hidden=False)]
        self.players += [
            Player(name=f"Seat {i+1}", stack=1500, bet=0, in_hand=True, cards_hidden=True)
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

        tk.Button(bar, text="Pause Game", command=self.pause_game).pack(side="left", padx=6)
        tk.Button(bar, text="Deal (Hidden)", command=self.demo_deal_hidden).pack(side="left", padx=6)
        tk.Button(bar, text="Clear Bets", command=self.demo_clear_bets).pack(side="left", padx=6)

        self.redraw()

    def setPot(value):
        self.pot = value

    def setFlop(cards):
        if len(cards) != 3:
            return
        else:
            for idx, card in enumerate(cards):
                self.community[idx] = card

    def setTurn(card):
        self.community[3] = card

    def setRiver(card):
        self.community[4] = card

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
                    c.create_text(x, cards_y, text="🂠" if p.cards_hidden else "??",
                                  fill="white" if p.cards_hidden else "black",
                                  font=("Helvetica", 12))

    # -=x=- Button Actions -=x=-
    def pause_game(self):
        pass

    def demo_deal_hidden(self):
        for p in self.players:
            p.in_hand = True
        self.community = ["??"] * 5
        self.redraw()

    def demo_clear_bets(self):
        for p in self.players:
            p.bet = 0
        self.pot = 0
        self.redraw()


PokerTableUI(n_seats=8).mainloop()
