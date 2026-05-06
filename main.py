"""
Battle City - Main Entry Point
Minimal test harness for Phase 0 & Phase 1
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import TILE_SIZE, GRID_WIDTH, GRID_HEIGHT, TERRAIN, PLAYER_SPAWN, EAGLE_POSITION
from grid import Grid
from game import GameState, GamePhase
from tank import Tank, TankType

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Warning: pygame not installed. Running in headless mode.")


class BattleCityGame:
    """
    Main game controller.
    Handles pygame initialization, rendering, and game loop.
    """

    def __init__(self, level=1, use_graphics=True):
        """
        Initialize the game.
        
        Args:
            level: Starting level (1, 2, or 'BOSS')
            use_graphics: If True, render with pygame; else headless mode
        """
        self.use_graphics = use_graphics and PYGAME_AVAILABLE
        self.level = level
        
        # Initialize game state
        self.state = GameState(level)
        self._setup_level()
        
        # Pygame
        if self.use_graphics:
            pygame.init()
            self.screen = pygame.display.set_mode(
                (GRID_WIDTH * TILE_SIZE, GRID_HEIGHT * TILE_SIZE)
            )
            pygame.display.set_caption(f"Battle City - Level {level}")
            self.clock = pygame.time.Clock()
        
        self.running = True
        self.paused = False

    def _setup_level(self):
        """Setup level 1 with test configuration."""
        # For now, just place some basic terrain and spawn player
        # CSP map generation will come in Phase 2
        
        # Place eagle
        self.state.grid.set_terrain(EAGLE_POSITION[0], EAGLE_POSITION[1], TERRAIN['EAGLE'])
        
        # Place some test walls
        self._place_test_walls()
        
        # Spawn player
        self.state.spawn_player()
        
        # Setup enemy pool (example: Level 1 has 7 Basic + 5 Fast)
        self.state.enemy_pool = [
            TankType.BASIC, TankType.BASIC, TankType.BASIC, TankType.BASIC,
            TankType.BASIC, TankType.BASIC, TankType.BASIC,
            TankType.FAST, TankType.FAST, TankType.FAST, TankType.FAST, TankType.FAST
        ]

    def _place_test_walls(self):
        """Place some test walls for gameplay."""
        # Create a simple brick maze
        for x in range(2, 10):
            for y in range(5, 15):
                if (x + y) % 3 == 0:
                    self.state.grid.set_terrain(x, y, TERRAIN['BRICK'])

    def handle_input(self):
        """Handle pygame events and return input state."""
        input_state = {'direction': 'NONE', 'shoot': False}
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
        
        if not self.paused:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_UP]:
                input_state['direction'] = 'UP'
            elif keys[pygame.K_DOWN]:
                input_state['direction'] = 'DOWN'
            elif keys[pygame.K_LEFT]:
                input_state['direction'] = 'LEFT'
            elif keys[pygame.K_RIGHT]:
                input_state['direction'] = 'RIGHT'
            
            if keys[pygame.K_z] or keys[pygame.K_LCTRL]:
                input_state['shoot'] = True
        
        return input_state

    def render(self):
        """Render the game using pygame."""
        if not self.use_graphics:
            return
        
        # Clear screen
        self.screen.fill((50, 50, 50))
        
        # Draw grid/terrain
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                terrain = self.state.grid.get_terrain(x, y)
                color = self._get_terrain_color(terrain)
                pygame.draw.rect(
                    self.screen, color,
                    (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                )
        
        # Draw tanks
        for tank in self.state.tanks:
            if tank.alive:
                self._draw_tank(tank)
        
        # Draw bullets
        for bullet in self.state.bullets.get_active_bullets():
            self._draw_bullet(bullet)
        
        # Draw HUD
        self._draw_hud()
        
        pygame.display.flip()

    def _get_terrain_color(self, terrain):
        """Get color for terrain type."""
        colors = {
            TERRAIN['EMPTY']: (80, 80, 90),           # Dark gray
            TERRAIN['BRICK']: (200, 100, 50),         # Orange (unchanged)
            TERRAIN['STEEL']: (0, 200, 255),          # Bright cyan - more prominent
            TERRAIN['WATER']: (0, 120, 255),          # Brighter blue
            TERRAIN['FOREST']: (50, 150, 50),         # Green (unchanged)
            TERRAIN['EAGLE']: (255, 200, 0)           # Yellow (unchanged)
        }
        return colors.get(terrain, (80, 80, 90))

    def _draw_tank(self, tank):
        """Draw a tank on screen."""
        x, y = tank.x * TILE_SIZE + TILE_SIZE // 2, tank.y * TILE_SIZE + TILE_SIZE // 2
        pygame.draw.circle(self.screen, tank.color, (x, y), TILE_SIZE // 3)
        
        # Draw direction indicator
        dir_x = x + (tank.direction[0] * TILE_SIZE // 4)
        dir_y = y + (tank.direction[1] * TILE_SIZE // 4)
        pygame.draw.line(self.screen, (255, 255, 255), (x, y), (dir_x, dir_y), 2)
        
        # Draw HP if armor tank
        if tank.hp > 1:
            font = pygame.font.Font(None, 24)
            hp_text = font.render(str(tank.hp), True, (255, 255, 255))
            self.screen.blit(hp_text, (x - 10, y - 10))

    def _draw_bullet(self, bullet):
        """Draw a bullet on screen."""
        bx, by = bullet.get_precise_position()
        x = bx * TILE_SIZE + TILE_SIZE // 2
        y = by * TILE_SIZE + TILE_SIZE // 2
        pygame.draw.circle(self.screen, (255, 255, 0), (int(x), int(y)), 3)

    def _draw_hud(self):
        """Draw heads-up display."""
        if not PYGAME_AVAILABLE:
            return
        
        font = pygame.font.Font(None, 28)
        status = self.state.get_status()
        
        texts = [
            f"Level: {status['level']}",
            f"Lives: {status['player_lives']}",
            f"Enemies: {status['enemies_defeated']}/{20}",
            f"Active: {status['active_enemies']}",
            f"Bullets: {status['bullets_active']}",
            f"Time: {status['time']:.1f}s",
            "[SPACE] Pause | [ESC] Quit"
        ]
        
        if self.paused:
            texts.insert(0, "PAUSED")
        
        for i, text in enumerate(texts):
            surface = font.render(text, True, (255, 255, 255))
            self.screen.blit(surface, (10, 10 + i * 30))

    def run(self):
        """Main game loop."""
        print(f"Starting Battle City - Level {self.level}")
        print("Controls: Arrow Keys = Move, Z/Ctrl = Shoot, Space = Pause, ESC = Quit")
        
        if self.use_graphics:
            self._run_with_graphics()
        else:
            self._run_headless()

    def _run_with_graphics(self):
        """Game loop with graphics."""
        while self.running and not self.state.is_game_over() and not self.state.is_level_won():
            dt = self.clock.tick(60) / 1000.0  # Convert to seconds
            
            if not self.paused:
                input_state = self.handle_input()
                self.state.tick(dt, input_state)
            else:
                self.handle_input()
            
            self.render()
        
        # Game ended
        status = self.state.get_status()
        print(f"\nGame Over: {self.state.phase.value}")
        print(f"Final Status: {status}")
        
        if PYGAME_AVAILABLE:
            pygame.quit()

    def _run_headless(self):
        """Game loop without graphics (for testing)."""
        print("Running in headless mode (no graphics)")
        ticks = 0
        max_ticks = 600  # 10 seconds at 60 FPS
        
        while self.running and ticks < max_ticks:
            dt = 1.0 / 60.0  # 60 FPS
            self.state.tick(dt)
            ticks += 1
            
            if ticks % 60 == 0:
                status = self.state.get_status()
                print(f"Tick {ticks}: {status}")
            
            if self.state.is_game_over() or self.state.is_level_won():
                break
        
        status = self.state.get_status()
        print(f"\nGame Over: {self.state.phase.value}")
        print(f"Final Status: {status}")


def main():
    """Entry point."""
    game = BattleCityGame(level=1, use_graphics=PYGAME_AVAILABLE)
    game.run()


if __name__ == '__main__':
    main()
