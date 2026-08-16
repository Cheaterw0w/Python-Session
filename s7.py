"""
Chess Game - Tkinter GUI implementation with full rule validation.

Features:
- All standard piece movement rules
- Check, checkmate, and stalemate detection
- Castling (kingside and queenside)
- En passant capture
- Pawn promotion (with piece choice dialog)
- Move highlighting and turn indicator
"""

import tkinter as tk
from tkinter import Toplevel, Button, Label, Frame, messagebox
from collections import namedtuple

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------

SQUARE = 70
MARGIN = 36
BOARD_PX = SQUARE * 8

LIGHT_SQ = "#EEEED2"
DARK_SQ = "#769656"
SELECT_COLOR = "#F6F669"
MOVE_DOT = "#3A3A3A"
CAPTURE_RING = "#D3542A"
CHECK_COLOR = "#E86A6A"
LAST_MOVE_COLOR = "#BACA44"

PIECE_UNICODE = {
    "wK": "\u2654", "wQ": "\u2655", "wR": "\u2656",
    "wB": "\u2657", "wN": "\u2658", "wP": "\u2659",
    "bK": "\u265A", "bQ": "\u265B", "bR": "\u265C",
    "bB": "\u265D", "bN": "\u265E", "bP": "\u265F",
}

DIRS_BISHOP = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
DIRS_ROOK = [(-1, 0), (1, 0), (0, -1), (0, 1)]
DIRS_QUEEN = DIRS_BISHOP + DIRS_ROOK
KNIGHT_MOVES = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
KING_MOVES = DIRS_QUEEN

Move = namedtuple("Move", ["fr", "to", "flag", "promo"])


def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def piece_color(p):
    return p[0] if p else None


def piece_type(p):
    return p[1] if p else None


def opponent(color):
    return "b" if color == "w" else "w"


def square_name(r, c):
    return "abcdefgh"[c] + str(8 - r)


# ----------------------------------------------------------------------
# Board / state setup
# ----------------------------------------------------------------------

def initial_board():
    board = [[None] * 8 for _ in range(8)]
    order = ["R", "N", "B", "Q", "K", "B", "N", "R"]
    for c in range(8):
        board[0][c] = "b" + order[c]
        board[1][c] = "bP"
        board[6][c] = "wP"
        board[7][c] = "w" + order[c]
    return board


class GameState:
    def __init__(self):
        self.board = initial_board()
        self.turn = "w"
        self.castling = {"wK": True, "wQ": True, "bK": True, "bQ": True}
        self.ep_target = None
        self.move_log = []
        self.game_over = False

    def copy(self):
        gs = GameState.__new__(GameState)
        gs.board = [row[:] for row in self.board]
        gs.turn = self.turn
        gs.castling = dict(self.castling)
        gs.ep_target = self.ep_target
        gs.move_log = list(self.move_log)
        gs.game_over = self.game_over
        return gs


# ----------------------------------------------------------------------
# Attack generation (used for check detection)
# ----------------------------------------------------------------------

def attacked_squares_by_piece(board, r, c):
    p = board[r][c]
    if not p:
        return set()
    color = piece_color(p)
    t = piece_type(p)
    squares = set()

    if t == "P":
        d = -1 if color == "w" else 1
        for dc in (-1, 1):
            nr, nc = r + d, c + dc
            if in_bounds(nr, nc):
                squares.add((nr, nc))
    elif t == "N":
        for dr, dc in KNIGHT_MOVES:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc):
                squares.add((nr, nc))
    elif t == "K":
        for dr, dc in KING_MOVES:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc):
                squares.add((nr, nc))
    elif t in ("B", "R", "Q"):
        dirs = DIRS_BISHOP if t == "B" else DIRS_ROOK if t == "R" else DIRS_QUEEN
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            while in_bounds(nr, nc):
                squares.add((nr, nc))
                if board[nr][nc] is not None:
                    break
                nr += dr
                nc += dc
    return squares


def is_square_attacked(board, r, c, by_color):
    for rr in range(8):
        for cc in range(8):
            p = board[rr][cc]
            if p and piece_color(p) == by_color:
                if (r, c) in attacked_squares_by_piece(board, rr, cc):
                    return True
    return False


def find_king(board, color):
    for r in range(8):
        for c in range(8):
            if board[r][c] == color + "K":
                return (r, c)
    return None


# ----------------------------------------------------------------------
# Pseudo-legal move generation
# ----------------------------------------------------------------------

