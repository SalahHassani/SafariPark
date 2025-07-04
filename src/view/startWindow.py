# ──────────────────────────────────────────────────────────────────────────────
# selectDifficulty.py – Displays intro and difficulty selection for Safari Park
# ──────────────────────────────────────────────────────────────────────────────
# This module initializes a full-screen Pygame window and presents the player
# with an introductory tutorial sequence, followed by difficulty selection.
# It features animated hover effects and ensures a difficulty is selected
# before starting the game.
# ──────────────────────────────────────────────────────────────────────────────

import pygame

def select_difficulty(screen, skip_intro=False):
    # ──────────────────────────────────────────────────────────────────────────
    # Initialization
    # ──────────────────────────────────────────────────────────────────────────
    pygame.init()

    info = pygame.display.Info()
    SCREEN_WIDTH = int(info.current_w)
    SCREEN_HEIGHT = int(info.current_h)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Safari Park")

    # Load and scale the background image to full screen
    image_path = "src/assets/images/background-image/background.jpg"
    background = pygame.image.load(image_path)
    scaled_bg = pygame.transform.smoothscale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))

    # Colors and fonts
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    TRANSPARENT_GRAY = (200, 200, 200, 180)
    TEXT_HOVER_COLOR = (0, 0, 255)

    pygame.font.init()
    title_font = pygame.font.Font(None, 50)
    menu_font = pygame.font.Font(None, 25)
    proceed_font = pygame.font.Font(None, 20)

    # ──────────────────────────────────────────────────────────────────────────
    # UI Setup
    # ──────────────────────────────────────────────────────────────────────────
    difficulty_options = ["Easy", "Medium", "Hard"]
    selected_difficulty = None

    # Setup difficulty box dimensions and positioning
    line_height = 20
    total_lines = 1 + len(difficulty_options) + 1
    box_height = total_lines * line_height + (SCREEN_HEIGHT / 14) + 20
    box_width = int(SCREEN_WIDTH * 0.6)
    box_x = (SCREEN_WIDTH - box_width) // 2
    box_y = int(SCREEN_HEIGHT * 0.65)

    difficulty_box = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
    difficulty_box.fill(TRANSPARENT_GRAY)

    # Introductory tutorial text
    intro_messages = [
        "Welcome to Safari Park Game!",
        "In this game, you must protect the wildlife.",
        "Rangers will guard the animals while poachers try to hunt them.",
        "You win by keeping the number of animals and capital above the threshold."
    ]
    message_index = 0
    show_intro = not skip_intro

    # ──────────────────────────────────────────────────────────────────────────
    # Utility Function – Text Wrapping
    # ──────────────────────────────────────────────────────────────────────────
    def wrap_text(text, font, max_width):
        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if font.size(test_line)[0] < max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        return lines

    # ──────────────────────────────────────────────────────────────────────────
    # Main Loop – Handles rendering and interaction
    # ──────────────────────────────────────────────────────────────────────────
    running = True
    while running:
        screen.blit(scaled_bg, (0, 0))

        # Render title
        title_text = title_font.render("Safari Park Game", True, BLACK)
        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 90))

        if show_intro:
            # Draw transparent box and intro text
            screen.blit(difficulty_box, (box_x, box_y))
            wrapped_lines = wrap_text(intro_messages[message_index], menu_font, box_width - 40)
            start_y = box_y + (box_height - (len(wrapped_lines) * 30 + 40)) // 2

            for i, line in enumerate(wrapped_lines):
                message_text = menu_font.render(line, True, BLACK)
                screen.blit(message_text, (SCREEN_WIDTH // 2 - message_text.get_width() // 2, start_y + i * 30))

            # Instruction to proceed
            proceed_text = proceed_font.render("Click anywhere to proceed", True, BLACK)
            screen.blit(proceed_text, (SCREEN_WIDTH // 2 - proceed_text.get_width() // 2, box_y + box_height - 30))

        else:
            # Draw difficulty selection menu
            screen.blit(difficulty_box, (box_x, box_y))
            select_text = menu_font.render("Select a difficulty level:", True, BLACK)
            screen.blit(select_text, (SCREEN_WIDTH // 2 - select_text.get_width() // 2, box_y + 10))

            mouse_pos = pygame.mouse.get_pos()

            # Render difficulty levels with hover effect
            for i, level in enumerate(difficulty_options):
                color = TEXT_HOVER_COLOR if selected_difficulty == level else BLACK
                text_x = SCREEN_WIDTH // 2 - menu_font.size(level)[0] // 2
                text_y = box_y + 40 + i * 25

                if text_x <= mouse_pos[0] <= text_x + menu_font.size(level)[0] and text_y <= mouse_pos[1] <= text_y + menu_font.size(level)[1]:
                    color = TEXT_HOVER_COLOR

                diff_text = menu_font.render(level, True, color)
                screen.blit(diff_text, (text_x, text_y))

            # Start game option
            start_text = menu_font.render("Start the game", True, BLACK)
            start_x = SCREEN_WIDTH // 2 - start_text.get_width() // 2
            start_y = box_y + 40 + len(difficulty_options) * 30
            start_rect = pygame.Rect(start_x, start_y, start_text.get_width(), start_text.get_height())

            if start_rect.collidepoint(mouse_pos):
                start_text = menu_font.render("Start the game", True, TEXT_HOVER_COLOR)

            screen.blit(start_text, (start_x, start_y))

        # ──────────────────────────────────────────────────────────────────────
        # Event Handling
        # ──────────────────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                return None

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if show_intro:
                    message_index += 1
                    if message_index >= len(intro_messages):
                        show_intro = False
                else:
                    # Difficulty selection
                    for i, level in enumerate(difficulty_options):
                        text_x = SCREEN_WIDTH // 2 - menu_font.size(level)[0] // 2
                        text_y = box_y + 40 + i * 25
                        if text_x <= event.pos[0] <= text_x + menu_font.size(level)[0] and text_y <= event.pos[1] <= text_y + menu_font.size(level)[1]:
                            selected_difficulty = level

                    # Start game
                    if start_rect.collidepoint(event.pos):
                        if selected_difficulty:
                            print(f"Starting game on {selected_difficulty} mode!")
                            running = False
                        else:
                            print("Please select a difficulty level before starting.")

        pygame.display.update()

    return selected_difficulty
    