#!/usr/bin/env python3
"""
Battle City - Main Menu
Level selection and game entry point
"""

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    pygame = None
    PYGAME_AVAILABLE = False

import sys
import os
sys.path.insert(0, 'src')

from config import GRID_WIDTH, GRID_HEIGHT, TILE_SIZE

class MainMenu:
    """Main menu for level selection."""
    
    def __init__(self):
        """Initialize menu."""
        if not PYGAME_AVAILABLE:
            print("ERROR: pygame not available")
            sys.exit(1)
        
        pygame.init()
        self.WIDTH = GRID_WIDTH * TILE_SIZE
        self.HEIGHT = GRID_HEIGHT * TILE_SIZE
        print(f"DEBUG: Pygame initialized. Screen size: {self.WIDTH}x{self.HEIGHT}")
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        print("DEBUG: Window created successfully.")
        pygame.display.set_caption("Battle City - Level Select")
        self.clock = pygame.time.Clock()
        self.selected = 0
        self.levels = [
            {'name': 'Level 1: Brick Maze', 'value': 1, 'desc': 'Intro: BFS pathfinding, dynamic map changes', 'icon': 'tank_basic'},
            {'name': 'Level 2: Steel Fortress', 'value': 2, 'desc': 'Challenge: A* with cost-awareness', 'icon': 'tank_armor'},
            {'name': 'Level 3: BOSS Battle', 'value': 'BOSS', 'desc': 'Advanced: Minimax adversarial search', 'icon': 'tank_boss'}
        ]
        self._load_menu_assets()

    def _load_menu_assets(self):
        """Load sprites for menu icons."""
        self.icons = {}
        asset_dir = os.path.join(os.path.dirname(__file__), 'assets')
        if not os.path.exists(asset_dir):
            return
            
        for level in self.levels:
            icon_name = level['icon']
            path = os.path.join(asset_dir, f"{icon_name}.png")
            if os.path.exists(path):
                surf = pygame.image.load(path).convert_alpha()
                self.icons[icon_name] = pygame.transform.scale(surf, (60, 60))
    
    def handle_input(self):
        """Handle menu input."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected = (self.selected - 1) % len(self.levels)
                elif event.key == pygame.K_DOWN:
                    self.selected = (self.selected + 1) % len(self.levels)
                elif event.key == pygame.K_RETURN:
                    return self.levels[self.selected]['value']
                elif event.key == pygame.K_ESCAPE:
                    return None
        return False
    
    def render(self):
        """Render menu with modern styling."""
        # Modern gradient-inspired background
        self.screen.fill((10, 15, 25))
        
        # Draw subtle background pattern
        for y in range(0, self.HEIGHT, 40):
            pygame.draw.line(self.screen, (25, 35, 50), (0, y), (self.WIDTH, y), 1)
        
        # Title with modern styling
        title_font = pygame.font.Font(None, 80)
        title = title_font.render("BATTLE CITY", True, (100, 200, 255))
        title_rect = title.get_rect(center=(self.WIDTH // 2, 60))
        # Add subtle shadow effect
        shadow = title_font.render("BATTLE CITY", True, (0, 0, 0))
        self.screen.blit(shadow, (title_rect.x + 3, title_rect.y + 3))
        self.screen.blit(title, title_rect)
        
        # Subtitle
        subtitle_font = pygame.font.Font(None, 28)
        subtitle = subtitle_font.render("SELECT LEVEL", True, (150, 180, 220))
        subtitle_rect = subtitle.get_rect(center=(self.WIDTH // 2, 130))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Decorative line
        pygame.draw.line(self.screen, (100, 200, 255), (self.WIDTH // 2 - 100, 150), (self.WIDTH // 2 + 100, 150), 2)
        
        # Level options
        option_font = pygame.font.Font(None, 28)
        desc_font = pygame.font.Font(None, 18)
        
        y_offset = 210
        for i, level in enumerate(self.levels):
            is_selected = i == self.selected
            
            # Modern card-style background
            card_height = 80
            card_y = y_offset - 10
            card_color = (40, 60, 90) if is_selected else (25, 40, 65)
            pygame.draw.rect(self.screen, card_color, (40, card_y, self.WIDTH - 80, card_height))
            
            # Selected card border
            if is_selected:
                pygame.draw.rect(self.screen, (100, 200, 255), (40, card_y, self.WIDTH - 80, card_height), 3)
            
            # Text color
            color = (255, 255, 255) if is_selected else (180, 200, 220)
            
            # Level icon
            icon = self.icons.get(level['icon'])
            if icon:
                self.screen.blit(icon, (60, card_y + 10))
            
            # Level name
            text = option_font.render(str(level['name']), True, color)
            self.screen.blit(text, (140, card_y + 8))
            
            # Description
            desc_color = (200, 220, 240) if is_selected else (130, 150, 180)
            desc_text = desc_font.render(str(level['desc']), True, desc_color)
            self.screen.blit(desc_text, (140, card_y + 40))
            
            y_offset += 90
        
        # Bottom instructions with modern styling
        inst_font = pygame.font.Font(None, 18)
        inst_box_y = self.HEIGHT - 55
        pygame.draw.rect(self.screen, (20, 30, 50), (0, inst_box_y, self.WIDTH, 55))
        pygame.draw.line(self.screen, (100, 200, 255), (0, inst_box_y), (self.WIDTH, inst_box_y), 1)
        
        inst1 = inst_font.render("↑ ↓  Select  |  ENTER  Play  |  ESC  Quit", True, (150, 200, 255))
        inst_rect = inst1.get_rect(center=(self.WIDTH // 2, inst_box_y + 27))
        self.screen.blit(inst1, inst_rect)
        
        pygame.display.flip()
    
    def run(self):
        """Run menu loop."""
        while True:
            result = self.handle_input()
            
            if result is None:
                return None  # User quit
            elif result is not False:
                return result  # User selected a level
            
            self.render()
            self.clock.tick(60)


def main():
    """Main entry point."""
    if not PYGAME_AVAILABLE:
        print("ERROR: pygame not installed")
        sys.exit(1)
    
    pygame.init()
    
    try:
        print("DEBUG: Starting main loop...")
        while True:
            menu = MainMenu()
            print("DEBUG: Running menu...")
            level = menu.run()
            
            if level is None:
                print("DEBUG: Menu returned None (Quit). Exiting...")
                break
            
            # Import game after menu selection
            from main import BattleCityGame
            
            print(f"\nDEBUG: Starting Level {level}...")
            game = BattleCityGame(level)
            game.run()
            
            # After game ends, show menu again
            print("\nDEBUG: Returning to menu...\n")
    
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to close...")
    finally:
        pygame.quit()
        sys.exit(0)


if __name__ == '__main__':
    main()