def gen_piece_moves(state, r, c):
    board = state.board
    p = board[r][c]
    if not p:
        return []
    color = piece_color(p)
    t = piece_type(p)
    moves = []

    if t == "P":
        d = -1 if color == "w" else 1
        start_row = 6 if color == "w" else 1
        last_row = 0 if color == "w" else 7
        nr = r + d
        if in_bounds(nr, c) and board[nr][c] is None:
            if nr == last_row:
                for promo in ["Q", "R", "B", "N"]:
                    moves.append(Move((r, c), (nr, c), "promo", promo))
            else:
                moves.append(Move((r, c), (nr, c), None, None))
            nr2 = r + 2 * d
            if r == start_row and in_bounds(nr2, c) and board[nr2][c] is None:
                moves.append(Move((r, c), (nr2, c), "double", None))
        for dc in (-1, 1):
            nc = c + dc
            if in_bounds(nr, nc):
                target = board[nr][nc]
                if target and piece_color(target) != color:
                    if nr == last_row:
                        for promo in ["Q", "R", "B", "N"]:
                            moves.append(Move((r, c), (nr, nc), "promo", promo))
                    else:
                        moves.append(Move((r, c), (nr, nc), None, None))
                elif state.ep_target == (nr, nc):
                    moves.append(Move((r, c), (nr, nc), "ep", None))

    elif t == "N":
        for dr, dc in KNIGHT_MOVES:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc):
                target = board[nr][nc]
                if target is None or piece_color(target) != color:
                    moves.append(Move((r, c), (nr, nc), None, None))

    elif t == "K":
        for dr, dc in KING_MOVES:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc):
                target = board[nr][nc]
                if target is None or piece_color(target) != color:
                    moves.append(Move((r, c), (nr, nc), None, None))
        opp = opponent(color)
        if not is_square_attacked(board, r, c, opp):
            if state.castling.get(color + "K"):
                if (board[r][5] is None and board[r][6] is None
                        and board[r][7] == color + "R"):
                    if (not is_square_attacked(board, r, 5, opp)
                            and not is_square_attacked(board, r, 6, opp)):
                        moves.append(Move((r, c), (r, 6), "castleK", None))
            if state.castling.get(color + "Q"):
                if (board[r][1] is None and board[r][2] is None and board[r][3] is None
                        and board[r][0] == color + "R"):
                    if (not is_square_attacked(board, r, 3, opp)
                            and not is_square_attacked(board, r, 2, opp)):
                        moves.append(Move((r, c), (r, 2), "castleQ", None))

    elif t in ("B", "R", "Q"):
        dirs = DIRS_BISHOP if t == "B" else DIRS_ROOK if t == "R" else DIRS_QUEEN
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            while in_bounds(nr, nc):
                target = board[nr][nc]
                if target is None:
                    moves.append(Move((r, c), (nr, nc), None, None))
                else:
                    if piece_color(target) != color:
                        moves.append(Move((r, c), (nr, nc), None, None))
                    break
                nr += dr
                nc += dc

    return moves


