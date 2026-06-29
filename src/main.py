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

BOARD_SIZE = 900
RIGHT_PANEL_WIDTH = int(SCREEN_WIDTH * 0.35)
WINDOW_WIDTH = BOARD_SIZE + RIGHT_PANEL_WIDTH
WINDOW_HEIGHT = max(SCREEN_HEIGHT, BOARD_SIZE)

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Chess")

SQSIZE = BOARD_SIZE // 8

# =========================
# COLORS
# =========================

COLOR_BG = (15, 18, 25)
COLOR_LIGHT = (240, 217, 181)
COLOR_DARK = (181, 136, 99)
COLOR_HIGHLIGHT = (246, 246, 105)
COLOR_LAST_MOVE = (186, 202, 68)
COLOR_RIGHT_PANEL = (25, 28, 35)
COLOR_TEXT = (230, 230, 230)
COLOR_ACCENT = (255, 215, 0)
COLOR_CAPTURE_BG = (35, 38, 45)
COLOR_CHAT_BG = (30, 33, 40)
COLOR_MOVE_BG = (30, 33, 40)

# =========================
# FONTS
# =========================

FONT_TITLE = pygame.font.SysFont("serif", 80, bold=True)
FONT_SUBTITLE = pygame.font.SysFont("arial", 32)
FONT_MODE = pygame.font.SysFont("arial", 36)
FONT_SMALL = pygame.font.SysFont("arial", 22)
FONT_MOVE = pygame.font.SysFont("consolas", 20)
FONT_CHAT = pygame.font.SysFont("arial", 20)
FONT_TURN = pygame.font.SysFont("arial", 24, bold=True)

# =========================
# ASSET PATHS
# =========================

ASSET_DIR = "assets"
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
    def __init__(self, color, kind):
        self.color = color
        self.kind = kind  # 'P','N','B','R','Q','K'

    def __repr__(self):
        return f"{self.color[0]}{self.kind}"


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
    return [[board[r][c] if board[r][c] is None else Piece(board[r][c].color, board[r][c].kind)
             for c in range(8)] for r in range(8)]


def find_king(board, color):
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p and p.color == color and p.kind == "K":
                return r, c
    return None


def generate_moves_for_piece(board, r, c):
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

        # forward
        nr = r + dir
        if in_bounds(nr, c) and board[nr][c] is None:
            moves.append((r, c, nr, c))
            nr2 = r + 2 * dir
            if r == start_row and board[nr2][c] is None:
                moves.append((r, c, nr2, c))

        # captures
        for dc in [-1, 1]:
            nc = c + dc
            nr = r + dir
            if in_bounds(nr, nc) and board[nr][nc] and board[nr][nc].color != color:
                moves.append((r, c, nr, nc))

    # Knight
    elif kind == "N":
        jumps = [(2, 1), (2, -1), (-2, 1), (-2, -1),
                 (1, 2), (1, -2), (-1, 2), (-1, -2)]
        for dr, dc in jumps:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc) and not is_friend(board[nr][nc], color):
                moves.append((r, c, nr, nc))

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
            if in_bounds(nr, nc) and not is_friend(board[nr][nc], color):
                moves.append((r, c, nr, nc))

    # Sliding pieces (Bishop, Rook, Queen)
    if directions:
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            while in_bounds(nr, nc):
                if board[nr][nc] is None:
                    moves.append((r, c, nr, nc))
                else:
                    if board[nr][nc].color != color:
                        moves.append((r, c, nr, nc))
                    break
                nr += dr
                nc += dc

    return moves


def make_move(board, move):
    r1, c1, r2, c2 = move
    piece = board[r1][c1]
    captured = board[r2][c2]

    board[r2][c2] = piece
    board[r1][c1] = None

    # promotion
    if piece.kind == "P":
        if piece.color == WHITE and r2 == 0:
            piece.kind = "Q"
        if piece.color == BLACK and r2 == 7:
            piece.kind = "Q"

    return captured


def undo_move(board, move, captured):
    r1, c1, r2, c2 = move
    piece = board[r2][c2]
    board[r1][c1] = piece
    board[r2][c2] = captured


