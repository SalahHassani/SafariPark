# ──────────────────────────────────────────────────────────────────────────────
# storeUI.py – UI for purchasing and selling animals and items in the store
# ──────────────────────────────────────────────────────────────────────────────

from src.utils.support import import_folder
import pygame

# ──────────────────────────────────────────────────────────────────────────────
# StoreUI: Handles the in-game store menu (buying/selling animals, items)
# ──────────────────────────────────────────────────────────────────────────────
class StoreUI:
    def __init__(self, game):
        """Initialize the StoreUI, loading assets and configuring UI layout."""
        self.game = game
        self.display_surface = pygame.display.get_surface()
        self.screen_width, self.screen_height = self.display_surface.get_width(), self.display_surface.get_height()

        # State flags
        self.menu_open = False
        self.menu_type = None
        self.confirmation_active = False
        self.animal_to_confirm = None
        
        # Chipping modal
        self.chipping_active = False
        self.unchipped_animals = []
        self.chip_buttons = []
        self.chip_cost = 50
        self.dragging_scrollbar = False
        self.scrollbar_thumb_rect = None
        self.chip_message = None
        self.chip_message_time = 0 

        # UI colors and styles
        self.colors = {
            "forest_green": (60, 100, 70),
            "leafy_green": (100, 160, 110),
            "dark_foliage": (40, 80, 50),
            "accent": (150, 210, 130),
            "text": (235, 255, 235),
            "white": (255, 255, 255),
            "item_bg": (50, 70, 55)
        }

        # Store button (bottom-right corner)
        self.rect = pygame.Rect(self.screen_width - 110, self.screen_height - 110, 100, 100)
        self.store_button_image = pygame.transform.scale(
            pygame.image.load("src/assets/ui/store_button.png").convert_alpha(),
            (100, 100)
        )

        # Fonts
        self.font = pygame.font.SysFont(None, 28)
        self.header_font = pygame.font.SysFont(None, 36)

        # Main store menu rectangle
        self.store_menu_width = 400
        self.store_menu_height = 550 
        self.menu_rect = pygame.Rect(
            (self.screen_width - self.store_menu_width) // 2,
            (self.screen_height - self.store_menu_height) // 2,
            self.store_menu_width,
            self.store_menu_height
        )

        # Arrow navigation
        arrow_height = 50
        arrow_width = 50
        self.left_arrow_button = pygame.Rect(
            self.menu_rect.x + self.store_menu_width // 4 - arrow_width // 2,
            self.menu_rect.y + self.store_menu_height - 80,
            arrow_width, arrow_height
        )
        self.right_arrow_button = pygame.Rect(
            self.menu_rect.x + self.store_menu_width * 3 // 4 - arrow_width // 2,
            self.menu_rect.y + self.store_menu_height - 80,
            arrow_width, arrow_height
        )
        self.left_arrow_image = pygame.transform.scale(
            pygame.image.load("src/assets/ui/left_arrow.png").convert_alpha(), (arrow_width, arrow_height))
        self.right_arrow_image = pygame.transform.scale(
            pygame.image.load("src/assets/ui/right_arrow.png").convert_alpha(), (arrow_width, arrow_height))

        # Tab buttons (Buy / Sell)
        self.tab_buttons = {}
        tab_width, tab_height = 100, 40
        tab_x = self.menu_rect.x + (self.store_menu_width - (tab_width * 2 + 10)) // 2
        for tab in ["Buy", "Sell"]:
            self.tab_buttons[tab] = pygame.Rect(tab_x, self.menu_rect.y + 50, tab_width, tab_height)
            tab_x += tab_width + 10
        self.selected_tab = "Buy"

        # Close button
        self.close_button = pygame.Rect(self.menu_rect.x + self.store_menu_width - 30, self.menu_rect.y + 10, 20, 20)

        # Item list and index
        self.items = []  # Will be filled by generate_animal_store_items()
        self.current_item_index = 0
        self.chip_scroll_index = 0
        self.done_chip_button = None
        self.scroll_up_button = None
        self.scroll_down_button = None

        # Item card dimensions
        self.item_width = 240
        self.item_height = 280

        # Confirmation buttons (Yes / No)
        self.confirm_buttons = {
            "yes": pygame.Rect(0, 0, 80, 40),
            "no": pygame.Rect(0, 0, 80, 40)
        }
        # Error
        self.error_message = None
        self.error_message_time = 0
        
        # Success
        self.success_message = None
        self.success_message_time = 0

    # ──────────────────────────────────────────────────────────────────────────────
    # Generates buyable animal items and their respective prices and icons
    # ──────────────────────────────────────────────────────────────────────────────
    def generate_animal_store_items(self):
        store_items = {
            "chip": 50,
            "jeep": 500,
            "pond": 100,
            "flower": 10,
            "tree": 50,
            "bush": 25
        }

        store_animals = {
            "cow": 150, "deer": 120, "goat": 130, "sheep": 100, "hen": 50,
            "cock": 60, "pig": 140, "horse": 200, "rabbit": 30, "buffalo": 170,
            "musk ox": 180, "cub": 300, "cat": 200, "puppy": 120, "wolf": 350,
            "jackals": 260, "tigers": 400, "lioness": 380, "bears": 400,
            "beavers": 220, "raccoons": 180, "bear cubs": 150, "boars": 190, "giraffe": 350
        }

        self.items = []  # Initialize here only once

        for item_name, price in store_items.items():
            icon_path = f"src/assets/ui/icons/{item_name}.png"
            self.items.append({
                "name": item_name.title(),
                "price": price,
                "image": icon_path
            })

        for species, price in store_animals.items():
            icon_path = f"src/assets/ui/icons/{species.replace(' ', '_')}.png"
            self.items.append({
                "name": species.title(),
                "price": price,
                "image": icon_path
            })
    # ──────────────────────────────────────────────────────────────────────────────
    # Renders the full store interface (Buy/Sell/Navigation)
    # ──────────────────────────────────────────────────────────────────────────────
    
    def draw(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()

        if self.menu_open:
            overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            self.display_surface.blit(overlay, (0, 0))

            menu_surface = pygame.Surface((self.store_menu_width, self.store_menu_height), pygame.SRCALPHA)
            rounded_rect_color = (*self.colors["forest_green"], 180)
            pygame.draw.rect(menu_surface, rounded_rect_color, menu_surface.get_rect(), border_radius=15)
            self.display_surface.blit(menu_surface, self.menu_rect.topleft)

            pygame.draw.rect(self.display_surface, self.colors["dark_foliage"], self.menu_rect, 2, border_radius=15)

            header_rect = pygame.Rect(self.menu_rect.x, self.menu_rect.y, self.store_menu_width, 40)
            pygame.draw.rect(self.display_surface, self.colors["dark_foliage"], header_rect, border_top_left_radius=15, border_top_right_radius=15)

            header_text = self.header_font.render("Store", True, self.colors["white"])
            self.display_surface.blit(header_text, (
                self.menu_rect.x + (self.store_menu_width - header_text.get_width()) // 2,
                self.menu_rect.y + 8
            ))

            for tab, rect in self.tab_buttons.items():
                if tab == self.selected_tab:
                    pygame.draw.rect(self.display_surface, self.colors["accent"], rect, border_radius=8)
                    tab_text = self.font.render(tab, True, self.colors["white"])
                else:
                    hover_color = self.colors["leafy_green"] if rect.collidepoint(mouse_x, mouse_y) else self.colors["leafy_green"]
                    pygame.draw.rect(self.display_surface, hover_color, rect, border_radius=8)
                    tab_text = self.font.render(tab, True, self.colors["text"])

                pygame.draw.rect(self.display_surface, self.colors["dark_foliage"], rect, 2, border_radius=8)
                self.display_surface.blit(tab_text, (
                    rect.x + (rect.width - tab_text.get_width()) // 2,
                    rect.y + (rect.height - tab_text.get_height()) // 2
                ))

            close_button_radius = 12
            close_button_center = (self.menu_rect.x + self.store_menu_width - 20, self.menu_rect.y + 20)
            pygame.draw.circle(self.display_surface, self.colors["white"], close_button_center, close_button_radius)
            pygame.draw.circle(self.display_surface, self.colors["dark_foliage"], close_button_center, close_button_radius, 2)

            line_offset = 6
            pygame.draw.line(self.display_surface, self.colors["dark_foliage"],
                            (close_button_center[0] - line_offset, close_button_center[1] - line_offset),
                            (close_button_center[0] + line_offset, close_button_center[1] + line_offset), 2)
            pygame.draw.line(self.display_surface, self.colors["dark_foliage"],
                            (close_button_center[0] - line_offset, close_button_center[1] + line_offset),
                            (close_button_center[0] + line_offset, close_button_center[1] - line_offset), 2)

            self.close_button = pygame.Rect(
                close_button_center[0] - close_button_radius,
                close_button_center[1] - close_button_radius,
                close_button_radius * 2,
                close_button_radius * 2
            )

            if self.confirmation_active:
                confirm_overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
                confirm_overlay.fill((0, 0, 0, 150))
                self.display_surface.blit(confirm_overlay, (0, 0))

                dialog_width, dialog_height = 300, 150
                dialog_rect = pygame.Rect(
                    (self.screen_width - dialog_width) // 2,
                    (self.screen_height - dialog_height) // 2,
                    dialog_width,
                    dialog_height
                )
                pygame.draw.rect(self.display_surface, self.colors["item_bg"], dialog_rect, border_radius=10)
                pygame.draw.rect(self.display_surface, self.colors["white"], dialog_rect, 2, border_radius=10)

                text = self.font.render("Are you sure?", True, self.colors["text"])
                self.display_surface.blit(text, (dialog_rect.centerx - text.get_width() // 2, dialog_rect.y + 20))

                self.confirm_buttons["yes"].center = (dialog_rect.centerx - 60, dialog_rect.bottom - 40)
                self.confirm_buttons["no"].center = (dialog_rect.centerx + 60, dialog_rect.bottom - 40)

                pygame.draw.rect(self.display_surface, self.colors["accent"], self.confirm_buttons["yes"], border_radius=5)
                pygame.draw.rect(self.display_surface, self.colors["dark_foliage"], self.confirm_buttons["no"], border_radius=5)

                yes_text = self.font.render("Yes", True, self.colors["white"])
                no_text = self.font.render("No", True, self.colors["white"])
                self.display_surface.blit(yes_text, yes_text.get_rect(center=self.confirm_buttons["yes"].center))
                self.display_surface.blit(no_text, no_text.get_rect(center=self.confirm_buttons["no"].center))
            if self.chipping_active:
                self.draw_chip_selection_window()

            elif not self.chipping_active:
                if self.selected_tab == "Buy":
                    self.draw_buy_item()
                    item_list = self.items
                else:
                    self.draw_sell_item()
                    item_list = self.game.animals

                total_items = len(item_list)
                if total_items > 0:
                    counter_text = self.font.render(f"{self.current_item_index + 1}/{total_items}", True, self.colors["white"])
                    counter_rect = counter_text.get_rect(center=(self.menu_rect.x + self.store_menu_width // 2,
                                                                self.menu_rect.y + self.store_menu_height - 50))
                    self.display_surface.blit(counter_text, counter_rect)

                    if total_items > 1:
                        self.draw_navigation_arrows()
            
        else:
            self.draw_store_button()

        if self.confirmation_active:
            self.draw_confirmation_window()
        if self.chip_message:
            time_since = pygame.time.get_ticks() - self.chip_message_time
            if time_since < 1000:
                msg_surface = self.font.render(self.chip_message, True, self.colors["white"])

                padding_x = 40
                padding_y = 20
                box_width = msg_surface.get_width() + padding_x
                box_height = msg_surface.get_height() + padding_y

                box_x = (self.screen_width - box_width) // 2
                box_y = (self.screen_height - box_height) // 2

                msg_rect = pygame.Rect(box_x, box_y, box_width, box_height)

                pygame.draw.rect(self.display_surface, self.colors["dark_foliage"], msg_rect, border_radius=12)
                pygame.draw.rect(self.display_surface, self.colors["white"], msg_rect, 2, border_radius=12)

                self.display_surface.blit(msg_surface, msg_surface.get_rect(center=msg_rect.center))
            else:
                self.chip_message = None
        # Error message box
        if self.error_message:
            time_since = pygame.time.get_ticks() - self.error_message_time
            if time_since < 1500:
                msg_surface = self.font.render(self.error_message, True, self.colors["white"])
                
                padding_x = 40
                padding_y = 20
                box_width = msg_surface.get_width() + padding_x
                box_height = msg_surface.get_height() + padding_y

                box_x = (self.screen_width - box_width) // 2
                box_y = (self.screen_height - box_height) // 2 + 70

                msg_rect = pygame.Rect(box_x, box_y, box_width, box_height)

                pygame.draw.rect(self.display_surface, (180, 60, 60), msg_rect, border_radius=12)
                pygame.draw.rect(self.display_surface, self.colors["white"], msg_rect, 2, border_radius=12)

                self.display_surface.blit(msg_surface, msg_surface.get_rect(center=msg_rect.center))
            else:
                self.error_message = None
                
        # Success message box
        if self.success_message:
            time_since = pygame.time.get_ticks() - self.success_message_time
            if time_since < 1000:
                msg_surface = self.font.render(self.success_message, True, self.colors["white"])
                
                padding_x = 40
                padding_y = 20
                box_width = msg_surface.get_width() + padding_x
                box_height = msg_surface.get_height() + padding_y

                box_x = (self.screen_width - box_width) // 2
                box_y = (self.screen_height - box_height) // 2 + 75  # Positioned below chip + error messages

                msg_rect = pygame.Rect(box_x, box_y, box_width, box_height)

                pygame.draw.rect(self.display_surface, self.colors["leafy_green"], msg_rect, border_radius=12)
                pygame.draw.rect(self.display_surface, self.colors["white"], msg_rect, 2, border_radius=12)

                self.display_surface.blit(msg_surface, msg_surface.get_rect(center=msg_rect.center))
            else:
                self.success_message = None
    
    # ──────────────────────────────────────────────────────────────────────────────
    # Renders the small button used to open the store (bottom-right corner)
    # ──────────────────────────────────────────────────────────────────────────────
    def draw_store_button(self):
        self.display_surface.blit(self.store_button_image, self.rect)
        pygame.draw.rect(self.display_surface, self.colors["dark_foliage"], self.rect, 3, border_radius=10)
    
    # ──────────────────────────────────────────────────────────────────────────────
    # Renders confirmation modal when selling an animal
    # ──────────────────────────────────────────────────────────────────────────────
    def draw_confirmation_window(self):
        width, height = 300, 150
        x = (self.screen_width - width) // 2
        y = (self.screen_height - height) // 2
        rect = pygame.Rect(x, y, width, height)

        pygame.draw.rect(self.display_surface, self.colors["item_bg"], rect, border_radius=12)
        pygame.draw.rect(self.display_surface, self.colors["dark_foliage"], rect, 2, border_radius=12)

        text = self.font.render("Sell this animal?", True, self.colors["text"])
        self.display_surface.blit(text, (x + (width - text.get_width()) // 2, y + 20))

        confirm_rect = pygame.Rect(x + 40, y + 80, 90, 35)
        cancel_rect = pygame.Rect(x + 170, y + 80, 90, 35)

        pygame.draw.rect(self.display_surface, self.colors["accent"], confirm_rect, border_radius=10)
        pygame.draw.rect(self.display_surface, self.colors["dark_foliage"], cancel_rect, border_radius=10)

        confirm_text = self.font.render("Confirm", True, self.colors["white"])
        cancel_text = self.font.render("Cancel", True, self.colors["white"])

        self.display_surface.blit(confirm_text, (confirm_rect.centerx - confirm_text.get_width() // 2, confirm_rect.y + 6))
        self.display_surface.blit(cancel_text, (cancel_rect.centerx - cancel_text.get_width() // 2, cancel_rect.y + 6))

        self.confirm_rect = confirm_rect
        self.cancel_rect = cancel_rect
    
    # ──────────────────────────────────────────────────────────────────────────────
    # Renders currently selected item in Buy tab
    # ──────────────────────────────────────────────────────────────────────────────
    def draw_buy_item(self):
        if not self.items:
            empty_text = self.font.render("No items available", True, self.colors["text"])
            self.display_surface.blit(empty_text, (
                self.menu_rect.x + (self.store_menu_width - empty_text.get_width()) // 2,
                self.menu_rect.y + 150
            ))
            return

        if self.current_item_index >= len(self.items):
            self.current_item_index = 0

        item = self.items[self.current_item_index]

        x = self.menu_rect.x + (self.store_menu_width - self.item_width) // 2
        y = self.menu_rect.y + 100
        self.draw_item(item, x, y, is_buy=True)

    # ──────────────────────────────────────────────────────────────────────────────
    # Renders currently selected animal in Sell tab
    # ──────────────────────────────────────────────────────────────────────────────
    def draw_sell_item(self):
        if not self.game.animals:
            empty_text = self.font.render("No animals to sell", True, self.colors["text"])
            self.display_surface.blit(empty_text, (
                self.menu_rect.x + (self.store_menu_width - empty_text.get_width()) // 2,
                self.menu_rect.y + 150
            ))
            return

        if self.current_item_index >= len(self.game.animals):
            self.current_item_index = 0

        animal = self.game.animals[self.current_item_index]

        x = self.menu_rect.x + (self.store_menu_width - self.item_width) // 2
        y = self.menu_rect.y + 100
        self.draw_item(animal, x, y, is_buy=False)

    # ──────────────────────────────────────────────────────────────────────────────
    # Draws the item card with icon, price, name, and action button
    # ──────────────────────────────────────────────────────────────────────────────
    def draw_item(self, item, x, y, is_buy):
        rect = pygame.Rect(x, y, self.item_width, self.item_height)

        shadow_rect = rect.copy()
        shadow_rect.x += 4
        shadow_rect.y += 4
        pygame.draw.rect(self.display_surface, (30, 30, 30, 100), shadow_rect, border_radius=10)
        pygame.draw.rect(self.display_surface, self.colors["item_bg"], rect, border_radius=10)
        pygame.draw.rect(self.display_surface, self.colors["dark_foliage"], rect, 2, border_radius=10)

        # Item image
        image_size = self.item_width - 60
        image_rect = pygame.Rect(x + (self.item_width - image_size) // 2, y + 10, image_size, image_size)

        if is_buy:
            try:
                image = pygame.image.load(item["image"]).convert_alpha()
                image = pygame.transform.scale(image, (image_size, image_size))
                self.display_surface.blit(image, image_rect)
            except:
                pass
            name = item["name"]
            price = item["price"]
        else:
            try:
                species_key = item.species.split("/")[0].lower()
                image_path = f"src/assets/ui/icons/{species_key}.png"
                image = pygame.image.load(image_path).convert_alpha()
                image = pygame.transform.scale(image, (image_size, image_size))
                self.display_surface.blit(image, image_rect)
            except Exception as e:
                print(f"Failed to load image for {item.species}: {e}")
                try:
                    fallback = pygame.image.load("src/assets/ui/icons/animal_placeholder.png").convert_alpha()
                    fallback = pygame.transform.scale(fallback, (image_size, image_size))
                    self.display_surface.blit(fallback, image_rect)
                except:
                    pass
            name = item.name
            price = item.price

        text_y = y + image_size + 20

        if is_buy:
            species_text = self.font.render(f"Species: {name}", True, self.colors["text"])
            self.display_surface.blit(species_text, (x + 10, text_y))
            text_y += 20
            
        elif hasattr(item, 'species'):
            species_text = self.font.render(f"Species: {item.species.split('/')[0]}", True, self.colors["text"])
            self.display_surface.blit(species_text, (x + 10, text_y))
            text_y += 20
            
            name_text = self.font.render(f"Name: {name}", True, self.colors["text"])
            self.display_surface.blit(name_text, (x + 10, text_y))
            text_y += 20
            
            if hasattr(item, 'age'):
                age_text = self.font.render(f"Age: {item.age}", True, self.colors["text"])
                self.display_surface.blit(age_text, (x + 10, text_y))
                text_y += 20

        if is_buy:
            text_y += 70
        else:
            text_y += 30

        # Draw price tag
        price_tag_rect = pygame.Rect(x + 10, text_y, self.item_width - 20, 35)
        pygame.draw.rect(self.display_surface, self.colors["dark_foliage"], price_tag_rect, border_radius=15)

        price_text = self.font.render(f"${price}", True, self.colors["white"])
        self.display_surface.blit(price_text, (
            price_tag_rect.x + (price_tag_rect.width - price_text.get_width()) // 2,
            price_tag_rect.y + (price_tag_rect.height - price_text.get_height()) // 2
        ))

        button_rect = pygame.Rect(x + 10, price_tag_rect.bottom + 10, self.item_width - 20, 30)

        # --- Draw Buy or Sell button ---
        button_rect = pygame.Rect(x + 10, price_tag_rect.bottom + 10, self.item_width - 20, 30)
        button_text = "BUY" if is_buy else "SELL"

        pygame.draw.rect(self.display_surface, self.colors["accent"], button_rect, border_radius=10)
        button_label = self.font.render(button_text, True, self.colors["white"])
        self.display_surface.blit(button_label, (
            button_rect.x + (button_rect.width - button_label.get_width()) // 2,
            button_rect.y + (button_rect.height - button_label.get_height()) // 2
        ))

        # --- Handle click ---
        if button_rect.collidepoint(pygame.mouse.get_pos()):
            if pygame.mouse.get_pressed()[0]:
                if not hasattr(self, 'click_cooldown') or pygame.time.get_ticks() - self.click_cooldown > 300:
                    if is_buy:
                        self.buy_item(item)
                    else:
                        self.confirmation_active = True
                        self.animal_to_confirm = item
                    self.click_cooldown = pygame.time.get_ticks()

     # ──────────────────────────────────────────────────────────────────────────────
    # Renders the left/right arrows to navigate item pages
    # ──────────────────────────────────────────────────────────────────────────────
    def draw_navigation_arrows(self):
        for button, image in [(self.left_arrow_button, self.left_arrow_image), 
                             (self.right_arrow_button, self.right_arrow_image)]:
            pygame.draw.circle(self.display_surface, self.colors["leafy_green"], 
                              (button.x + button.width // 2, button.y + button.height // 2), 25)
            pygame.draw.circle(self.display_surface, self.colors["dark_foliage"], 
                              (button.x + button.width // 2, button.y + button.height // 2), 25, 2)
            
            self.display_surface.blit(image, button)
            
    # ──────────────────────────────────────────────────────────────────────────────
    # Handles item purchases based on type
    # ──────────────────────────────────────────────────────────────────────────────        
    def buy_item(self, item):
        item_name = item["name"].lower()
        success = False

        if item_name in ["deer", "cow", "goat", "sheep", "hen", "cock", "pig", "horse", "rabbit", "buffalo", "musk ox",
                        "cub", "cat", "puppy", "wolf", "jackals", "tigers", "lioness", "bears", "beavers", "raccoons",
                        "bear cubs", "boars", "giraffe"]:
            success = self.game.buy_item("animal", animal_type=item_name, item_price=item["price"])

        elif item_name == "chip":
            unchipped = [a for a in self.game.animals if a not in self.game.chipped_animals]

            if not unchipped:
                self.chip_message = "All animals are already chipped!"
                self.chip_message_time = pygame.time.get_ticks()
            else:
                self.chipping_active = True
                self.unchipped_animals = unchipped
                self.chip_scroll_index = 0
            return

        elif item_name == "jeep":
            success = self.game.buy_item("jeep", item_price=item["price"])
        elif item_name in ["pond", "flower", "tree", "bush"]:
            success = self.game.buy_item(item_name, item_price=item["price"])
            
        if success:
            self.success_message = f"Bought {item_name.title()}!"
            self.success_message_time = pygame.time.get_ticks()
        elif success is None:
            self.success_message = f"Placing {item_name.title()}..."
            self.success_message_time = pygame.time.get_ticks()
        else:
            self.error_message = f"Not enough capital for {item_name.title()}!"
            self.error_message_time = pygame.time.get_ticks()

    # ──────────────────────────────────────────────────────────────────────────────
    # Removes an animal from the park and adds its price to capital
    # ──────────────────────────────────────────────────────────────────────────────
    def sell_animal(self, index):
        if 0 <= index < len(self.game.animals):
            animal = self.game.animals[index]
            self.game.capital += animal.price
            
            if animal in self.game.herbivores:
                self.game.herbivores.remove(animal)
            elif animal in self.game.carnivores:
                self.game.carnivores.remove(animal)
            elif animal in self.game.omnivores:
                self.game.omnivores.remove(animal)
                
            self.game.animals.remove(animal)
            animal.kill()
            
            if index >= len(self.game.animals):
                self.current_item_index = max(0, len(self.game.animals) - 1)
            else:
                self.current_item_index = index
            
            return True
        return False
    def draw_chip_selection_window(self):
        width, height = 500, 450
        x = (self.screen_width - width) // 2
        y = (self.screen_height - height) // 2
        window_rect = pygame.Rect(x, y, width, height)

        pygame.draw.rect(self.display_surface, self.colors["item_bg"], window_rect, border_radius=12)
        pygame.draw.rect(self.display_surface, self.colors["white"], window_rect, 2, border_radius=12)

        title = self.header_font.render("Which animal would you like to chip?", True, self.colors["white"])
        self.display_surface.blit(title, (x + 20, y + 20))

        spacing = 45
        visible_animals = self.unchipped_animals[self.chip_scroll_index:self.chip_scroll_index + 6]
        start_y = y + 115

        # Scrollbar dimensions
        bar_x = x + width - 20 
        bar_y = y + 70
        bar_width = 6
        bar_height = height - 130 

        # Draw scrollbar background track
        pygame.draw.rect(self.display_surface, self.colors["dark_foliage"], (bar_x, bar_y, bar_width, bar_height), border_radius=3)

        # If total items > visible, draw the scroll thumb
        total_animals = len(self.unchipped_animals)
        visible_count = 6

        if total_animals > visible_count:
            scroll_ratio = visible_count / total_animals
            thumb_height = max(30, bar_height * scroll_ratio)

            max_scroll = total_animals - visible_count
            scroll_position_ratio = self.chip_scroll_index / max_scroll if max_scroll > 0 else 0

            thumb_y = bar_y + int((bar_height - thumb_height) * scroll_position_ratio)
            self.scrollbar_thumb_rect = pygame.Rect(bar_x, thumb_y, bar_width, thumb_height)

            pygame.draw.rect(self.display_surface, self.colors["accent"], self.scrollbar_thumb_rect, border_radius=3)
        else:
            self.scrollbar_thumb_rect = None

        self.chip_buttons = []

        visible_animals = self.unchipped_animals[self.chip_scroll_index:self.chip_scroll_index + 6]
        
        # Scroll Up
        if self.chip_scroll_index > 0:
            up_rect = pygame.Rect(x + 200, y + 60, 30, 30)
            pygame.draw.polygon(self.display_surface, self.colors["white"], [
                (up_rect.centerx, up_rect.y),
                (up_rect.x, up_rect.bottom),
                (up_rect.right, up_rect.bottom)
            ])
            self.scroll_up_button = up_rect
        else:
            self.scroll_up_button = None

        # Scroll Down
        if self.chip_scroll_index + 6 < len(self.unchipped_animals):
            down_rect = pygame.Rect(x + 200, y + height - 60, 30, 30)
            pygame.draw.polygon(self.display_surface, self.colors["white"], [
                (down_rect.centerx, down_rect.bottom),
                (down_rect.x, down_rect.y),
                (down_rect.right, down_rect.y)
            ])
            self.scroll_down_button = down_rect
        else:
            self.scroll_down_button = None


        for i, animal in enumerate(visible_animals):
            text = self.font.render(f"{animal.name} ({animal.species})", True, self.colors["white"])
            self.display_surface.blit(text, (x + 30, start_y + i * spacing))

            button_rect = pygame.Rect(x + 320, start_y + i * spacing, 120, 30)
            pygame.draw.rect(self.display_surface, self.colors["accent"], button_rect, border_radius=8)
            pygame.draw.rect(self.display_surface, self.colors["white"], button_rect, 2, border_radius=8)

            label = self.font.render("Chip", True, self.colors["white"])
            self.display_surface.blit(label, label.get_rect(center=button_rect.center))

            self.chip_buttons.append((button_rect, animal))
            
        done_rect = pygame.Rect(x + width - 130, y + height - 50, 100, 30)
        pygame.draw.rect(self.display_surface, self.colors["accent"], done_rect, border_radius=8)
        done_text = self.font.render("Done", True, self.colors["white"])
        self.display_surface.blit(done_text, done_text.get_rect(center=done_rect.center))
        self.done_chip_button = done_rect


    # ──────────────────────────────────────────────────────────────────────────────
    # Handles mouse input and navigation within the store
    # ──────────────────────────────────────────────────────────────────────────────
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            if self.chipping_active and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for button, animal in self.chip_buttons:
                    if button.collidepoint(event.pos):
                        self.game.chipped_animals.add(animal)
                        self.game.capital -= self.chip_cost
                        self.chip_message = f"{animal.name} the {animal.species.split('/')[0]} has been chipped!"
                        self.chip_message_time = pygame.time.get_ticks()

                        self.unchipped_animals.remove(animal)

                        if self.chip_scroll_index >= len(self.unchipped_animals):
                            self.chip_scroll_index = max(0, len(self.unchipped_animals) - 6)

                        # Only close window if no animals are left to chip
                        if not self.unchipped_animals:
                            self.chipping_active = False
                            self.done_chip_button = None

            if self.done_chip_button and self.done_chip_button.collidepoint(mouse_pos):
                self.chipping_active = False
                self.unchipped_animals.clear()
                self.chip_scroll_index = 0
                return True

            if self.scroll_up_button and self.scroll_up_button.collidepoint(mouse_pos):
                self.chip_scroll_index = max(0, self.chip_scroll_index - 1)
                return True

            if self.scroll_down_button and self.scroll_down_button.collidepoint(mouse_pos):
                if self.chip_scroll_index + 6 < len(self.unchipped_animals):
                    self.chip_scroll_index += 1
                return True
            if self.scrollbar_thumb_rect and self.scrollbar_thumb_rect.collidepoint(event.pos):
                self.dragging_scrollbar = True

            if self.confirmation_active:
                if hasattr(self, 'confirm_rect') and self.confirm_rect.collidepoint(mouse_pos):
                    if self.animal_to_confirm in self.game.animals:
                        self.game.capital += self.animal_to_confirm.price
                        
                        if self.animal_to_confirm in self.game.herbivores:
                            self.game.herbivores.remove(self.animal_to_confirm)
                        elif self.animal_to_confirm in self.game.carnivores:
                            self.game.carnivores.remove(self.animal_to_confirm)
                        elif self.animal_to_confirm in self.game.omnivores:
                            self.game.omnivores.remove(self.animal_to_confirm)
                        
                        self.game.animals.remove(self.animal_to_confirm)
                        self.animal_to_confirm.kill()
                        
                        if self.current_item_index >= len(self.game.animals):
                            self.current_item_index = max(0, len(self.game.animals) - 1)
                    
                    self.confirmation_active = False
                    self.animal_to_confirm = None
                    return True
                    
                elif hasattr(self, 'cancel_rect') and self.cancel_rect.collidepoint(mouse_pos):
                    self.confirmation_active = False
                    self.animal_to_confirm = None
                    return True

            if self.rect.collidepoint(event.pos) and not self.menu_open:
                self.menu_open = True

            elif self.close_button.collidepoint(event.pos):
                self.menu_open = False

            elif self.tab_buttons["Buy"].collidepoint(event.pos):
                self.selected_tab = "Buy"
            elif self.tab_buttons["Sell"].collidepoint(event.pos):
                self.selected_tab = "Sell"

            if self.left_arrow_button.collidepoint(event.pos):
                self.current_item_index = (self.current_item_index - 1) % len(
                    self.items if self.selected_tab == "Buy" else self.game.animals
                )
            elif self.right_arrow_button.collidepoint(event.pos):
                self.current_item_index = (self.current_item_index + 1) % len(
                    self.items if self.selected_tab == "Buy" else self.game.animals
                )
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging_scrollbar = False
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging_scrollbar = False
        if event.type == pygame.MOUSEMOTION and self.dragging_scrollbar:
            bar_y = self.menu_rect.y + (self.store_menu_height - 400) // 2 + 70
            bar_height = 400 - 130
            total_animals = len(self.unchipped_animals)
            visible_count = 6
            max_scroll = total_animals - visible_count

            if max_scroll > 0:
                rel_y = event.pos[1] - bar_y
                rel_y = max(0, min(rel_y, bar_height))
                scroll_ratio = rel_y / (bar_height)
                self.chip_scroll_index = int(scroll_ratio * max_scroll)