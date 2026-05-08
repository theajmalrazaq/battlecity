#!/usr/bin/env python3
"""
Battle City - Main Menu
Level selection and game entry point
"""

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

import sys
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
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Battle City - Level Select")
        self.clock = pygame.time.Clock()
        self.selected = 0
        self.levels = [
            {'name': 'Level 1: Brick Maze', 'value': 1, 'desc': 'Intro: BFS pathfinding, dynamic map changes'},
            {'name': 'Level 2: Steel Fortress', 'value': 2, 'desc': 'Challenge: A* with cost-awareness'},
            {'name': 'Level 3: BOSS Battle', 'value': 'BOSS', 'desc': 'Advanced: Minimax adversarial search'}
        ]
    
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
            
            # Level name
            text = option_font.render(f"{'→ ' if i == self.selected else '  '}{level['name']}", True, color)
            self.screen.blit(text, (80, y_offset))
            
            # Description
            desc_text = desc_font.render(level['desc'], True, (150, 150, 150))
            self.screen.blit(desc_text, (120, y_offset + 35))
            
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
        while True:
            menu = MainMenu()
            level = menu.run()
            menu.screen = None  # Clear the screen
            
            if level is None:
                print("Exiting Battle City...")
                break
            
            # Import game after menu selection
            from main import BattleCityGame
            
            print(f"\nStarting Level {level}...")
            game = BattleCityGame(level)
            game.run()
            
            # After game ends, show menu again
            print("\nReturning to menu...\n")
    
    finally:
        pygame.quit()
        sys.exit(0)


if __name__ == '__main__':
    main()