def is_in_check(board, color):
    king_pos = find_king(board, color)
    if not king_pos:
        return True

    kr, kc = king_pos
    enemy = WHITE if color == BLACK else BLACK

    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p and p.color == enemy:
                for m in generate_moves_for_piece(board, r, c):
                    _, _, tr, tc = m
                    if tr == kr and tc == kc:
                        return True

    return False


def generate_legal_moves(board, color):
    moves = []
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p and p.color == color:
                for m in generate_moves_for_piece(board, r, c):
                    captured = make_move(board, m)
                    if not is_in_check(board, color):
                        moves.append(m)
                    undo_move(board, m, captured)
    return moves


def evaluate_board(board):
    score = 0
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p:
                val = PIECE_VALUES[p.kind]
                score += val if p.color == WHITE else -val
    return score


def minimax(board, depth, alpha, beta, maximizing, color_to_move):
    if depth == 0:
        return evaluate_board(board), None

    moves = generate_legal_moves(board, color_to_move)
    if not moves:
        if is_in_check(board, color_to_move):
            return (-999999 if maximizing else 999999), None
        else:
            return 0, None

    enemy = WHITE if color_to_move == BLACK else BLACK
    best_move = None

    if maximizing:
        max_eval = -math.inf
        for m in moves:
            captured = make_move(board, m)
            eval_score, _ = minimax(board, depth - 1, alpha, beta, False, enemy)
            undo_move(board, m, captured)

            if eval_score > max_eval:
                max_eval = eval_score
                best_move = m

            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break

        return max_eval, best_move

    else:
        min_eval = math.inf
        for m in moves:
            captured = make_move(board, m)
            eval_score, _ = minimax(board, depth - 1, alpha, beta, True, enemy)
            undo_move(board, m, captured)

            if eval_score < min_eval:
                min_eval = eval_score
                best_move = m

            beta = min(beta, eval_score)
            if beta <= alpha:
                break

        return min_eval, best_move

# =========================
# UI: BOARD, DRAGGER, PIECE DRAWING, LEGAL MOVE DOTS
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


def draw_piece(surface, piece, r, c):
    key = piece.color[0] + piece.kind
    img = PIECE_IMAGES[key]
    x = c * SQSIZE
    y = r * SQSIZE
    surface.blit(img, (x, y))


def draw_piece_at(surface, piece, x, y):
    key = piece.color[0] + piece.kind
    img = PIECE_IMAGES[key]
    rect = img.get_rect(center=(x, y))
    surface.blit(img, rect)


def draw_board(surface, board, last_move, hover_square, dragger):
    # Draw squares
    for r in range(8):
        for c in range(8):
            color = COLOR_LIGHT if (r + c) % 2 == 0 else COLOR_DARK
            rect = pygame.Rect(c * SQSIZE, r * SQSIZE, SQSIZE, SQSIZE)
            pygame.draw.rect(surface, color, rect)

    # Highlight last move
    if last_move:
        r1, c1, r2, c2 = last_move
        for rr, cc in [(r1, c1), (r2, c2)]:
            rect = pygame.Rect(cc * SQSIZE, rr * SQSIZE, SQSIZE, SQSIZE)
            s = pygame.Surface((SQSIZE, SQSIZE), pygame.SRCALPHA)
            s.fill((*COLOR_LAST_MOVE, 120))
            surface.blit(s, rect.topleft)

    # Hover highlight
    if hover_square:
        hr, hc = hover_square
        rect = pygame.Rect(hc * SQSIZE, hr * SQSIZE, SQSIZE, SQSIZE)
        s = pygame.Surface((SQSIZE, SQSIZE), pygame.SRCALPHA)
        s.fill((*COLOR_HIGHLIGHT, 80))
        surface.blit(s, rect.topleft)

    # Draw pieces (skip dragged piece)
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece:
                if dragger.dragging and dragger.start_row == r and dragger.start_col == c:
                    continue
                draw_piece(surface, piece, r, c)

    # LEGAL MOVE DOTS
    if dragger.dragging:
        piece = dragger.piece
        legal_moves = generate_legal_moves(board, piece.color)
        for m in legal_moves:
            r1, c1, r2, c2 = m
            if r1 == dragger.start_row and c1 == dragger.start_col:
                cx = c2 * SQSIZE + SQSIZE // 2
                cy = r2 * SQSIZE + SQSIZE // 2
                pygame.draw.circle(surface, (0, 0, 0), (cx, cy), 12)

    # Draw dragged piece on top
    if dragger.dragging and dragger.piece:
        draw_piece_at(surface, dragger.piece, dragger.mouse_x, dragger.mouse_y)

