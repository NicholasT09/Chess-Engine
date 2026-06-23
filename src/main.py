import pygame
import sys
import random

from const import *
from chess_game import Game
from square import Square
from move import Move

class Main:

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('Chess')

        self.game = Game()
        self.state = "menu"

        # UI fonts
        self.title_font = pygame.font.SysFont("arial", 72, bold=True)
        self.button_font = pygame.font.SysFont("arial", 40)

        # Play button
        self.play_button = pygame.Rect(WIDTH//2 - 120, HEIGHT//2, 240, 70)

        # -------------------------
        # LOAD MENU BACKGROUND
        # -------------------------
        self.menu_bg = pygame.image.load("menu_background.jpg")
        self.menu_bg = pygame.transform.scale(self.menu_bg, (WIDTH, HEIGHT))

        # Semi-transparent overlay
        self.overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 120))

        # -------------------------
        # BOT VOICELINES
        # -------------------------
        self.bot_lines = [
            "Your move was… interesting.",
            "I’ve seen better moves from a pawn.",
            "Are you sure about that.",
            "Bold strategy. Let’s see if it pays off.",
            "I expected that… unfortunately.",
            "You’re playing right into my plan.",
            "I won’t go easy on you.",
            "You can resign at any time.",
            "I admire your confidence.",
            "I’ll give you that one."
        ]

        self.current_bot_line = ""
        self.bot_line_timer = 0

    # -------------------------
    # DRAW BOT VOICELINE
    # -------------------------
    def draw_bot_line(self):
        if self.current_bot_line and pygame.time.get_ticks() < self.bot_line_timer:
            font = pygame.font.SysFont("arial", 28)

            # Background box
            box = pygame.Surface((WIDTH, 60))
            box.set_alpha(160)
            box.fill((0, 0, 0))
            self.screen.blit(box, (0, HEIGHT - 60))

            # Text
            text_surf = font.render(self.current_bot_line, True, (255, 255, 255))
            self.screen.blit(text_surf, (20, HEIGHT - 45))

    # -------------------------
    # BOT MOVE (BLACK)
    # -------------------------
    def bot_move(self):
        board = self.game.board
        bot_color = "black"
        legal_moves = []

        for row in range(8):
            for col in range(8):
                square = board.squares[row][col]
                if square.has_piece():
                    piece = square.piece
                    if piece.color == bot_color:
                        board.calc_moves(piece, row, col, bool=True)
                        for move in piece.moves:
                            if board.valid_move(piece, move):
                                legal_moves.append((piece, move))

        if not legal_moves:
            return

        piece, move = random.choice(legal_moves)

        captured = board.squares[move.final.row][move.final.col].has_piece()
        board.move(piece, move)
        board.set_true_en_passant(piece)

        self.game.play_sound(captured)
        self.game.show_bg(self.screen)
        self.game.show_last_move(self.screen)
        self.game.show_pieces(self.screen)

        self.game.next_turn()

        # -------------------------
        # BOT SAYS A VOICELINE
        # -------------------------
        self.current_bot_line = random.choice(self.bot_lines)
        self.bot_line_timer = pygame.time.get_ticks() + 3000  # show for 3 seconds

    # -------------------------
    # MENU UI
    # -------------------------
    def draw_menu(self):
        self.screen.blit(self.menu_bg, (0, 0))
        self.screen.blit(self.overlay, (0, 0))

        title_surf = self.title_font.render("CHESS", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(WIDTH//2, HEIGHT//2 - 120))
        self.screen.blit(title_surf, title_rect)

        pygame.draw.rect(self.screen, (200, 200, 200), self.play_button, border_radius=10)
        play_text = self.button_font.render("PLAY", True, (0, 0, 0))
        play_rect = play_text.get_rect(center=self.play_button.center)
        self.screen.blit(play_text, play_rect)

    # -------------------------
    # MAIN LOOP
    # -------------------------
    def mainloop(self):

        screen = self.screen
        game = self.game
        board = self.game.board
        dragger = self.game.dragger

        while True:

            # -------------------------
            # MENU
            # -------------------------
            if self.state == "menu":
                self.draw_menu()

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()

                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.play_button.collidepoint(event.pos):
                            self.state = "game"

                pygame.display.update()
                continue

            # -------------------------
            # GAME
            # -------------------------
            game.show_bg(screen)
            game.show_last_move(screen)
            game.show_moves(screen)
            game.show_pieces(screen)
            game.show_hover(screen)

            # Draw bot voiceline
            self.draw_bot_line()

            if dragger.dragging:
                dragger.update_blit(screen)

            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    dragger.update_mouse(event.pos)

                    clicked_row = dragger.mouseY // SQSIZE
                    clicked_col = dragger.mouseX // SQSIZE

                    if board.squares[clicked_row][clicked_col].has_piece():
                        piece = board.squares[clicked_row][clicked_col].piece

                        if piece.color == game.next_player:
                            board.calc_moves(piece, clicked_row, clicked_col, bool=True)
                            dragger.save_initial(event.pos)
                            dragger.drag_piece(piece)

                            game.show_bg(screen)
                            game.show_last_move(screen)
                            game.show_moves(screen)
                            game.show_pieces(screen)

                elif event.type == pygame.MOUSEMOTION:
                    motion_row = event.pos[1] // SQSIZE
                    motion_col = event.pos[0] // SQSIZE

                    game.set_hover(motion_row, motion_col)

                    if dragger.dragging:
                        dragger.update_mouse(event.pos)
                        game.show_bg(screen)
                        game.show_last_move(screen)
                        game.show_moves(screen)
                        game.show_pieces(screen)
                        game.show_hover(screen)
                        dragger.update_blit(screen)

                elif event.type == pygame.MOUSEBUTTONUP:

                    if dragger.dragging:
                        dragger.update_mouse(event.pos)

                        released_row = dragger.mouseY // SQSIZE
                        released_col = dragger.mouseX // SQSIZE

                        initial = Square(dragger.initial_row, dragger.initial_col)
                        final = Square(released_row, released_col)
                        move = Move(initial, final)

                        if board.valid_move(dragger.piece, move):
                            captured = board.squares[released_row][released_col].has_piece()
                            board.move(dragger.piece, move)
                            board.set_true_en_passant(dragger.piece)

                            game.play_sound(captured)
                            game.show_bg(screen)
                            game.show_last_move(screen)
                            game.show_pieces(screen)

                            game.next_turn()

                            if game.next_player == "black":
                                self.bot_move()

                    dragger.undrag_piece()

                elif event.type == pygame.KEYDOWN:

                    if event.key == pygame.K_t:
                        game.change_theme()

                    if event.key == pygame.K_r:
                        game.reset()
                        game = self.game
                        board = self.game.board
                        dragger = self.game.dragger

            pygame.display.update()


main = Main()
main.mainloop()
