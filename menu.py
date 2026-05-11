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
        """Render menu."""
        self.screen.fill((20, 20, 30))
        
        # Title
        title_font = pygame.font.Font(None, 72)
        title = title_font.render("BATTLE CITY", True, (255, 200, 50))
        self.screen.blit(title, (self.WIDTH // 2 - 250, 50))
        
        subtitle_font = pygame.font.Font(None, 36)
        subtitle = subtitle_font.render("Level Select", True, (150, 150, 200))
        self.screen.blit(subtitle, (self.WIDTH // 2 - 140, 140))
        
        # Level options
        option_font = pygame.font.Font(None, 32)
        desc_font = pygame.font.Font(None, 20)
        
        y_offset = 250
        for i, level in enumerate(self.levels):
            if i == self.selected:
                # Highlight selected
                color = (255, 255, 50)
                pygame.draw.rect(self.screen, (100, 100, 0), 
                               (50, y_offset - 10, self.WIDTH - 100, 80))
            else:
                color = (200, 200, 200)
            
            # Level icon
            icon = self.icons.get(level['icon'])
            if icon:
                self.screen.blit(icon, (80, y_offset - 5))
            
            # Level name
            text = option_font.render(str(level['name']), True, color)
            self.screen.blit(text, (160, y_offset))
            
            # Description
            desc_text = desc_font.render(str(level['desc']), True, (150, 150, 150))
            self.screen.blit(desc_text, (160, y_offset + 35))
            
            y_offset += 100
        
        # Instructions
        inst_font = pygame.font.Font(None, 20)
        inst1 = inst_font.render("UP/DOWN: Select | ENTER: Play | ESC: Quit", True, (100, 200, 100))
        self.screen.blit(inst1, (self.WIDTH // 2 - 200, self.HEIGHT - 50))
        
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
