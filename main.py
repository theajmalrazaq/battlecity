
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
    pygame = None
    PYGAME_AVAILABLE = False
    print("Warning: pygame not installed. Running in headless mode.")


class BattleCityGame:
   

    def __init__(self, level=1, use_graphics=True):
      
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
        
        # Track last pressed direction key to handle multi-key presses
        self.last_direction_pressed = 'NONE'
        
        # Sprite assets
        if self.use_graphics:
            self._load_assets()

    def _load_assets(self):
       
        self.sprites = {}
        asset_dir = os.path.join(os.path.dirname(__file__), 'assets')
        
        if not os.path.exists(asset_dir):
            print(f"Warning: assets directory not found at {asset_dir}")
            return
            
        try:
       
            def load_scaled(name, size=(TILE_SIZE, TILE_SIZE)):
                path = os.path.join(asset_dir, f"{name}.png")
                # Try .jpg as fallback if .png doesn't exist
                if not os.path.exists(path):
                    path = os.path.join(asset_dir, f"{name}.jpg")
                    
                if os.path.exists(path):
                  
                    surf = pygame.image.load(path).convert_alpha()

                    
                    try:
                        w, h = surf.get_width(), surf.get_height()
                        corners = [surf.get_at((0, 0)), surf.get_at((w - 1, 0)), surf.get_at((0, h - 1)), surf.get_at((w - 1, h - 1))]
                        # If any corner already has alpha < 255, assume image has transparency
                        has_alpha = any(c[3] < 255 for c in corners)
                    except Exception:
                        has_alpha = True

                    if not has_alpha:
                        # Pick the most common corner RGB color as background
                        corner_rgbs = [c[:3] for c in corners]
                        bg_color = max(set(corner_rgbs), key=corner_rgbs.count)
                        surf.set_colorkey(bg_color)
                        surf = surf.convert_alpha()

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
                # Power tanks are smaller than other tanks (75% size)
                size = (int(TILE_SIZE * 0.75), int(TILE_SIZE * 0.75)) if t_type == 'power' else (TILE_SIZE, TILE_SIZE)
                base = load_scaled(f"tank_{t_type}", size=size)
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
     
        pass  

    def _place_test_walls(self):
      
        for x in range(2, 10):
            for y in range(5, 15):
                if (x + y) % 3 == 0:
                    self.state.grid.set_terrain(x, y, TERRAIN['BRICK'])

    def _update_terrain_cache(self):
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
    
        input_state = {'direction': 'NONE', 'shoot': False}
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_p:
                    self.paused = not self.paused
                # Shoot on KEY DOWN (edge trigger — catches quick taps)
                elif not self.paused and event.key in (pygame.K_b, pygame.K_SPACE):
                    input_state['shoot'] = True
        
        if not self.paused:
            keys = pygame.key.get_pressed()
            
            # Simple priority-based direction input: prefer most recently pressed key
            # Check in reverse order (RIGHT, LEFT, DOWN, UP) so UP takes priority if multiple pressed
            new_dir = 'NONE'
            if keys[pygame.K_UP]:
                new_dir = 'UP'
            if keys[pygame.K_DOWN]:
                new_dir = 'DOWN'
            if keys[pygame.K_LEFT]:
                new_dir = 'LEFT'
            if keys[pygame.K_RIGHT]:
                new_dir = 'RIGHT'
            
            input_state['direction'] = new_dir
            
        
            if keys[pygame.K_b] or keys[pygame.K_SPACE]:
                input_state['shoot'] = True
        
        return input_state

    def render(self, flip=True):
       
        if not self.use_graphics:
            return
        
     
        # Modern dark background with subtle gradient feel
        self.screen.fill((8, 12, 20))
        

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
        
 
        for tank in self.state.tanks:
            if tank.alive:
                self._draw_tank(tank)
        
   
        for bullet in self.state.bullets.get_active_bullets():
            self._draw_bullet(bullet)
        
      
        self._draw_hud()
        
        if flip:
            pygame.display.flip()

    def _get_terrain_color(self, terrain):
        """Get modern color scheme for terrain type."""
        colors = {
            TERRAIN['EMPTY']: (8, 12, 20),           # Dark background
            TERRAIN['BRICK']: (180, 100, 60),        # Modern orange-brown
            TERRAIN['STEEL']: (120, 140, 160),       # Modern gray-blue
            TERRAIN['WATER']: (60, 140, 200),        # Modern blue
            TERRAIN['FOREST']: (80, 140, 80),        # Modern green
            TERRAIN['EAGLE']: (255, 200, 60)         # Golden
        }
        return colors.get(terrain, (8, 12, 20))

    def _draw_tank(self, tank):
        """Draw a tank on screen with modern styling."""
        y_offset = 40
        
   
        visual_x = tank.x
        visual_y = tank.y
        if tank.direction_name != 'NONE' and tank.move_progress < 1.0:
            visual_x += tank.direction[0] * tank.move_progress
            visual_y += tank.direction[1] * tank.move_progress
        
        # Convert to screen coordinates
        rect_x, rect_y = visual_x * TILE_SIZE, visual_y * TILE_SIZE + y_offset
        
       
        t_type = tank.tank_type.value.lower()
        if tank.is_player:
            t_type = 'player'
      
        d_name = tank.direction_name
        if d_name == 'NONE':
            d_name = 'UP'
            
        sprite_key = f"tank_{t_type}_{d_name}"
        sprite = self.sprites.get(sprite_key)
        
        if sprite:
            # Center smaller sprites on the tile
            sprite_rect = sprite.get_rect()
            offset_x = (TILE_SIZE - sprite_rect.width) // 2
            offset_y = (TILE_SIZE - sprite_rect.height) // 2
            self.screen.blit(sprite, (rect_x + offset_x, rect_y + offset_y))
        else:
        
            x, y = rect_x + TILE_SIZE // 2, rect_y + TILE_SIZE // 2
            radius = TILE_SIZE // 3
            pygame.draw.circle(self.screen, tank.color, (x, y), radius)
            if tank.is_player:
                # Player outline with modern styling
                pygame.draw.circle(self.screen, (100, 200, 255), (x, y), radius + 2, 2)
        
        # Draw modern health bar for Armor/Boss tanks
        if tank.hp > 1:
            bar_width = TILE_SIZE - 4
            bar_height = 4
            fill = (tank.hp / tank.max_hp) * bar_width
            bar_x = rect_x + 2
            bar_y = rect_y + 2
            
            # Modern gradient-like effect with background
            pygame.draw.rect(self.screen, (60, 20, 20), (bar_x, bar_y, bar_width, bar_height))
            # Health bar with better colors
            health_color = (100, 255, 100) if tank.hp > tank.max_hp * 0.5 else (255, 150, 100)
            pygame.draw.rect(self.screen, health_color, (bar_x, bar_y, fill, bar_height))
            # Modern border
            pygame.draw.rect(self.screen, (150, 150, 150), (bar_x, bar_y, bar_width, bar_height), 1)

    def _draw_bullet(self, bullet):
        """Draw a bullet on screen with modern styling."""
        y_offset = 40
        bx, by = bullet.get_precise_position()
        x = bx * TILE_SIZE + TILE_SIZE // 2
        y = by * TILE_SIZE + TILE_SIZE // 2 + y_offset
        
        sprite_key = 'bullet_player' if bullet.owner and bullet.owner.is_player else 'bullet_enemy'
        sprite = self.sprites.get(sprite_key)
        if sprite:
            self.screen.blit(sprite, (int(x) - 3, int(y) - 3))
        else:
            # Modern colors for bullets
            color = (100, 200, 255) if bullet.owner and bullet.owner.is_player else (255, 180, 100)
            pygame.draw.circle(self.screen, color, (int(x), int(y)), 3)
            # Add glow effect
            pygame.draw.circle(self.screen, color, (int(x), int(y)), 5, 1)

    def _draw_hud(self):
        """Draw modern heads-up display."""
        if not PYGAME_AVAILABLE:
            return
        
        font = self._font_hud
        status = self.state.get_status()
        
        # Modern HUD background with gradient effect
        hud_bg_color = (12, 18, 35)
        hud_accent_color = (100, 180, 255)
        
        # Draw HUD background
        pygame.draw.rect(self.screen, hud_bg_color, (0, 0, self.WIDTH, 40))
        # Top border accent
        pygame.draw.line(self.screen, hud_accent_color, (0, 39), (self.WIDTH, 39), 2)
        
        # Create status information with better spacing
        small_font = pygame.font.Font(None, 22)
        
        # Left section: Level and Lives
        level_text = small_font.render(f"LVL {status['level']}", True, (100, 200, 255))
        lives_text = small_font.render(f"LIVES: {status['player_lives']}", True, (100, 200, 255))
        
        self.screen.blit(level_text, (15, 9))
        self.screen.blit(lives_text, (100, 9))
        
        # Middle section: Enemy/Boss info
        if self.level == 'BOSS':
            boss_tank = None
            for tank in self.state.tanks:
                if tank.tank_type.value == 'BOSS':
                    boss_tank = tank
                    break
            
            if boss_tank:
                phase_label = {1: 'PHASE 1', 2: 'PHASE 2', 3: 'PHASE 3'}.get(boss_tank.phase, 'UNKNOWN')
                boss_info = small_font.render(f"BOSS: {boss_tank.hp}/10 HP | {phase_label}", True, (255, 120, 80))
                self.screen.blit(boss_info, (290, 9))
            else:
                victory = small_font.render("⭐ BOSS DEFEATED! ⭐", True, (255, 215, 0))
                self.screen.blit(victory, (290, 9))
        else:
            enemy_info = small_font.render(f"DEFEATED: {status['enemies_defeated']}  |  REMAINING: {status['enemies_remaining']}", True, (100, 200, 255))
            self.screen.blit(enemy_info, (290, 9))
        
        # Right section: Time
        time_text = small_font.render(f"TIME: {status['time']:.0f}s", True, (100, 200, 255))
        time_rect = time_text.get_rect(right=self.WIDTH - 15, top=9)
        self.screen.blit(time_text, time_rect)
        
        # Bottom-right controls hint (subtle)
        ctrl_font = pygame.font.Font(None, 16)
        ctrl_surface = ctrl_font.render("↑↓←→ Move  |  SPACE Shoot  |  P Pause", True, (80, 120, 160))
        ctrl_rect = ctrl_surface.get_rect(right=self.WIDTH - 10, bottom=self.HEIGHT - 5)
        self.screen.blit(ctrl_surface, ctrl_rect)
        
        # Pause overlay
        if self.paused:
            # Semi-transparent overlay
            overlay = pygame.Surface((self.WIDTH, self.HEIGHT))
            overlay.set_alpha(100)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0, 0))
            
            # Pause text
            pause_font = pygame.font.Font(None, 60)
            pause_surface = pause_font.render("PAUSED", True, (255, 200, 80))
            pause_rect = pause_surface.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2))
            
            # Background box for pause text
            box_rect = pause_rect.inflate(100, 50)
            pygame.draw.rect(self.screen, (30, 40, 70), box_rect)
            pygame.draw.rect(self.screen, (100, 180, 255), box_rect, 3)
            
            self.screen.blit(pause_surface, pause_rect)

    def run(self):
        """Main game loop."""
        print(f"Starting Battle City - Level {self.level}")
        print("Controls: Arrow Keys = Move, SPACE / B = Shoot, P = Pause, ESC = Quit")
        
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
        
  
        if not self.running:
            return 
        
        game_ended = True
       
        self._display_game_over()

        return

    def _display_game_over(self):

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
        
   
        print("Returning to menu...")

    def _run_headless(self):
       
        print("Running in headless mode (no graphics)")
        ticks = 0
        max_ticks = 600 
        
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