# =========================
# RIGHT PANEL UI
# =========================

def draw_right_panel(surface, move_history, captured_white, captured_black, chat_lines, current_turn):
    panel_x = BOARD_SIZE
    panel_rect = pygame.Rect(panel_x, 0, RIGHT_PANEL_WIDTH, WINDOW_HEIGHT)
    pygame.draw.rect(surface, COLOR_RIGHT_PANEL, panel_rect)

    # Turn indicator
    turn_text = f"Turn: {'White' if current_turn == WHITE else 'Black'}"
    turn_surf = FONT_TURN.render(turn_text, True, COLOR_ACCENT)
    surface.blit(turn_surf, (panel_x + 20, 20))

    # Move list area
    move_area_y = 60
    move_area_h = WINDOW_HEIGHT * 0.35
    move_area_rect = pygame.Rect(panel_x + 10, move_area_y, RIGHT_PANEL_WIDTH - 20, int(move_area_h))
    pygame.draw.rect(surface, COLOR_MOVE_BG, move_area_rect, border_radius=8)

    title = FONT_SMALL.render("Moves", True, COLOR_TEXT)
    surface.blit(title, (move_area_rect.x + 10, move_area_rect.y + 5))

    # Render moves as numbered pairs
    y_offset = move_area_rect.y + 30
    line_height = 22
    for i in range(0, len(move_history), 2):
        move_num = i // 2 + 1
        white_move = move_history[i]
        black_move = move_history[i + 1] if i + 1 < len(move_history) else ""
        line = f"{move_num}. {white_move:<8} {black_move}"
        line_surf = FONT_MOVE.render(line, True, COLOR_TEXT)
        surface.blit(line_surf, (move_area_rect.x + 10, y_offset))
        y_offset += line_height
        if y_offset > move_area_rect.bottom - 10:
            break

    # Captured pieces area
    cap_area_y = move_area_rect.bottom + 10
    cap_area_h = WINDOW_HEIGHT * 0.15
    cap_area_rect = pygame.Rect(panel_x + 10, cap_area_y, RIGHT_PANEL_WIDTH - 20, int(cap_area_h))
    pygame.draw.rect(surface, COLOR_CAPTURE_BG, cap_area_rect, border_radius=8)

    cap_title = FONT_SMALL.render("Captured", True, COLOR_TEXT)
    surface.blit(cap_title, (cap_area_rect.x + 10, cap_area_rect.y + 5))

    # White captured (black pieces taken by white)
    y_white = cap_area_rect.y + 30
    label_white = FONT_SMALL.render("White:", True, COLOR_TEXT)
    surface.blit(label_white, (cap_area_rect.x + 10, y_white))
    x_offset = cap_area_rect.x + 80
    for p in captured_white:
        p_surf = FONT_SMALL.render(p.kind, True, COLOR_TEXT)
        surface.blit(p_surf, (x_offset, y_white))
        x_offset += 18

    # Black captured (white pieces taken by black)
    y_black = y_white + 24
    label_black = FONT_SMALL.render("Black:", True, COLOR_TEXT)
    surface.blit(label_black, (cap_area_rect.x + 10, y_black))
    x_offset = cap_area_rect.x + 80
    for p in captured_black:
        p_surf = FONT_SMALL.render(p.kind, True, COLOR_TEXT)
        surface.blit(p_surf, (x_offset, y_black))
        x_offset += 18

    # Chat area
    chat_area_y = cap_area_rect.bottom + 10
    chat_area_h = WINDOW_HEIGHT - chat_area_y - 20
    chat_area_rect = pygame.Rect(panel_x + 10, chat_area_y, RIGHT_PANEL_WIDTH - 20, int(chat_area_h))
    pygame.draw.rect(surface, COLOR_CHAT_BG, chat_area_rect, border_radius=8)

    chat_title = FONT_SMALL.render("Bot Chat", True, COLOR_TEXT)
    surface.blit(chat_title, (chat_area_rect.x + 10, chat_area_rect.y + 5))

    y_chat = chat_area_rect.y + 30
    for line in chat_lines[-8:]:
        chat_surf = FONT_CHAT.render(line, True, COLOR_TEXT)
        surface.blit(chat_surf, (chat_area_rect.x + 10, y_chat))
        y_chat += 22
        if y_chat > chat_area_rect.bottom - 10:
            break