def apply_move(state, move):
    """Return a new GameState with the move applied (no legality checking)."""
    ns = state.copy()
    board = ns.board
    r1, c1 = move.fr
    r2, c2 = move.to
    piece = board[r1][c1]
    color = piece_color(piece)
    captured = board[r2][c2]

    ns.ep_target = None
    if move.flag == "double":
        ns.ep_target = ((r1 + r2) // 2, c1)
    if move.flag == "ep":
        board[r1][c2] = None  # captured pawn sits beside the mover, same row as start

    board[r2][c2] = piece
    board[r1][c1] = None

    if move.flag == "promo":
        board[r2][c2] = color + move.promo

    if move.flag == "castleK":
        board[r2][5] = board[r2][7]
        board[r2][7] = None
    if move.flag == "castleQ":
        board[r2][3] = board[r2][0]
        board[r2][0] = None

    if piece_type(piece) == "K":
        ns.castling[color + "K"] = False
        ns.castling[color + "Q"] = False
    if piece_type(piece) == "R":
        home = 7 if color == "w" else 0
        if r1 == home and c1 == 0:
            ns.castling[color + "Q"] = False
        if r1 == home and c1 == 7:
            ns.castling[color + "K"] = False
    if captured and piece_type(captured) == "R":
        cc = piece_color(captured)
        home = 7 if cc == "w" else 0
        if r2 == home and c2 == 0:
            ns.castling[cc + "Q"] = False
        if r2 == home and c2 == 7:
            ns.castling[cc + "K"] = False

    ns.turn = opponent(color)
    ns.move_log.append(move)
    return ns


def in_check(state, color):
    kpos = find_king(state.board, color)
    if not kpos:
        return False
    return is_square_attacked(state.board, kpos[0], kpos[1], opponent(color))


def legal_moves_for_square(state, r, c):
    p = state.board[r][c]
    if not p or piece_color(p) != state.turn:
        return []
    legal = []
    for m in gen_piece_moves(state, r, c):
        ns = apply_move(state, m)
        if not in_check(ns, piece_color(p)):
            legal.append(m)
    return legal


def all_legal_moves(state):
    result = {}
    for r in range(8):
        for c in range(8):
            p = state.board[r][c]
            if p and piece_color(p) == state.turn:
                lm = legal_moves_for_square(state, r, c)
                if lm:
                    result[(r, c)] = lm
    return result


def game_status(state):
    moves = all_legal_moves(state)
    total = sum(len(v) for v in moves.values())
    if total == 0:
        return "checkmate" if in_check(state, state.turn) else "stalemate"
    return "ongoing"


# ----------------------------------------------------------------------
# GUI
# ----------------------------------------------------------------------

class ChessGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chess")
        self.root.resizable(False, False)

        self.state = GameState()
        self.selected = None
        self.legal_targets = {}

        outer = Frame(root, bg="#2B2B2B")
        outer.pack(padx=10, pady=10)

        self.status_label = Label(
            outer, text="", font=("Helvetica", 16, "bold"),
            bg="#2B2B2B", fg="white"
        )
        self.status_label.pack(pady=(0, 8))

        self.canvas = tk.Canvas(
            outer, width=BOARD_PX + 2 * MARGIN, height=BOARD_PX + 2 * MARGIN,
            bg="#2B2B2B", highlightthickness=0
        )
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_click)

        btn_frame = Frame(outer, bg="#2B2B2B")
        btn_frame.pack(pady=(10, 0))
        Button(btn_frame, text="New Game", font=("Helvetica", 12),
               command=self.new_game).pack(side="left", padx=5)

        self.redraw()

    # ---------------- board <-> pixel helpers ----------------

    def square_at(self, x, y):
        col = (x - MARGIN) // SQUARE
        row = (y - MARGIN) // SQUARE
        if in_bounds(row, col):
            return int(row), int(col)
        return None

    # ---------------- interaction ----------------

    def on_click(self, event):
        if self.state.game_over:
            return
        sq = self.square_at(event.x, event.y)
        if sq is None:
            return
        row, col = sq

        if self.selected and (row, col) in self.legal_targets:
            move = self.legal_targets[(row, col)]
            if move.flag == "promo":
                color = piece_color(self.state.board[self.selected[0]][self.selected[1]])
                promo = self.ask_promotion(color)
                move = Move(move.fr, move.to, "promo", promo)
            self.state = apply_move(self.state, move)
            self.selected = None
            self.legal_targets = {}
            self.after_move()
            return

        piece = self.state.board[row][col]
        if piece and piece_color(piece) == self.state.turn:
            self.selected = (row, col)
            self.legal_targets = {}
            for m in legal_moves_for_square(self.state, row, col):
                self.legal_targets[m.to] = m
        else:
            self.selected = None
            self.legal_targets = {}

        self.redraw()

    def ask_promotion(self, color):
        win = Toplevel(self.root)
        win.title("Promote Pawn")
        win.resizable(False, False)
        win.transient(self.root)
        win.grab_set()

        choice = {"value": "Q"}

        def pick(p):
            choice["value"] = p
            win.destroy()

        Label(win, text="Choose promotion:", font=("Helvetica", 13)).pack(pady=8)
        frame = Frame(win)
        frame.pack(padx=10, pady=10)
        for p, name in [("Q", "Queen"), ("R", "Rook"), ("B", "Bishop"), ("N", "Knight")]:
            symbol = PIECE_UNICODE[color + p]
            Button(
                frame, text=f"{symbol}\n{name}", font=("Arial", 18), width=5,
                command=lambda p=p: pick(p)
            ).pack(side="left", padx=4)

        win.update_idletasks()
        rx = self.root.winfo_rootx()
        ry = self.root.winfo_rooty()
        win.geometry(f"+{rx + 120}+{ry + 200}")
        win.wait_window()
        return choice["value"]

    def after_move(self):
        status = game_status(self.state)
        if status == "checkmate":
            self.state.game_over = True
            winner = "White" if self.state.turn == "b" else "Black"
            self.redraw()
            messagebox.showinfo("Checkmate", f"Checkmate! {winner} wins.")
        elif status == "stalemate":
            self.state.game_over = True
            self.redraw()
            messagebox.showinfo("Stalemate", "Stalemate! The game is a draw.")
        else:
            self.redraw()

    def new_game(self):
        self.state = GameState()
        self.selected = None
        self.legal_targets = {}
        self.redraw()

    # ---------------- drawing ----------------

    def redraw(self):
        self.canvas.delete("all")
        self.draw_coordinates()
        self.draw_squares()
        self.draw_last_move()
        self.draw_selection_and_targets()
        self.draw_check_highlight()
        self.draw_pieces()
        self.update_status()

    def draw_coordinates(self):
        for c in range(8):
            x = MARGIN + c * SQUARE + SQUARE // 2
            self.canvas.create_text(
                x, MARGIN // 2, text="abcdefgh"[c],
                fill="white", font=("Helvetica", 11)
            )
            self.canvas.create_text(
                x, MARGIN + BOARD_PX + MARGIN // 2, text="abcdefgh"[c],
                fill="white", font=("Helvetica", 11)
            )
        for r in range(8):
            y = MARGIN + r * SQUARE + SQUARE // 2
            self.canvas.create_text(
                MARGIN // 2, y, text=str(8 - r),
                fill="white", font=("Helvetica", 11)
            )
            self.canvas.create_text(
                MARGIN + BOARD_PX + MARGIN // 2, y, text=str(8 - r),
                fill="white", font=("Helvetica", 11)
            )

    def draw_squares(self):
        for r in range(8):
            for c in range(8):
                x1 = MARGIN + c * SQUARE
                y1 = MARGIN + r * SQUARE
                x2 = x1 + SQUARE
                y2 = y1 + SQUARE
                color = LIGHT_SQ if (r + c) % 2 == 0 else DARK_SQ
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

    def draw_last_move(self):
        if not self.state.move_log:
            return
        last = self.state.move_log[-1]
        for (r, c) in (last.fr, last.to):
            x1 = MARGIN + c * SQUARE
            y1 = MARGIN + r * SQUARE
            self.canvas.create_rectangle(
                x1, y1, x1 + SQUARE, y1 + SQUARE,
                fill=LAST_MOVE_COLOR, outline="", stipple="gray50"
            )

    def draw_selection_and_targets(self):
        if self.selected:
            r, c = self.selected
            x1 = MARGIN + c * SQUARE
            y1 = MARGIN + r * SQUARE
            self.canvas.create_rectangle(
                x1, y1, x1 + SQUARE, y1 + SQUARE,
                fill=SELECT_COLOR, outline=""
            )
        for (r, c) in self.legal_targets:
            x = MARGIN + c * SQUARE + SQUARE // 2
            y = MARGIN + r * SQUARE + SQUARE // 2
            is_capture = self.state.board[r][c] is not None or \
                self.legal_targets[(r, c)].flag == "ep"
            if is_capture:
                self.canvas.create_oval(
                    x - SQUARE // 2 + 5, y - SQUARE // 2 + 5,
                    x + SQUARE // 2 - 5, y + SQUARE // 2 - 5,
                    outline=CAPTURE_RING, width=4
                )
            else:
                rad = 9
                self.canvas.create_oval(
                    x - rad, y - rad, x + rad, y + rad,
                    fill=MOVE_DOT, outline=""
                )

    def draw_check_highlight(self):
        color = self.state.turn
        if in_check(self.state, color):
            kpos = find_king(self.state.board, color)
            if kpos:
                r, c = kpos
                x1 = MARGIN + c * SQUARE
                y1 = MARGIN + r * SQUARE
                self.canvas.create_rectangle(
                    x1, y1, x1 + SQUARE, y1 + SQUARE,
                    fill=CHECK_COLOR, outline="", stipple="gray50"
                )

    def draw_pieces(self):
        for r in range(8):
            for c in range(8):
                piece = self.state.board[r][c]
                if not piece:
                    continue
                x = MARGIN + c * SQUARE + SQUARE // 2
                y = MARGIN + r * SQUARE + SQUARE // 2
                char = PIECE_UNICODE[piece]
                main_color = "white" if piece[0] == "w" else "#111111"
                outline_color = "#111111" if piece[0] == "w" else "#EFEFEF"
                for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                    self.canvas.create_text(
                        x + dx, y + dy, text=char,
                        font=("Arial", int(SQUARE * 0.62)), fill=outline_color
                    )
                self.canvas.create_text(
                    x, y, text=char,
                    font=("Arial", int(SQUARE * 0.62)), fill=main_color
                )

    def update_status(self):
        if self.state.game_over:
            status = game_status(self.state)
            if status == "checkmate":
                winner = "White" if self.state.turn == "b" else "Black"
                text = f"Checkmate \u2014 {winner} wins"
            else:
                text = "Stalemate \u2014 Draw"
        else:
            turn_name = "White" if self.state.turn == "w" else "Black"
            text = f"{turn_name} to move"
            if in_check(self.state, self.state.turn):
                text += "  \u2014  Check!"
        self.status_label.config(text=text)


def main():
    root = tk.Tk()
    ChessGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()