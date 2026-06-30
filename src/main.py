import pygame
import sys
import math
import random
import os

pygame.init()

# =========================
# FULLSCREEN SETUP
# =========================

info = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w, info.current_h

# The old build placed the board at (0, 0), which made the UI feel empty.
# This version keeps fullscreen mode, but adds margins, a centred board and a
# proper right-hand game dashboard.
MARGIN = 36
SIDE_GAP = 28
RIGHT_PANEL_WIDTH = min(560, max(430, int(SCREEN_WIDTH * 0.32)))
BOARD_SIZE = min(900, SCREEN_HEIGHT - (MARGIN * 2), SCREEN_WIDTH - RIGHT_PANEL_WIDTH - SIDE_GAP - (MARGIN * 2))
BOARD_SIZE = max(560, (BOARD_SIZE // 8) * 8)

WINDOW_WIDTH, WINDOW_HEIGHT = SCREEN_WIDTH, SCREEN_HEIGHT
BOARD_X = max(MARGIN, (WINDOW_WIDTH - BOARD_SIZE - SIDE_GAP - RIGHT_PANEL_WIDTH) // 2)
BOARD_Y = max(MARGIN, (WINDOW_HEIGHT - BOARD_SIZE) // 2)
PANEL_X = BOARD_X + BOARD_SIZE + SIDE_GAP
PANEL_Y = BOARD_Y
PANEL_W = RIGHT_PANEL_WIDTH
PANEL_H = BOARD_SIZE

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Bonnyrigg Chess Engine")

SQSIZE = BOARD_SIZE // 8

# =========================
# COLORS
# =========================

# Dark modern game theme
COLOR_BG_TOP = (12, 16, 23)
COLOR_BG_BOTTOM = (23, 29, 39)
COLOR_BG = (15, 18, 25)
COLOR_LIGHT = (238, 222, 183)
COLOR_DARK = (111, 145, 76)
COLOR_BOARD_FRAME = (42, 34, 25)
COLOR_BOARD_BORDER = (199, 170, 91)
COLOR_HIGHLIGHT = (252, 212, 88)
COLOR_LAST_MOVE = (250, 205, 83)
COLOR_LEGAL = (148, 213, 75)
COLOR_SELECTED = (178, 255, 91)
COLOR_PANEL = (22, 28, 37)
COLOR_CARD = (30, 37, 47)
COLOR_CARD_DARK = (18, 23, 31)
COLOR_BORDER = (61, 73, 88)
COLOR_TEXT = (236, 239, 244)
COLOR_MUTED = (157, 166, 178)
COLOR_ACCENT = (242, 199, 89)
COLOR_ACCENT_DARK = (167, 123, 39)
COLOR_GREEN = (119, 168, 55)
COLOR_DANGER = (166, 71, 63)
COLOR_DISABLED = (93, 100, 109)
COLOR_MOVE_BG = (24, 30, 39)

# =========================
# FONTS
# =========================

UI_SCALE = max(0.85, min(1.15, BOARD_SIZE / 880))

def make_font(name, size, bold=False):
    return pygame.font.SysFont(name, int(size * UI_SCALE), bold=bold)

FONT_TITLE = make_font("georgia", 58, True)
FONT_SUBTITLE = make_font("arial", 24)
FONT_MODE = make_font("arial", 30, True)
FONT_SMALL = make_font("arial", 18)
FONT_TINY = make_font("arial", 14)
FONT_MOVE = make_font("consolas", 18)
FONT_CHAT = make_font("arial", 17)
FONT_TURN = make_font("arial", 22, True)
FONT_CARD_TITLE = make_font("georgia", 26, True)
FONT_TIMER = make_font("consolas", 28, True)
FONT_BUTTON = make_font("arial", 19, True)
FONT_COORD = make_font("georgia", 20, True)

# =========================
# ASSET PATHS
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = BASE_DIR if os.path.exists(os.path.join(BASE_DIR, "assets")) else os.path.dirname(BASE_DIR)
ASSET_DIR = os.path.join(PROJECT_DIR, "assets")
IMAGE_DIR = os.path.join(ASSET_DIR, "images", "imgs-128px")
SOUND_DIR = os.path.join(ASSET_DIR, "sounds")

# =========================
# LOAD PIECE IMAGES
# =========================

PIECE_IMAGES = {}

def load_piece_images():
    mapping = {
        ("white", "P"): "white_pawn.png",
        ("white", "R"): "white_rook.png",
        ("white", "N"): "white_knight.png",
        ("white", "B"): "white_bishop.png",
        ("white", "Q"): "white_queen.png",
        ("white", "K"): "white_king.png",

        ("black", "P"): "black_pawn.png",
        ("black", "R"): "black_rook.png",
        ("black", "N"): "black_knight.png",
        ("black", "B"): "black_bishop.png",
        ("black", "Q"): "black_queen.png",
        ("black", "K"): "black_king.png",
    }

    for (color, kind), filename in mapping.items():
        path = os.path.join(IMAGE_DIR, filename)
        img = pygame.image.load(path).convert_alpha()
        PIECE_IMAGES[color[0] + kind] = pygame.transform.smoothscale(img, (SQSIZE, SQSIZE))

load_piece_images()

# =========================
# OPTIONAL SOUNDS
# =========================

def load_sound(name):
    path = os.path.join(SOUND_DIR, name)
    if os.path.exists(path):
        return pygame.mixer.Sound(path)
    return None

MOVE_SOUND = load_sound("move.wav")
CAPTURE_SOUND = load_sound("capture.wav")
CHECK_SOUND = load_sound("check.wav")

# =========================
# BOT DIFFICULTY (DEFAULT)
# =========================

bot_depth = 3   # will be changed by difficulty menu

# =========================
# CHESS ENGINE
# =========================

WHITE = "white"
BLACK = "black"

PIECE_VALUES = {
    "P": 100,
    "N": 320,
    "B": 330,
    "R": 500,
    "Q": 900,
    "K": 20000
}

class Piece:
    def __init__(self, color, kind, moved=False):
        self.color = color
        self.kind = kind  # 'P','N','B','R','Q','K'
        self.moved = moved

    def __repr__(self):
        return f"{self.color[0]}{self.kind}{'*' if self.moved else ''}"


def create_start_board():
    board = [[None for _ in range(8)] for _ in range(8)]

    # Pawns
    for c in range(8):
        board[6][c] = Piece(WHITE, "P")
        board[1][c] = Piece(BLACK, "P")

    # Rooks
    board[7][0] = Piece(WHITE, "R")
    board[7][7] = Piece(WHITE, "R")
    board[0][0] = Piece(BLACK, "R")
    board[0][7] = Piece(BLACK, "R")

    # Knights
    board[7][1] = Piece(WHITE, "N")
    board[7][6] = Piece(WHITE, "N")
    board[0][1] = Piece(BLACK, "N")
    board[0][6] = Piece(BLACK, "N")

    # Bishops
    board[7][2] = Piece(WHITE, "B")
    board[7][5] = Piece(WHITE, "B")
    board[0][2] = Piece(BLACK, "B")
    board[0][5] = Piece(BLACK, "B")

    # Queens
    board[7][3] = Piece(WHITE, "Q")
    board[0][3] = Piece(BLACK, "Q")

    # Kings
    board[7][4] = Piece(WHITE, "K")
    board[0][4] = Piece(BLACK, "K")

    return board


def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def is_enemy(piece, color):
    return piece is not None and piece.color != color


def is_friend(piece, color):
    return piece is not None and piece.color == color


def clone_board(board):
    return [[board[r][c] if board[r][c] is None else Piece(board[r][c].color, board[r][c].kind, board[r][c].moved)
             for c in range(8)] for r in range(8)]


def other(color):
    return WHITE if color == BLACK else BLACK


def move_parts(move):
    return move[0], move[1], move[2], move[3]


def move_flag(move):
    return move[4] if len(move) > 4 else ""


def same_square_move(a, b):
    return tuple(a[:4]) == tuple(b[:4])


def find_matching_move(target_move, legal_moves):
    for move in legal_moves:
        if same_square_move(move, target_move):
            return move
    return None


def find_king(board, color):
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p and p.color == color and p.kind == "K":
                return r, c
    return None


def target_is_enemy_king(board, r, c, color):
    target = board[r][c]
    return target is not None and target.color != color and target.kind == "K"


def is_square_attacked(board, row, col, by_color):
    """True when by_color attacks (row, col). Pawns are handled as attacks only,
    not as normal forward moves. This fixes false check/checkmate detection."""
    pawn_dir = -1 if by_color == WHITE else 1
    for dc in (-1, 1):
        pr, pc = row - pawn_dir, col - dc
        if in_bounds(pr, pc):
            p = board[pr][pc]
            if p and p.color == by_color and p.kind == "P":
                return True

    for dr, dc in [(2, 1), (2, -1), (-2, 1), (-2, -1),
                   (1, 2), (1, -2), (-1, 2), (-1, -2)]:
        nr, nc = row + dr, col + dc
        if in_bounds(nr, nc):
            p = board[nr][nc]
            if p and p.color == by_color and p.kind == "N":
                return True

    # Bishop/queen diagonals
    for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        nr, nc = row + dr, col + dc
        while in_bounds(nr, nc):
            p = board[nr][nc]
            if p:
                if p.color == by_color and p.kind in ("B", "Q"):
                    return True
                break
            nr += dr
            nc += dc

    # Rook/queen lines
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = row + dr, col + dc
        while in_bounds(nr, nc):
            p = board[nr][nc]
            if p:
                if p.color == by_color and p.kind in ("R", "Q"):
                    return True
                break
            nr += dr
            nc += dc

    # King attacks
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = row + dr, col + dc
            if in_bounds(nr, nc):
                p = board[nr][nc]
                if p and p.color == by_color and p.kind == "K":
                    return True

    return False


def is_in_check(board, color):
    king_pos = find_king(board, color)
    if not king_pos:
        return True
    return is_square_attacked(board, king_pos[0], king_pos[1], other(color))


def generate_moves_for_piece(board, r, c, en_passant_target=None, include_castling=True):
    moves = []
    piece = board[r][c]
    if not piece:
        return moves

    color = piece.color
    kind = piece.kind
    directions = []

    # Pawn
    if kind == "P":
        dir = -1 if color == WHITE else 1
        start_row = 6 if color == WHITE else 1

        # forward one and two squares
        nr = r + dir
        if in_bounds(nr, c) and board[nr][c] is None:
            flag = "promotion" if nr in (0, 7) else ""
            moves.append((r, c, nr, c, flag))
            nr2 = r + 2 * dir
            if r == start_row and in_bounds(nr2, c) and board[nr2][c] is None:
                moves.append((r, c, nr2, c, "double_pawn"))

        # normal captures + promotion captures
        for dc in [-1, 1]:
            nc = c + dc
            nr = r + dir
            if in_bounds(nr, nc):
                target = board[nr][nc]
                if target and target.color != color and target.kind != "K":
                    flag = "promotion" if nr in (0, 7) else ""
                    moves.append((r, c, nr, nc, flag))

        # en passant capture
        if en_passant_target:
            ep_r, ep_c = en_passant_target
            if ep_r == r + dir and abs(ep_c - c) == 1:
                adjacent = board[r][ep_c]
                if adjacent and adjacent.color != color and adjacent.kind == "P":
                    moves.append((r, c, ep_r, ep_c, "en_passant"))

    # Knight
    elif kind == "N":
        jumps = [(2, 1), (2, -1), (-2, 1), (-2, -1),
                 (1, 2), (1, -2), (-1, 2), (-1, -2)]
        for dr, dc in jumps:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc) and not is_friend(board[nr][nc], color) and not target_is_enemy_king(board, nr, nc, color):
                moves.append((r, c, nr, nc, ""))

    # Bishop
    elif kind == "B":
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

    # Rook
    elif kind == "R":
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    # Queen
    elif kind == "Q":
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1),
                      (-1, 0), (1, 0), (0, -1), (0, 1)]

    # King
    elif kind == "K":
        steps = [(-1, -1), (-1, 0), (-1, 1),
                 (0, -1),          (0, 1),
                 (1, -1),  (1, 0), (1, 1)]
        for dr, dc in steps:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc) and not is_friend(board[nr][nc], color) and not target_is_enemy_king(board, nr, nc, color):
                moves.append((r, c, nr, nc, ""))

        # Castling: king and rook have not moved, path is clear, and king does not pass through check.
        if include_castling and not piece.moved and not is_in_check(board, color):
            home_row = 7 if color == WHITE else 0
            enemy = other(color)
            if r == home_row and c == 4:
                # Kingside castling: e1/e8 to g1/g8; rook h-file to f-file
                rook = board[home_row][7]
                if (rook and rook.color == color and rook.kind == "R" and not rook.moved and
                        board[home_row][5] is None and board[home_row][6] is None and
                        not is_square_attacked(board, home_row, 5, enemy) and
                        not is_square_attacked(board, home_row, 6, enemy)):
                    moves.append((r, c, home_row, 6, "castle_kingside"))

                # Queenside castling: e1/e8 to c1/c8; rook a-file to d-file
                rook = board[home_row][0]
                if (rook and rook.color == color and rook.kind == "R" and not rook.moved and
                        board[home_row][1] is None and board[home_row][2] is None and board[home_row][3] is None and
                        not is_square_attacked(board, home_row, 3, enemy) and
                        not is_square_attacked(board, home_row, 2, enemy)):
                    moves.append((r, c, home_row, 2, "castle_queenside"))

    # Sliding pieces (Bishop, Rook, Queen)
    if directions:
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            while in_bounds(nr, nc):
                if board[nr][nc] is None:
                    moves.append((r, c, nr, nc, ""))
                else:
                    if board[nr][nc].color != color and board[nr][nc].kind != "K":
                        moves.append((r, c, nr, nc, ""))
                    break
                nr += dr
                nc += dc

    return moves