# =========================
# MENU UI
# =========================

def draw_menu(surface):
    surface.fill(COLOR_BG)

    title_surf = FONT_TITLE.render("CHESS", True, COLOR_ACCENT)
    subtitle_surf = FONT_SUBTITLE.render("CHOOSE GAME MODE", True, COLOR_TEXT)

    center_x = WINDOW_WIDTH // 2
    center_y = WINDOW_HEIGHT // 2

    surface.blit(title_surf, title_surf.get_rect(center=(center_x, center_y - 200)))
    surface.blit(subtitle_surf, subtitle_surf.get_rect(center=(center_x, center_y - 140)))

    panel_width, panel_height = 300, 200
    spacing = 80

    left_panel = pygame.Rect(center_x - panel_width - spacing // 2, center_y - 50, panel_width, panel_height)
    right_panel = pygame.Rect(center_x + spacing // 2, center_y - 50, panel_width, panel_height)

    pygame.draw.rect(surface, (30, 30, 30), left_panel, border_radius=15)
    pygame.draw.rect(surface, (30, 30, 30), right_panel, border_radius=15)

    pvp_text = FONT_MODE.render("PLAYER VS PLAYER", True, COLOR_TEXT)
    pvb_text = FONT_MODE.render("PLAYER VS BOT", True, COLOR_TEXT)

    surface.blit(pvp_text, pvp_text.get_rect(center=(left_panel.centerx, left_panel.centery)))
    surface.blit(pvb_text, pvb_text.get_rect(center=(right_panel.centerx, right_panel.centery)))

    return left_panel, right_panel


# =========================
# DIFFICULTY MENU
# =========================

def draw_difficulty_menu(surface):
    surface.fill(COLOR_BG)

    title_surf = FONT_TITLE.render("DIFFICULTY", True, COLOR_ACCENT)
    subtitle_surf = FONT_SUBTITLE.render("CHOOSE BOT LEVEL", True, COLOR_TEXT)

    center_x = WINDOW_WIDTH // 2
    center_y = WINDOW_HEIGHT // 2

    surface.blit(title_surf, title_surf.get_rect(center=(center_x, center_y - 200)))
    surface.blit(subtitle_surf, subtitle_surf.get_rect(center=(center_x, center_y - 140)))

    panel_width, panel_height = 260, 150
    spacing = 40

    easy_panel = pygame.Rect(center_x - panel_width - spacing, center_y - 50, panel_width, panel_height)
    med_panel = pygame.Rect(center_x - panel_width//2, center_y - 50, panel_width, panel_height)
    hard_panel = pygame.Rect(center_x + spacing, center_y - 50, panel_width, panel_height)

    pygame.draw.rect(surface, (30, 30, 30), easy_panel, border_radius=15)
    pygame.draw.rect(surface, (30, 30, 30), med_panel, border_radius=15)
    pygame.draw.rect(surface, (30, 30, 30), hard_panel, border_radius=15)

    easy_text = FONT_MODE.render("EASY", True, COLOR_TEXT)
    med_text = FONT_MODE.render("MEDIUM", True, COLOR_TEXT)
    hard_text = FONT_MODE.render("HARD", True, COLOR_TEXT)

    surface.blit(easy_text, easy_text.get_rect(center=easy_panel.center))
    surface.blit(med_text, med_text.get_rect(center=med_panel.center))
    surface.blit(hard_text, hard_text.get_rect(center=hard_panel.center))

    return easy_panel, med_panel, hard_panel

# =========================
# MAIN LOOP + BOT LOGIC
# =========================

def move_to_notation(board, move, captured):
    r1, c1, r2, c2 = move
    piece = board[r2][c2]
    col_letter = "abcdefgh"[c2]
    row_number = 8 - r2
    prefix = piece.kind if piece.kind != "P" else "P"
    capture_mark = "x" if captured else "-"
    return f"{prefix}{capture_mark}{col_letter}{row_number}"


def bot_say(chat_lines, text):
    chat_lines.append("Bot: " + text)
    if len(chat_lines) > 50:
        chat_lines.pop(0)


def run_game(mode):
    global bot_depth

    board = create_start_board()
    dragger = Dragger()
    move_history = []
    captured_white = []
    captured_black = []
    chat_lines = ["Bot: Good luck!"] if mode == "pvb" else []
    current_turn = WHITE
    last_move = None
    hover_square = None

    running = True
    bot_thinking = False

    while running:
        screen.fill(COLOR_BG)

        # BOT MOVE
        if mode == "pvb" and current_turn == BLACK and not dragger.dragging and not bot_thinking:
            bot_thinking = True
            pygame.display.update()

            score, bot_move = minimax(board, bot_depth, -math.inf, math.inf, True, BLACK)

            if bot_move:
                r1, c1, r2, c2 = bot_move
                captured = make_move(board, bot_move)

                if captured and CAPTURE_SOUND:
                    CAPTURE_SOUND.play()
                elif MOVE_SOUND:
                    MOVE_SOUND.play()

                if captured:
                    captured_black.append(captured)

                notation = move_to_notation(board, bot_move, captured)
                move_history.append(notation)

                last_move = bot_move
                current_turn = WHITE

                bot_say(chat_lines, f"I played {notation}")
            else:
                bot_say(chat_lines, "I have no legal moves.")

            bot_thinking = False

        # EVENTS
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

            # Mouse movement
            if event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                dragger.update_mouse((mx, my))

                if mx < BOARD_SIZE:
                    hover_square = (my // SQSIZE, mx // SQSIZE)
                else:
                    hover_square = None

            # Mouse down
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if mx < BOARD_SIZE:
                    r = my // SQSIZE
                    c = mx // SQSIZE
                    piece = board[r][c]

                    if piece and piece.color == current_turn:
                        dragger.start_drag(piece, r, c, (mx, my))

            # Mouse up
            if event.type == pygame.MOUSEBUTTONUP:
                if dragger.dragging:
                    mx, my = event.pos
                    r2 = my // SQSIZE
                    c2 = mx // SQSIZE

                    move = (dragger.start_row, dragger.start_col, r2, c2)
                    legal_moves = generate_legal_moves(board, current_turn)

                    if move in legal_moves:
                        captured = make_move(board, move)

                        if captured and CAPTURE_SOUND:
                            CAPTURE_SOUND.play()
                        elif MOVE_SOUND:
                            MOVE_SOUND.play()

                        if captured:
                            if current_turn == WHITE:
                                captured_white.append(captured)
                            else:
                                captured_black.append(captured)

                        notation = move_to_notation(board, move, captured)
                        move_history.append(notation)

                        last_move = move
                        current_turn = BLACK if current_turn == WHITE else WHITE

                        if current_turn == BLACK and mode == "pvb":
                            bot_say(chat_lines, "Thinking...")

                    dragger.stop_drag()

        # DRAW EVERYTHING
        draw_board(screen, board, last_move, hover_square, dragger)
        draw_right_panel(screen, move_history, captured_white, captured_black, chat_lines, current_turn)

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
                        bot_depth = 4
                        mode = "pvb"
                        choosing_difficulty = False

        # START GAME
        else:
            run_game(mode)


if __name__ == "__main__":
    main()
