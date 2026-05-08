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
            self.WIDTH = GRID_WIDTH * TILE_SIZE
            self.HEIGHT = GRID_HEIGHT * TILE_SIZE + 40 # Padding for HUD
            self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
            pygame.display.set_caption(f"Battle City - Level {level}")
            self.clock = pygame.time.Clock()
            # Pre-create font objects (BUG 8 fix: not per-frame)
            self._font_small = pygame.font.Font(None, 20)
            self._font_hud   = pygame.font.Font(None, 28)
        
        self.running = True
        self.paused = False
        
        # Sprite assets
        if self.use_graphics:
            self._load_assets()

    def _load_assets(self):
        """Load and scale sprite assets."""
        self.sprites = {}
        asset_dir = os.path.join(os.path.dirname(__file__), 'assets')
        
        if not os.path.exists(asset_dir):
            print(f"Warning: assets directory not found at {asset_dir}")
            return
            
        try:
            # Helper to load, scale, and handle alpha
            def load_scaled(name, size=(TILE_SIZE, TILE_SIZE)):
                path = os.path.join(asset_dir, f"{name}.png")
                if os.path.exists(path):
                    # Load as RGBA to respect the deep clean we just did
                    surf = pygame.image.load(path).convert_alpha()
                    return pygame.transform.scale(surf, size)
                return None

            # Load terrain
            self.sprites['tile_brick'] = load_scaled('tile_brick')
            self.sprites['tile_steel'] = load_scaled('tile_steel')
            self.sprites['tile_water'] = load_scaled('tile_water')
            self.sprites['tile_forest'] = load_scaled('tile_forest')
            self.sprites['tile_eagle'] = load_scaled('tile_eagle')
            
            # Load tanks and create rotations
            tank_types = ['player', 'basic', 'fast', 'armor', 'power', 'boss']
            for t_type in tank_types:
                base = load_scaled(f"tank_{t_type}")
                if base:
                    # Map directions to rotation angles (assuming base faces UP)
                    # Fixed inversion: UP=base, DOWN=180, LEFT=90, RIGHT=270
                    self.sprites[f"tank_{t_type}_UP"] = base
                    self.sprites[f"tank_{t_type}_LEFT"] = pygame.transform.rotate(base, 90)
                    self.sprites[f"tank_{t_type}_DOWN"] = pygame.transform.rotate(base, 180)
                    self.sprites[f"tank_{t_type}_RIGHT"] = pygame.transform.rotate(base, 270)
            
            # Bullet sprites (Colored based on owner)
            self.sprites['bullet_player'] = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(self.sprites['bullet_player'], (0, 255, 255), (3, 3), 3) # Cyan
            pygame.draw.circle(self.sprites['bullet_player'], (255, 255, 255), (3, 3), 1)
            
            self.sprites['bullet_enemy'] = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(self.sprites['bullet_enemy'], (255, 200, 0), (3, 3), 3) # Yellow/Orange
            pygame.draw.circle(self.sprites['bullet_enemy'], (255, 255, 255), (3, 3), 1)

        except Exception as e:
            print(f"Error loading assets: {e}")

    def _setup_level(self):
        """
        Level setup is fully handled by GameState.__init__ via LevelGenerator (CSP-based).
        This method is intentionally a no-op — do NOT add map edits, enemy pool overrides,
        or player spawns here, as GameState already does all of that correctly.
        """
        pass  # All setup done by GameState.__init__ / LevelGenerator / CSP

    def _place_test_walls(self):
        """Place some test walls for gameplay."""
        # Create a simple brick maze
        for x in range(2, 10):
            for y in range(5, 15):
                if (x + y) % 3 == 0:
                    self.state.grid.set_terrain(x, y, TERRAIN['BRICK'])

    def _update_terrain_cache(self):
        """Pre-render terrain to a surface for faster rendering."""
        if not self.use_graphics:
            return
        
        self.terrain_cache = pygame.Surface(
            (GRID_WIDTH * TILE_SIZE, GRID_HEIGHT * TILE_SIZE)
        )
        
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                terrain = self.state.grid.get_terrain(x, y)
                color = self._get_terrain_color(terrain)
                pygame.draw.rect(
                    self.terrain_cache, color,
                    (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                )

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
                # Shoot on KEY DOWN (edge trigger — catches quick taps)
                elif not self.paused and event.key in (pygame.K_b, pygame.K_LSHIFT):
                    input_state['shoot'] = True
        
        if not self.paused:
            keys = pygame.key.get_pressed()
            # Check direction keys
            new_dir = 'NONE'
            if keys[pygame.K_UP]: new_dir = 'UP'
            elif keys[pygame.K_DOWN]: new_dir = 'DOWN'
            elif keys[pygame.K_LEFT]: new_dir = 'LEFT'
            elif keys[pygame.K_RIGHT]: new_dir = 'RIGHT'
            
            input_state['direction'] = new_dir
            
            # SHOOTING (Isolated from direction)
            # Remove SPACE from shoot to avoid pause conflict
            if keys[pygame.K_b] or keys[pygame.K_LSHIFT]:
                input_state['shoot'] = True
        
        return input_state

    def render(self, flip=True):
        """Render the game using pygame."""
        if not self.use_graphics:
            return
        
        # Draw background (Pure Black)
        self.screen.fill((0, 0, 0))
        
        # Draw terrain (Offset by 40px for HUD)
        y_offset = 40
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                terrain = self.state.grid.get_terrain(x, y)
                if terrain == TERRAIN['EMPTY']:
                    continue
                
                sprite = None
                if terrain == TERRAIN['BRICK']: sprite = self.sprites.get('tile_brick')
                elif terrain == TERRAIN['STEEL']: sprite = self.sprites.get('tile_steel')
                elif terrain == TERRAIN['WATER']: sprite = self.sprites.get('tile_water')
                elif terrain == TERRAIN['FOREST']: sprite = self.sprites.get('tile_forest')
                elif terrain == TERRAIN['EAGLE']: sprite = self.sprites.get('tile_eagle')
                
                draw_pos = (x * TILE_SIZE, y * TILE_SIZE + y_offset)
                if sprite:
                    self.screen.blit(sprite, draw_pos)
                else:
                    color = self._get_terrain_color(terrain)
                    pygame.draw.rect(self.screen, color, (draw_pos[0], draw_pos[1], TILE_SIZE, TILE_SIZE))
        
        # Draw tanks
        for tank in self.state.tanks:
            if tank.alive:
                self._draw_tank(tank)
        
        # Draw bullets
        for bullet in self.state.bullets.get_active_bullets():
            self._draw_bullet(bullet)
        
        # Draw HUD
        self._draw_hud()
        
        if flip:
            pygame.display.flip()

    def _get_terrain_color(self, terrain):
        """Get color for terrain type (Fallback)."""
        colors = {
            TERRAIN['EMPTY']: (0, 0, 0),             # Pure black background
            TERRAIN['BRICK']: (200, 100, 50),
            TERRAIN['STEEL']: (100, 100, 120),
            TERRAIN['WATER']: (0, 0, 255),
            TERRAIN['FOREST']: (0, 255, 0),
            TERRAIN['EAGLE']: (255, 215, 0)
        }
        return colors.get(terrain, (0, 0, 0))

    def _draw_tank(self, tank):
        """Draw a tank on screen using sprites with smooth pixel interpolation."""
        y_offset = 40
        
        # SMOOTH INTERPOLATION: Calculate visual pixel position
        # Fix: If not moving, don't interpolate (prevents phasing through walls)
        visual_x = tank.x
        visual_y = tank.y
        if tank.direction_name != 'NONE' and tank.move_progress < 1.0:
            visual_x += tank.direction[0] * tank.move_progress
            visual_y += tank.direction[1] * tank.move_progress
        
        # Convert to screen coordinates
        rect_x, rect_y = visual_x * TILE_SIZE, visual_y * TILE_SIZE + y_offset
        
        # Determine sprite key
        t_type = tank.tank_type.value.lower()
        if tank.is_player:
            t_type = 'player'
        
        # Get direction (default to UP if NONE)
        d_name = tank.direction_name
        if d_name == 'NONE':
            d_name = 'UP'
            
        sprite_key = f"tank_{t_type}_{d_name}"
        sprite = self.sprites.get(sprite_key)
        
        if sprite:
            self.screen.blit(sprite, (rect_x, rect_y))
        else:
            # Fallback to primitive shapes
            x, y = rect_x + TILE_SIZE // 2, rect_y + TILE_SIZE // 2
            radius = TILE_SIZE // 3 if tank.is_player else TILE_SIZE // 4
            pygame.draw.circle(self.screen, tank.color, (x, y), radius)
            if tank.is_player:
                pygame.draw.circle(self.screen, (255, 255, 0), (x, y), radius + 2, 2)
        
        # Draw health bar for Armor/Boss tanks
        if tank.hp > 1:
            bar_width = TILE_SIZE - 4
            bar_height = 4
            fill = (tank.hp / tank.max_hp) * bar_width
            
            # Background (Red)
            pygame.draw.rect(self.screen, (100, 0, 0), (rect_x + 2, rect_y + 2, bar_width, bar_height))
            # Foreground (Green)
            pygame.draw.rect(self.screen, (0, 255, 0), (rect_x + 2, rect_y + 2, fill, bar_height))
            # Border
            pygame.draw.rect(self.screen, (255, 255, 255), (rect_x + 2, rect_y + 2, bar_width, bar_height), 1)

    def _draw_bullet(self, bullet):
        """Draw a bullet on screen."""
        y_offset = 40
        bx, by = bullet.get_precise_position()
        x = bx * TILE_SIZE + TILE_SIZE // 2
        y = by * TILE_SIZE + TILE_SIZE // 2 + y_offset
        
        sprite_key = 'bullet_player' if bullet.owner and bullet.owner.is_player else 'bullet_enemy'
        sprite = self.sprites.get(sprite_key)
        if sprite:
            self.screen.blit(sprite, (int(x) - 3, int(y) - 3))
        else:
            color = (0, 255, 255) if bullet.owner and bullet.owner.is_player else (255, 255, 0)
            pygame.draw.circle(self.screen, color, (int(x), int(y)), 3)

    def _draw_hud(self):
        """Draw heads-up display."""
        if not PYGAME_AVAILABLE:
            return
        
        font = self._font_hud
        status = self.state.get_status()
        
        texts = [
            f"LVL {status['level']} | LIVES: {status['player_lives']}",
        ]
        
        # Add boss info if boss level
        if self.level == 'BOSS':
            boss_tank = None
            for tank in self.state.tanks:
                if tank.tank_type.value == 'BOSS':
                    boss_tank = tank
                    break
            
            if boss_tank:
                phase_label = {1: 'AGGR', 2: 'TACT', 3: 'DESP'}.get(boss_tank.phase, '?')
                texts.append(f"BOSS HP: {boss_tank.hp}/10 | {phase_label}")
            else:
                texts.append("BOSS DEFEATED!")
        else:
            texts.append(f"ENEMY: {status['enemies_defeated']} | REM: {status['enemies_remaining']}")
        
        texts.append(f"TIME: {status['time']:.0f}s")
        
        # Draw sleek dark HUD bar at top
        pygame.draw.rect(self.screen, (20, 20, 25), (0, 0, self.WIDTH, 40))
        pygame.draw.line(self.screen, (255, 200, 50), (0, 39), (self.WIDTH, 39), 2) # Golden divider
        
        font = pygame.font.Font(None, 24)
        hud_str = "   ".join(texts)
        surface = font.render(hud_str, True, (255, 255, 255))
        self.screen.blit(surface, (20, 10))
        
        # Small controls text at bottom
        ctrl_font = pygame.font.Font(None, 18)
        ctrl_surface = ctrl_font.render("ARROWS: Move | B: Shoot | SPACE: Pause", True, (100, 100, 100))
        self.screen.blit(ctrl_surface, (self.WIDTH - 250, self.HEIGHT - 20))
        
        if self.paused:
            pause_surface = font.render("PAUSED", True, (255, 255, 0))
            self.screen.blit(pause_surface, (self.WIDTH // 2 - 40, self.HEIGHT // 2))

    def run(self):
        """Main game loop."""
        print(f"Starting Battle City - Level {self.level}")
        print("Controls: Arrow Keys = Move, B / Shift = Shoot, Space = Pause, ESC = Quit")
        
        if self.use_graphics:
            self._run_with_graphics()
        else:
            self._run_headless()

    def _run_with_graphics(self):
        """Game loop with graphics."""
        game_ended = False
        
        while self.running and not self.state.is_game_over() and not self.state.is_level_won():
            dt = self.clock.tick(60) / 1000.0  # Convert to seconds
            
            if not self.paused:
                input_state = self.handle_input()
                self.state.tick(dt, input_state)
            else:
                self.handle_input()
            
            self.render()
        
        # Only display game over if game actually ended (not just window closed)
        if not self.running:
            return  # User closed window, don't show game over screen
        
        game_ended = True
        # Game ended - display result
        self._display_game_over()
        
        # Return to menu instead of quitting
        return

    def _display_game_over(self):
        """Display game over message and wait for user."""
        if not self.use_graphics:
            return
        
        # Get final status
        status = self.state.get_status()
        if self.state.is_game_over():
            reason = self.state.get_end_reason()
            title_msg = f"GAME OVER - {reason}"
            color = (255, 50, 50)
        else:
            reason = "Level Complete!"
            title_msg = "LEVEL WON!"
            color = (50, 255, 50)
        
        # Print to console
        print(f"\n{'='*50}")
        print(f"Game Ended: {reason}")
        print(f"Lives Remaining: {status['player_lives']}")
        print(f"Enemies Defeated: {status['enemies_defeated']}")
        print(f"Time Played: {status['time']:.1f}s")
        print(f"{'='*50}\n")
        
        # Display for 5 seconds (or until ESC pressed)
        start_time = pygame.time.get_ticks()
        
        while True:
            elapsed = pygame.time.get_ticks() - start_time
            if elapsed > 5000:  # Auto-close after 5 seconds
                break
            
            # Handle input events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                        return
                    elif event.key == pygame.K_SPACE:
                        # Allow restart with space
                        return
            
            # Render base layer
            self.render(flip=False)
            
            # Semi-transparent overlay
            overlay = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            
            # Message
            font_big = pygame.font.Font(None, 56)
            surface = font_big.render(title_msg, True, color)
            self.screen.blit(surface, (self.WIDTH // 2 - surface.get_width() // 2, self.HEIGHT // 2 - 80))
            
            # Stats
            font_medium = pygame.font.Font(None, 32)
            stat_text = f"Lives: {status['player_lives']} | Enemies: {status['enemies_defeated']} | Time: {status['time']:.1f}s"
            surface = font_medium.render(stat_text, True, (200, 200, 200))
            self.screen.blit(surface, (self.WIDTH // 2 - surface.get_width() // 2, self.HEIGHT // 2 + 20))
            
            # Prompt
            surface = font_medium.render("Press SPACE to return to menu", True, (255, 255, 255))
            self.screen.blit(surface, (self.WIDTH // 2 - surface.get_width() // 2, self.HEIGHT // 2 + 80))
            
            pygame.display.flip()
            self.clock.tick(60)
        
        # Auto-close after 5 seconds
        print("Returning to menu...")

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
    import argparse
    
    parser = argparse.ArgumentParser(description='Battle City - AI Semester Project')
    parser.add_argument('--level', type=str, default='1', help='Level to play: 1, 2, or BOSS')
    parser.add_argument('--no-graphics', action='store_true', help='Run in headless mode (no graphics)')
    args = parser.parse_args()
    
    # Parse level argument
    level = args.level.upper() if args.level.upper() == 'BOSS' else int(args.level)
    
    print(f"\n{'='*50}")
    print(f"Battle City - Level {level}")
    if level == 'BOSS':
        print("BOSS ARENA - Phase 3 Challenge!")
    print(f"{'='*50}\n")
    
    game = BattleCityGame(level=level, use_graphics=PYGAME_AVAILABLE and not args.no_graphics)
    game.run()


if __name__ == '__main__':
    main()