def get_next_en_passant_target(board, move):
    r1, c1, r2, c2 = move_parts(move)
    piece = board[r1][c1]
    if piece and piece.kind == "P" and abs(r2 - r1) == 2:
        return ((r1 + r2) // 2, c1)
    return None


def make_move(board, move):
    r1, c1, r2, c2 = move_parts(move)
    flag = move_flag(move)
    piece = board[r1][c1]

    record = {
        "captured": board[r2][c2],
        "captured_square": (r2, c2),
        "piece_prev_kind": piece.kind if piece else None,
        "piece_prev_moved": piece.moved if piece else False,
        "rook_move": None,
    }

    # En passant captures the pawn behind the target square, not on the target square.
    if flag == "en_passant":
        cap_r, cap_c = r1, c2
        record["captured"] = board[cap_r][cap_c]
        record["captured_square"] = (cap_r, cap_c)
        board[cap_r][cap_c] = None

    board[r2][c2] = piece
    board[r1][c1] = None
    if piece:
        piece.moved = True

    # Move rook for castling.
    if flag == "castle_kingside":
        rook_from = (r1, 7)
        rook_to = (r1, 5)
        rook = board[rook_from[0]][rook_from[1]]
        record["rook_move"] = (rook_from, rook_to, rook.moved if rook else False)
        board[rook_to[0]][rook_to[1]] = rook
        board[rook_from[0]][rook_from[1]] = None
        if rook:
            rook.moved = True
    elif flag == "castle_queenside":
        rook_from = (r1, 0)
        rook_to = (r1, 3)
        rook = board[rook_from[0]][rook_from[1]]
        record["rook_move"] = (rook_from, rook_to, rook.moved if rook else False)
        board[rook_to[0]][rook_to[1]] = rook
        board[rook_from[0]][rook_from[1]] = None
        if rook:
            rook.moved = True

    # Auto promote to queen. The previous kind is restored in undo_move.
    if piece and piece.kind == "P" and r2 in (0, 7):
        piece.kind = "Q"

    return record


def undo_move(board, move, record):
    r1, c1, r2, c2 = move_parts(move)
    piece = board[r2][c2]

    # Move rook back first if castling.
    if record.get("rook_move"):
        rook_from, rook_to, rook_prev_moved = record["rook_move"]
        rook = board[rook_to[0]][rook_to[1]]
        board[rook_from[0]][rook_from[1]] = rook
        board[rook_to[0]][rook_to[1]] = None
        if rook:
            rook.moved = rook_prev_moved

    board[r1][c1] = piece
    board[r2][c2] = None

    if piece:
        piece.kind = record["piece_prev_kind"]
        piece.moved = record["piece_prev_moved"]

    captured = record.get("captured")
    cap_square = record.get("captured_square", (r2, c2))
    if captured:
        board[cap_square[0]][cap_square[1]] = captured
    else:
        # Normal non-capture moves should keep the destination empty after undo.
        board[r2][c2] = None


def generate_legal_moves(board, color, en_passant_target=None):
    legal_moves = []
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p and p.color == color:
                for move in generate_moves_for_piece(board, r, c, en_passant_target, include_castling=True):
                    record = make_move(board, move)
                    if not is_in_check(board, color):
                        legal_moves.append(move)
                    undo_move(board, move, record)
    return legal_moves


# Piece-square tables are from White's perspective. Black pieces use the mirrored row.
PST = {
    "P": [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [50, 50, 50, 50, 50, 50, 50, 50],
        [10, 10, 20, 30, 30, 20, 10, 10],
        [5, 5, 10, 25, 25, 10, 5, 5],
        [0, 0, 0, 20, 20, 0, 0, 0],
        [5, -5, -10, 0, 0, -10, -5, 5],
        [5, 10, 10, -20, -20, 10, 10, 5],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ],
    "N": [
        [-50, -40, -30, -30, -30, -30, -40, -50],
        [-40, -20, 0, 5, 5, 0, -20, -40],
        [-30, 5, 10, 15, 15, 10, 5, -30],
        [-30, 0, 15, 20, 20, 15, 0, -30],
        [-30, 5, 15, 20, 20, 15, 5, -30],
        [-30, 0, 10, 15, 15, 10, 0, -30],
        [-40, -20, 0, 0, 0, 0, -20, -40],
        [-50, -40, -30, -30, -30, -30, -40, -50],
    ],
    "B": [
        [-20, -10, -10, -10, -10, -10, -10, -20],
        [-10, 5, 0, 0, 0, 0, 5, -10],
        [-10, 10, 10, 10, 10, 10, 10, -10],
        [-10, 0, 10, 10, 10, 10, 0, -10],
        [-10, 5, 5, 10, 10, 5, 5, -10],
        [-10, 0, 5, 10, 10, 5, 0, -10],
        [-10, 0, 0, 0, 0, 0, 0, -10],
        [-20, -10, -10, -10, -10, -10, -10, -20],
    ],
    "R": [
        [0, 0, 0, 5, 5, 0, 0, 0],
        [-5, 0, 0, 0, 0, 0, 0, -5],
        [-5, 0, 0, 0, 0, 0, 0, -5],
        [-5, 0, 0, 0, 0, 0, 0, -5],
        [-5, 0, 0, 0, 0, 0, 0, -5],
        [-5, 0, 0, 0, 0, 0, 0, -5],
        [5, 10, 10, 10, 10, 10, 10, 5],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ],
    "Q": [
        [-20, -10, -10, -5, -5, -10, -10, -20],
        [-10, 0, 0, 0, 0, 0, 0, -10],
        [-10, 0, 5, 5, 5, 5, 0, -10],
        [-5, 0, 5, 5, 5, 5, 0, -5],
        [0, 0, 5, 5, 5, 5, 0, -5],
        [-10, 5, 5, 5, 5, 5, 0, -10],
        [-10, 0, 5, 0, 0, 0, 0, -10],
        [-20, -10, -10, -5, -5, -10, -10, -20],
    ],
    "K": [
        [20, 30, 10, 0, 0, 10, 30, 20],
        [20, 20, 0, 0, 0, 0, 20, 20],
        [-10, -20, -20, -20, -20, -20, -20, -10],
        [-20, -30, -30, -40, -40, -30, -30, -20],
        [-30, -40, -40, -50, -50, -40, -40, -30],
        [-30, -40, -40, -50, -50, -40, -40, -30],
        [-30, -40, -40, -50, -50, -40, -40, -30],
        [-30, -40, -40, -50, -50, -40, -40, -30],
    ],
}

CHECKMATE_SCORE = 1000000


def evaluate_board(board):
    score = 0
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if not p:
                continue
            base = PIECE_VALUES[p.kind]
            table_row = r if p.color == WHITE else 7 - r
            positional = PST[p.kind][table_row][c]
            value = base + positional
            score += value if p.color == WHITE else -value

    # Keep evaluation lightweight so the Pygame window does not freeze after a move.
    # Mobility was removed from the leaf evaluation because it recursively generated
    # legal moves at every minimax leaf and made the AI feel like the game had crashed.
    return score


def move_score_for_ordering(board, move):
    r1, c1, r2, c2 = move_parts(move)
    flag = move_flag(move)
    moving = board[r1][c1]
    captured = board[r2][c2]
    score = 0

    if captured:
        score += 10 * PIECE_VALUES[captured.kind] - PIECE_VALUES[moving.kind]
    if flag == "en_passant":
        score += 900
    if flag in ("promotion",):
        score += 850
    if flag.startswith("castle"):
        score += 80

    # Prefer central development slightly.
    if (r2, c2) in [(3, 3), (3, 4), (4, 3), (4, 4)]:
        score += 25
    if moving and moving.kind in ("N", "B") and not moving.moved:
        score += 12
    return score


def ordered_moves(board, moves):
    moves = list(moves)
    random.shuffle(moves)
    moves.sort(key=lambda m: move_score_for_ordering(board, m), reverse=True)
    return moves


def minimax(board, depth, alpha, beta, maximizing, color_to_move, en_passant_target=None):
    # The board evaluation is positive for White and negative for Black.
    maximizing = (color_to_move == WHITE)

    legal_moves = generate_legal_moves(board, color_to_move, en_passant_target)
    if depth == 0 or not legal_moves:
        if not legal_moves:
            if is_in_check(board, color_to_move):
                return ((-CHECKMATE_SCORE - depth) if color_to_move == WHITE else (CHECKMATE_SCORE + depth)), None
            return 0, None
        return evaluate_board(board), None

    enemy = other(color_to_move)
    best_move = None

    if maximizing:
        best_eval = -math.inf
        for move in ordered_moves(board, legal_moves):
            next_ep = get_next_en_passant_target(board, move)
            record = make_move(board, move)
            eval_score, _ = minimax(board, depth - 1, alpha, beta, False, enemy, next_ep)
            undo_move(board, move, record)

            if eval_score > best_eval:
                best_eval = eval_score
                best_move = move
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return best_eval, best_move

    else:
        best_eval = math.inf
        for move in ordered_moves(board, legal_moves):
            next_ep = get_next_en_passant_target(board, move)
            record = make_move(board, move)
            eval_score, _ = minimax(board, depth - 1, alpha, beta, True, enemy, next_ep)
            undo_move(board, move, record)

            if eval_score < best_eval:
                best_eval = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return best_eval, best_move


def opening_book_move(board, color, legal_moves, move_stack):
    """Small opening book for natural early development. It is only used when the
    book move is legal, then minimax takes over after the opening."""
    if color != BLACK or len(move_stack) > 8:
        return None

    history = [tuple(item["move"][:4]) for item in move_stack]
    book = {
        ((6, 4, 4, 4),): [(1, 4, 3, 4), (1, 2, 3, 2), (1, 3, 3, 3)],  # vs e4: e5/c5/d5
        ((6, 3, 4, 3),): [(1, 3, 3, 3), (0, 6, 2, 5)],              # vs d4: d5/Nf6
        ((6, 2, 4, 2),): [(1, 4, 3, 4), (0, 6, 2, 5)],              # vs c4: e5/Nf6
        ((7, 6, 5, 5),): [(1, 3, 3, 3), (0, 6, 2, 5)],              # vs Nf3
        ((6, 4, 4, 4), (1, 4, 3, 4), (7, 6, 5, 5)): [(0, 1, 2, 2), (0, 6, 2, 5)],
        ((6, 4, 4, 4), (1, 4, 3, 4), (7, 5, 4, 2)): [(0, 1, 2, 2), (0, 6, 2, 5)],
        ((6, 3, 4, 3), (1, 3, 3, 3), (7, 6, 5, 5)): [(0, 6, 2, 5), (1, 4, 2, 4)],
    }

    candidates = book.get(tuple(history))
    if not candidates:
        return None

    legal_first4 = {tuple(m[:4]): m for m in legal_moves}
    random.shuffle(candidates)
    for candidate in candidates:
        if tuple(candidate) in legal_first4:
            return legal_first4[tuple(candidate)]
    return None


def choose_ai_move(board, color, depth, en_passant_target, move_stack):
    legal_moves = generate_legal_moves(board, color, en_passant_target)
    if not legal_moves:
        return 0, None

    book_move = opening_book_move(board, color, legal_moves, move_stack)
    if book_move:
        return evaluate_board(board), book_move

    return minimax(board, depth, -math.inf, math.inf, color == WHITE, color, en_passant_target)


def get_game_status(board, current_turn, en_passant_target):
    legal_moves = generate_legal_moves(board, current_turn, en_passant_target)
    if legal_moves:
        if is_in_check(board, current_turn):
            return {"type": "check", "title": "Check", "message": f"{'White' if current_turn == WHITE else 'Black'} is in check."}
        return None

    if is_in_check(board, current_turn):
        winner = "Black" if current_turn == WHITE else "White"
        return {
            "type": "checkmate",
            "title": "Checkmate",
            "message": f"{winner} wins by checkmate!",
        }
    return {
        "type": "stalemate",
        "title": "Stalemate",
        "message": "Draw: the player to move has no legal moves and is not in check.",
    }

# =========================
# UI HELPERS, BOARD, DRAGGER, PIECE DRAWING, LEGAL MOVE DOTS
# =========================

class Dragger:
    def __init__(self):
        self.dragging = False
        self.piece = None
        self.start_row = None
        self.start_col = None
        self.mouse_x = 0
        self.mouse_y = 0

    def start_drag(self, piece, row, col, mouse_pos):
        self.dragging = True
        self.piece = piece
        self.start_row = row
        self.start_col = col
        self.mouse_x, self.mouse_y = mouse_pos

    def update_mouse(self, pos):
        self.mouse_x, self.mouse_y = pos

    def stop_drag(self):
        self.dragging = False
        self.piece = None
        self.start_row = None
        self.start_col = None


def draw_vertical_gradient(surface, top_color, bottom_color):
    """Simple background gradient so the game does not look like a flat block."""
    h = surface.get_height()
    for y in range(h):
        t = y / max(1, h - 1)
        col = (
            int(top_color[0] * (1 - t) + bottom_color[0] * t),
            int(top_color[1] * (1 - t) + bottom_color[1] * t),
            int(top_color[2] * (1 - t) + bottom_color[2] * t),
        )
        pygame.draw.line(surface, col, (0, y), (surface.get_width(), y))


def blit_text(surface, text, font, color, pos, anchor="topleft"):
    surf = font.render(text, True, color)
    rect = surf.get_rect()
    setattr(rect, anchor, pos)
    surface.blit(surf, rect)
    return rect


def draw_soft_shadow(surface, rect, radius=18):
    for i, alpha in [(12, 35), (8, 42), (4, 55)]:
        shadow = pygame.Surface((rect.w + i * 2, rect.h + i * 2), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, alpha), shadow.get_rect(), border_radius=radius + i)
        surface.blit(shadow, (rect.x - i // 2, rect.y + i // 2))


def draw_card(surface, rect, fill=COLOR_CARD, border=COLOR_BORDER, radius=16, alpha=235):
    draw_soft_shadow(surface, rect, radius)
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, (*fill, alpha), panel.get_rect(), border_radius=radius)
    pygame.draw.rect(panel, (*border, 180), panel.get_rect(), width=1, border_radius=radius)
    surface.blit(panel, rect.topleft)


def draw_button(surface, rect, text, primary=False, disabled=False):
    if disabled:
        fill = (45, 51, 59)
        border = (69, 75, 85)
        text_color = COLOR_DISABLED
    elif primary:
        fill = COLOR_ACCENT
        border = (255, 232, 157)
        text_color = (30, 24, 12)
    else:
        fill = (42, 50, 61)
        border = (79, 91, 105)
        text_color = COLOR_TEXT

    draw_card(surface, rect, fill=fill, border=border, radius=10, alpha=245)
    blit_text(surface, text, FONT_BUTTON, text_color, rect.center, "center")


def draw_piece_icon(surface, piece, x, y, size=28):
    if not piece:
        return
    key = piece.color[0] + piece.kind
    img = pygame.transform.smoothscale(PIECE_IMAGES[key], (size, size))
    surface.blit(img, (x, y))


def board_coords_from_mouse(mx, my):
    if BOARD_X <= mx < BOARD_X + BOARD_SIZE and BOARD_Y <= my < BOARD_Y + BOARD_SIZE:
        return (my - BOARD_Y) // SQSIZE, (mx - BOARD_X) // SQSIZE
    return None


def draw_piece(surface, piece, r, c):
    key = piece.color[0] + piece.kind
    img = PIECE_IMAGES[key]
    x = BOARD_X + c * SQSIZE
    y = BOARD_Y + r * SQSIZE
    surface.blit(img, (x, y))


def draw_piece_at(surface, piece, x, y):
    key = piece.color[0] + piece.kind
    img = PIECE_IMAGES[key]
    rect = img.get_rect(center=(x, y))
    surface.blit(img, rect)


def draw_board(surface, board, last_move, hover_square, dragger, en_passant_target=None):
    # Outer frame and border
    frame_rect = pygame.Rect(BOARD_X - 14, BOARD_Y - 14, BOARD_SIZE + 28, BOARD_SIZE + 28)
    draw_card(surface, frame_rect, fill=COLOR_BOARD_FRAME, border=COLOR_BOARD_BORDER, radius=18, alpha=255)

    # Draw squares
    for r in range(8):
        for c in range(8):
            color = COLOR_LIGHT if (r + c) % 2 == 0 else COLOR_DARK
            rect = pygame.Rect(BOARD_X + c * SQSIZE, BOARD_Y + r * SQSIZE, SQSIZE, SQSIZE)
            pygame.draw.rect(surface, color, rect)

            # subtle texture lines to stop the board looking flat
            if (r + c) % 2 == 0:
                pygame.draw.line(surface, (255, 255, 255, 16), rect.topleft, rect.topright)
            else:
                pygame.draw.line(surface, (0, 0, 0, 18), rect.bottomleft, rect.bottomright)

    # Highlight last move. Moves may be 4-tuples or 5-tuples with a special-rule flag.
    if last_move:
        r1, c1, r2, c2 = move_parts(last_move)
        for rr, cc in [(r1, c1), (r2, c2)]:
            rect = pygame.Rect(BOARD_X + cc * SQSIZE, BOARD_Y + rr * SQSIZE, SQSIZE, SQSIZE)
            s = pygame.Surface((SQSIZE, SQSIZE), pygame.SRCALPHA)
            s.fill((*COLOR_LAST_MOVE, 105))
            surface.blit(s, rect.topleft)

    # Selected square glow
    if dragger.dragging:
        rect = pygame.Rect(BOARD_X + dragger.start_col * SQSIZE, BOARD_Y + dragger.start_row * SQSIZE, SQSIZE, SQSIZE)
        s = pygame.Surface((SQSIZE, SQSIZE), pygame.SRCALPHA)
        pygame.draw.rect(s, (*COLOR_SELECTED, 95), s.get_rect(), border_radius=8)
        pygame.draw.rect(s, (*COLOR_SELECTED, 230), s.get_rect(), width=4, border_radius=8)
        surface.blit(s, rect.topleft)

    # Hover highlight
    if hover_square:
        hr, hc = hover_square
        rect = pygame.Rect(BOARD_X + hc * SQSIZE, BOARD_Y + hr * SQSIZE, SQSIZE, SQSIZE)
        s = pygame.Surface((SQSIZE, SQSIZE), pygame.SRCALPHA)
        pygame.draw.rect(s, (*COLOR_HIGHLIGHT, 55), s.get_rect(), border_radius=6)
        pygame.draw.rect(s, (*COLOR_HIGHLIGHT, 120), s.get_rect(), width=2, border_radius=6)
        surface.blit(s, rect.topleft)

    # Legal move dots and capture rings
    if dragger.dragging and dragger.piece:
        legal_moves = generate_legal_moves(board, dragger.piece.color, en_passant_target)
        for m in legal_moves:
            r1, c1, r2, c2 = move_parts(m)
            if r1 == dragger.start_row and c1 == dragger.start_col:
                cx = BOARD_X + c2 * SQSIZE + SQSIZE // 2
                cy = BOARD_Y + r2 * SQSIZE + SQSIZE // 2
                if board[r2][c2]:
                    pygame.draw.circle(surface, (*COLOR_LEGAL, 230), (cx, cy), SQSIZE // 2 - 10, 5)
                else:
                    dot = pygame.Surface((SQSIZE, SQSIZE), pygame.SRCALPHA)
                    pygame.draw.circle(dot, (*COLOR_LEGAL, 165), (SQSIZE // 2, SQSIZE // 2), max(7, SQSIZE // 10))
                    surface.blit(dot, (BOARD_X + c2 * SQSIZE, BOARD_Y + r2 * SQSIZE))

    # Draw pieces, skipping dragged piece
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece:
                if dragger.dragging and dragger.start_row == r and dragger.start_col == c:
                    continue
                draw_piece(surface, piece, r, c)

    # Coordinates outside board
    for i in range(8):
        rank = str(8 - i)
        file = "abcdefgh"[i]
        blit_text(surface, rank, FONT_COORD, COLOR_MUTED, (BOARD_X - 24, BOARD_Y + i * SQSIZE + SQSIZE // 2), "center")
        blit_text(surface, file, FONT_COORD, COLOR_MUTED, (BOARD_X + i * SQSIZE + SQSIZE // 2, BOARD_Y + BOARD_SIZE + 24), "center")

    # Draw dragged piece on top
    if dragger.dragging and dragger.piece:
        draw_piece_at(surface, dragger.piece, dragger.mouse_x, dragger.mouse_y)

# =========================
# RIGHT PANEL UI
# =========================

def format_time(seconds):
    seconds = max(0, int(seconds))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def draw_player_card(surface, rect, color, active, timer, captured):
    draw_card(surface, rect, fill=COLOR_CARD if active else COLOR_CARD_DARK, border=COLOR_ACCENT if active else COLOR_BORDER, radius=16)
    name = "White" if color == WHITE else "Black"
    avatar_piece = Piece(color, "P")

    avatar_rect = pygame.Rect(rect.x + 16, rect.y + 16, 54, 54)
    pygame.draw.rect(surface, (12, 16, 22), avatar_rect, border_radius=12)
    draw_piece_icon(surface, avatar_piece, avatar_rect.x + 6, avatar_rect.y + 6, 42)

    if active:
        pygame.draw.circle(surface, COLOR_GREEN, (rect.x + 83, rect.y + 33), 7)

    blit_text(surface, name, FONT_CARD_TITLE, COLOR_TEXT, (rect.x + 96, rect.y + 22))
    blit_text(surface, "Elo 1500" if color == WHITE else "Elo 1450", FONT_TINY, COLOR_MUTED, (rect.x + 98, rect.y + 54))

    timer_rect = pygame.Rect(rect.right - 118, rect.y + 18, 96, 48)
    pygame.draw.rect(surface, COLOR_GREEN if active else (30, 35, 43), timer_rect, border_radius=10)
    pygame.draw.rect(surface, COLOR_BORDER, timer_rect, width=1, border_radius=10)
    blit_text(surface, format_time(timer), FONT_TIMER, COLOR_TEXT, timer_rect.center, "center")

    blit_text(surface, "Captured Pieces", FONT_SMALL, COLOR_MUTED, (rect.x + 16, rect.y + 82))
    x = rect.x + 18
    y = rect.y + 106
    for p in captured[:10]:
        draw_piece_icon(surface, p, x, y, 30)
        x += 30


def draw_move_history(surface, rect, move_history):
    draw_card(surface, rect, fill=COLOR_MOVE_BG, border=COLOR_BORDER, radius=16)
    blit_text(surface, "Move History", FONT_TURN, COLOR_ACCENT, (rect.x + 18, rect.y + 15))
    blit_text(surface, "Game Info", FONT_SMALL, COLOR_MUTED, (rect.right - 102, rect.y + 18))
    pygame.draw.line(surface, COLOR_BORDER, (rect.x + 16, rect.y + 50), (rect.right - 16, rect.y + 50), 1)

    # Show the latest moves if the list grows.
    rows_available = max(1, (rect.h - 65) // 24)
    start_pair = max(0, (len(move_history) // 2) - rows_available + 1)
    y = rect.y + 60
    for pair_index in range(start_pair, (len(move_history) + 1) // 2):
        i = pair_index * 2
        move_num = pair_index + 1
        white_move = move_history[i] if i < len(move_history) else ""
        black_move = move_history[i + 1] if i + 1 < len(move_history) else ""
        row_rect = pygame.Rect(rect.x + 12, y - 2, rect.w - 24, 22)
        if i + 1 >= len(move_history) - 1:
            pygame.draw.rect(surface, (61, 69, 80), row_rect, border_radius=6)
            pygame.draw.circle(surface, COLOR_ACCENT, (row_rect.x + 8, row_rect.centery), 5)
        blit_text(surface, f"{move_num:>2}.", FONT_MOVE, COLOR_MUTED, (rect.x + 24, y))
        blit_text(surface, f"{white_move:<8}", FONT_MOVE, COLOR_TEXT, (rect.x + 72, y))
        blit_text(surface, black_move, FONT_MOVE, COLOR_TEXT, (rect.x + 178, y))
        y += 24


def draw_status_box(surface, rect, current_turn, mode, bot_thinking):
    draw_card(surface, rect, fill=COLOR_CARD_DARK, border=COLOR_BORDER, radius=16)
    pygame.draw.circle(surface, COLOR_TEXT, (rect.centerx, rect.y + 36), 11)
    pygame.draw.circle(surface, (190, 195, 204), (rect.centerx, rect.y + 36), 7)
    if bot_thinking:
        title = "AI thinking..."
        sub = "Calculating best move"
    else:
        title = f"{'White' if current_turn == WHITE else 'Black'} to move"
        sub = "Make your move" if not (mode == "pvb" and current_turn == BLACK) else "Computer turn"
    blit_text(surface, title, FONT_TURN, COLOR_TEXT, (rect.centerx, rect.y + 70), "center")
    blit_text(surface, sub, FONT_SMALL, COLOR_MUTED, (rect.centerx, rect.y + 102), "center")


def draw_right_panel(surface, move_history, captured_white, captured_black, chat_lines, current_turn, mode, bot_thinking, white_time, black_time):
    buttons = {}
    panel_rect = pygame.Rect(PANEL_X, PANEL_Y, PANEL_W, PANEL_H)
    draw_card(surface, panel_rect, fill=COLOR_PANEL, border=(45, 58, 74), radius=20, alpha=245)

    # Split the sidebar into an information column and a button column.
    control_w = max(150, int(PANEL_W * 0.34))
    info_w = PANEL_W - control_w - 18
    info_x = PANEL_X + 12
    control_x = info_x + info_w + 18
    y = PANEL_Y + 12

    top_card = pygame.Rect(info_x, y, info_w, 132)
    draw_player_card(surface, top_card, BLACK, current_turn == BLACK, black_time, captured_black)

    move_rect = pygame.Rect(info_x, top_card.bottom + 14, info_w, PANEL_H - 304)
    draw_move_history(surface, move_rect, move_history)

    bottom_card = pygame.Rect(info_x, move_rect.bottom + 14, info_w, 132)
    draw_player_card(surface, bottom_card, WHITE, current_turn == WHITE, white_time, captured_white)

    # Buttons panel
    game_rect = pygame.Rect(control_x, y, control_w - 12, 288)
    draw_card(surface, game_rect, fill=COLOR_CARD, border=COLOR_BORDER, radius=16)
    blit_text(surface, "Game", FONT_TURN, COLOR_TEXT, (game_rect.centerx, game_rect.y + 22), "center")

    button_y = game_rect.y + 58
    button_h = 42
    gap = 12
    button_specs = [
        ("new", "New Game", True, False),
        ("play_ai", "Play vs AI", False, mode == "pvb"),
        ("undo", "Undo Move", False, len(move_history) == 0),
        ("settings", "Settings", False, True),
        ("exit", "Exit Game", False, False),
    ]
    for key, label, primary, disabled in button_specs:
        rect = pygame.Rect(game_rect.x + 14, button_y, game_rect.w - 28, button_h)
        draw_button(surface, rect, label, primary=primary, disabled=disabled)
        buttons[key] = rect if not disabled else None
        button_y += button_h + gap

    status_rect = pygame.Rect(control_x, game_rect.bottom + 18, control_w - 12, 164)
    draw_status_box(surface, status_rect, current_turn, mode, bot_thinking)

    hint_rect = pygame.Rect(control_x, status_rect.bottom + 18, control_w - 12, 52)
    show_rect = pygame.Rect(control_x, hint_rect.bottom + 12, control_w - 12, 52)
    draw_button(surface, hint_rect, "Hint", disabled=True)
    draw_button(surface, show_rect, "Show Legal", disabled=True)

    # Small bot message strip
    if chat_lines:
        chat_rect = pygame.Rect(control_x, show_rect.bottom + 18, control_w - 12, max(70, PANEL_Y + PANEL_H - show_rect.bottom - 30))
        draw_card(surface, chat_rect, fill=COLOR_CARD_DARK, border=COLOR_BORDER, radius=16)
        blit_text(surface, "Bot", FONT_TURN, COLOR_ACCENT, (chat_rect.x + 14, chat_rect.y + 12))
        y_msg = chat_rect.y + 44
        for line in chat_lines[-3:]:
            blit_text(surface, line, FONT_CHAT, COLOR_TEXT, (chat_rect.x + 14, y_msg))
            y_msg += 22

    return buttons

# =========================
# MENU UI
# =========================

def draw_menu(surface):
    draw_vertical_gradient(surface, COLOR_BG_TOP, COLOR_BG_BOTTOM)
    center_x = WINDOW_WIDTH // 2
    center_y = WINDOW_HEIGHT // 2

    blit_text(surface, "♛ BONNYRIGG CHESS ENGINE", FONT_TITLE, COLOR_ACCENT, (center_x, center_y - 220), "center")
    blit_text(surface, "Choose a mode and start playing", FONT_SUBTITLE, COLOR_TEXT, (center_x, center_y - 162), "center")

    panel_width, panel_height = 360, 210
    spacing = 70
    left_panel = pygame.Rect(center_x - panel_width - spacing // 2, center_y - 65, panel_width, panel_height)
    right_panel = pygame.Rect(center_x + spacing // 2, center_y - 65, panel_width, panel_height)

    draw_card(surface, left_panel, fill=COLOR_CARD, border=COLOR_BORDER, radius=22)
    draw_card(surface, right_panel, fill=COLOR_CARD, border=COLOR_ACCENT, radius=22)

    blit_text(surface, "Player vs Player", FONT_MODE, COLOR_TEXT, (left_panel.centerx, left_panel.y + 72), "center")
    blit_text(surface, "Local two-player chess", FONT_SMALL, COLOR_MUTED, (left_panel.centerx, left_panel.y + 118), "center")
    draw_button(surface, pygame.Rect(left_panel.x + 70, left_panel.y + 150, left_panel.w - 140, 42), "Start", primary=False)

    blit_text(surface, "Player vs AI", FONT_MODE, COLOR_TEXT, (right_panel.centerx, right_panel.y + 72), "center")
    blit_text(surface, "Play against minimax AI", FONT_SMALL, COLOR_MUTED, (right_panel.centerx, right_panel.y + 118), "center")
    draw_button(surface, pygame.Rect(right_panel.x + 70, right_panel.y + 150, right_panel.w - 140, 42), "Choose", primary=True)

    blit_text(surface, "ESC to quit", FONT_SMALL, COLOR_MUTED, (center_x, WINDOW_HEIGHT - 48), "center")
    return left_panel, right_panel


# =========================
# DIFFICULTY MENU
# =========================

def draw_difficulty_menu(surface):
    draw_vertical_gradient(surface, COLOR_BG_TOP, COLOR_BG_BOTTOM)
    center_x = WINDOW_WIDTH // 2
    center_y = WINDOW_HEIGHT // 2

    blit_text(surface, "AI DIFFICULTY", FONT_TITLE, COLOR_ACCENT, (center_x, center_y - 220), "center")
    blit_text(surface, "Select how far the engine searches", FONT_SUBTITLE, COLOR_TEXT, (center_x, center_y - 162), "center")

    panel_width, panel_height = 280, 170
    spacing = 34
    easy_panel = pygame.Rect(center_x - panel_width - spacing - panel_width // 2, center_y - 55, panel_width, panel_height)
    med_panel = pygame.Rect(center_x - panel_width // 2, center_y - 55, panel_width, panel_height)
    hard_panel = pygame.Rect(center_x + panel_width // 2 + spacing, center_y - 55, panel_width, panel_height)

    panels = [
        (easy_panel, "Basic", "Depth 1", "Fast moves"),
        (med_panel, "Intermediate", "Depth 3", "Balanced"),
        (hard_panel, "Advanced", "Depth 3", "Stronger AI"),
    ]
    for rect, title, depth, desc in panels:
        draw_card(surface, rect, fill=COLOR_CARD, border=COLOR_ACCENT if title == "Intermediate" else COLOR_BORDER, radius=22)
        blit_text(surface, title, FONT_MODE, COLOR_TEXT, (rect.centerx, rect.y + 46), "center")
        blit_text(surface, depth, FONT_SMALL, COLOR_ACCENT, (rect.centerx, rect.y + 92), "center")
        blit_text(surface, desc, FONT_SMALL, COLOR_MUTED, (rect.centerx, rect.y + 124), "center")

    return easy_panel, med_panel, hard_panel

# =========================
# MAIN LOOP + BOT LOGIC
# =========================

def move_to_notation(board, move, record, gives_check=False, is_mate=False):
    r1, c1, r2, c2 = move_parts(move)
    flag = move_flag(move)
    piece = board[r2][c2]
    captured = record.get("captured") if isinstance(record, dict) else None

    if flag == "castle_kingside":
        notation = "O-O"
    elif flag == "castle_queenside":
        notation = "O-O-O"
    else:
        dest = f"{'abcdefgh'[c2]}{8 - r2}"
        capture_mark = "x" if captured else ""
        if piece.kind == "P":
            prefix = "" if not captured else "abcdefgh"[c1]
        else:
            prefix = piece.kind
        notation = f"{prefix}{capture_mark}{dest}"
        if flag == "promotion":
            notation += "=Q"
        if flag == "en_passant":
            notation += " e.p."

    if is_mate:
        notation += "#"
    elif gives_check:
        notation += "+"
    return notation


def bot_say(chat_lines, text):
    chat_lines.append("Bot: " + text)
    if len(chat_lines) > 50:
        chat_lines.pop(0)


def add_captured_piece(captured_white, captured_black, mover, captured):
    if not captured:
        return
    if mover == WHITE:
        captured_white.append(captured)
    else:
        captured_black.append(captured)


def remove_captured_piece(captured_white, captured_black, mover, captured):
    if not captured:
        return
    if mover == WHITE and captured_white:
        captured_white.pop()
    elif mover == BLACK and captured_black:
        captured_black.pop()


def apply_game_move(board, move, mover, move_history, move_stack, captured_white, captured_black, en_passant_target):
    prev_ep = en_passant_target
    next_ep = get_next_en_passant_target(board, move)
    record = make_move(board, move)
    captured = record.get("captured")
    add_captured_piece(captured_white, captured_black, mover, captured)

    next_turn = other(mover)
    status_after = get_game_status(board, next_turn, next_ep)
    gives_check = bool(status_after and status_after["type"] in ("check", "checkmate"))
    is_mate = bool(status_after and status_after["type"] == "checkmate")
    notation = move_to_notation(board, move, record, gives_check, is_mate)

    move_history.append(notation)
    move_stack.append({
        "move": move,
        "record": record,
        "mover": mover,
        "prev_ep": prev_ep,
        "next_ep": next_ep,
        "notation": notation,
    })
    return next_ep, status_after, notation


def undo_last_move(board, move_history, move_stack, captured_white, captured_black):
    if not move_stack:
        return None, None
    item = move_stack.pop()
    undo_move(board, item["move"], item["record"])
    remove_captured_piece(captured_white, captured_black, item["mover"], item["record"].get("captured"))
    if move_history:
        move_history.pop()
    return item["mover"], item["prev_ep"]


def draw_game_over_popup(surface, title, message):
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 155))
    surface.blit(overlay, (0, 0))

    popup_w, popup_h = 540, 290
    rect = pygame.Rect((WINDOW_WIDTH - popup_w) // 2, (WINDOW_HEIGHT - popup_h) // 2, popup_w, popup_h)
    draw_card(surface, rect, fill=(25, 31, 42), border=COLOR_ACCENT, radius=24, alpha=250)

    blit_text(surface, title, FONT_TITLE, COLOR_ACCENT, (rect.centerx, rect.y + 58), "center")
    blit_text(surface, message, FONT_SUBTITLE, COLOR_TEXT, (rect.centerx, rect.y + 128), "center")

    menu_button = pygame.Rect(rect.x + 56, rect.bottom - 88, 190, 52)
    exit_button = pygame.Rect(rect.right - 246, rect.bottom - 88, 190, 52)
    draw_button(surface, menu_button, "Main Menu", primary=True)
    draw_button(surface, exit_button, "Exit Game")
    return {"menu": menu_button, "exit": exit_button}


def run_game(mode):
    global bot_depth

    board = create_start_board()
    dragger = Dragger()
    move_history = []
    move_stack = []
    captured_white = []   # black pieces captured by White
    captured_black = []   # white pieces captured by Black
    chat_lines = ["Bot: Good luck!"] if mode == "pvb" else []
    current_turn = WHITE
    last_move = None
    hover_square = None
    white_time = 15 * 60
    black_time = 15 * 60
    buttons = {}
    popup_buttons = {}
    clock = pygame.time.Clock()
    en_passant_target = None
    game_over = None

    running = True
    bot_thinking = False

    while running:
        dt = clock.tick(60) / 1000

        if not game_over:
            if current_turn == WHITE:
                white_time -= dt
                if white_time <= 0:
                    game_over = {"type": "timeout", "title": "Time Out", "message": "Black wins on time!"}
            else:
                black_time -= dt
                if black_time <= 0:
                    game_over = {"type": "timeout", "title": "Time Out", "message": "White wins on time!"}

        draw_vertical_gradient(screen, COLOR_BG_TOP, COLOR_BG_BOTTOM)
        blit_text(screen, "♛ Chess", FONT_CARD_TITLE, COLOR_ACCENT, (WINDOW_WIDTH // 2, 22), "center")

        # BOT MOVE
        if (not game_over and mode == "pvb" and current_turn == BLACK and
                not dragger.dragging and not bot_thinking):
            bot_thinking = True
            draw_board(screen, board, last_move, hover_square, dragger, en_passant_target)
            buttons = draw_right_panel(screen, move_history, captured_white, captured_black, chat_lines,
                                       current_turn, mode, bot_thinking, white_time, black_time)
            pygame.display.update()

            score, bot_move = choose_ai_move(board, BLACK, bot_depth, en_passant_target, move_stack)

            if bot_move:
                en_passant_target, status_after, notation = apply_game_move(
                    board, bot_move, BLACK, move_history, move_stack, captured_white, captured_black, en_passant_target
                )

                captured = move_stack[-1]["record"].get("captured")
                if captured and CAPTURE_SOUND:
                    CAPTURE_SOUND.play()
                elif status_after and status_after["type"] in ("check", "checkmate") and CHECK_SOUND:
                    CHECK_SOUND.play()
                elif MOVE_SOUND:
                    MOVE_SOUND.play()

                last_move = bot_move
                current_turn = WHITE
                bot_say(chat_lines, f"I played {notation}")
                if status_after and status_after["type"] in ("checkmate", "stalemate"):
                    game_over = status_after
            else:
                game_over = get_game_status(board, current_turn, en_passant_target)
                bot_say(chat_lines, "I have no legal moves.")

            bot_thinking = False

        # EVENTS
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return

            # If the game is finished, only the popup buttons should work.
            if game_over:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    if popup_buttons.get("menu") and popup_buttons["menu"].collidepoint(mx, my):
                        return
                    if popup_buttons.get("exit") and popup_buttons["exit"].collidepoint(mx, my):
                        pygame.quit()
                        sys.exit()
                continue

            # Mouse movement
            if event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                dragger.update_mouse((mx, my))
                hover_square = board_coords_from_mouse(mx, my)

            # Mouse down
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos

                # Sidebar buttons
                if buttons.get("new") and buttons["new"].collidepoint(mx, my):
                    return
                if buttons.get("exit") and buttons["exit"].collidepoint(mx, my):
                    pygame.quit()
                    sys.exit()
                if buttons.get("play_ai") and buttons["play_ai"].collidepoint(mx, my):
                    mode = "pvb"
                    bot_depth = 3
                    if not chat_lines:
                        chat_lines.append("Bot: Good luck!")
                    bot_say(chat_lines, "AI mode enabled.")
                if buttons.get("undo") and buttons["undo"].collidepoint(mx, my):
                    # In player vs AI, undo both the AI move and the player's move if possible.
                    undone, prev_ep = undo_last_move(board, move_history, move_stack, captured_white, captured_black)
                    if prev_ep is not None or undone is not None:
                        en_passant_target = prev_ep
                    if mode == "pvb" and undone == BLACK:
                        undone, prev_ep = undo_last_move(board, move_history, move_stack, captured_white, captured_black)
                        if prev_ep is not None or undone is not None:
                            en_passant_target = prev_ep
                    current_turn = WHITE if mode == "pvb" else (undone or current_turn)
                    last_move = move_stack[-1]["move"] if move_stack else None
                    dragger.stop_drag()
                    continue

                pos = board_coords_from_mouse(mx, my)
                if pos and not (mode == "pvb" and current_turn == BLACK):
                    r, c = pos
                    piece = board[r][c]
                    if piece and piece.color == current_turn:
                        dragger.start_drag(piece, r, c, (mx, my))

            # Mouse up
            if event.type == pygame.MOUSEBUTTONUP:
                if dragger.dragging:
                    mx, my = event.pos
                    pos = board_coords_from_mouse(mx, my)

                    if pos:
                        r2, c2 = pos
                        attempted_move = (dragger.start_row, dragger.start_col, r2, c2)
                        legal_moves = generate_legal_moves(board, current_turn, en_passant_target)
                        move = find_matching_move(attempted_move, legal_moves)

                        if move:
                            mover = current_turn
                            en_passant_target, status_after, notation = apply_game_move(
                                board, move, mover, move_history, move_stack, captured_white, captured_black, en_passant_target
                            )

                            captured = move_stack[-1]["record"].get("captured")
                            if captured and CAPTURE_SOUND:
                                CAPTURE_SOUND.play()
                            elif status_after and status_after["type"] in ("check", "checkmate") and CHECK_SOUND:
                                CHECK_SOUND.play()
                            elif MOVE_SOUND:
                                MOVE_SOUND.play()

                            last_move = move
                            current_turn = other(current_turn)

                            if status_after and status_after["type"] in ("checkmate", "stalemate"):
                                game_over = status_after
                            elif current_turn == BLACK and mode == "pvb":
                                bot_say(chat_lines, "Thinking...")

                    dragger.stop_drag()

        # DRAW EVERYTHING
        draw_board(screen, board, last_move, hover_square, dragger, en_passant_target)
        buttons = draw_right_panel(screen, move_history, captured_white, captured_black, chat_lines,
                                   current_turn, mode, bot_thinking, white_time, black_time)
        if game_over:
            popup_buttons = draw_game_over_popup(screen, game_over["title"], game_over["message"])

        pygame.display.update()


# =========================
# MAIN PROGRAM ENTRY
# =========================

def main():
    global bot_depth

    in_menu = True
    choosing_difficulty = False
    mode = None

    while True:
        # MAIN MENU
        if in_menu:
            left_panel, right_panel = draw_menu(screen)
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos

                    # Player vs Player
                    if left_panel.collidepoint(mx, my):
                        mode = "pvp"
                        in_menu = False

                    # Player vs Bot → Difficulty menu
                    elif right_panel.collidepoint(mx, my):
                        choosing_difficulty = True
                        in_menu = False

        # DIFFICULTY MENU
        elif choosing_difficulty:
            easy_panel, med_panel, hard_panel = draw_difficulty_menu(screen)
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos

                    if easy_panel.collidepoint(mx, my):
                        bot_depth = 1
                        mode = "pvb"
                        choosing_difficulty = False

                    elif med_panel.collidepoint(mx, my):
                        bot_depth = 3
                        mode = "pvb"
                        choosing_difficulty = False

                    elif hard_panel.collidepoint(mx, my):
                        bot_depth = 3
                        mode = "pvb"
                        choosing_difficulty = False

        # START GAME
        else:
            run_game(mode)
            in_menu = True
            choosing_difficulty = False
            mode = None


if __name__ == "__main__":
    main()
