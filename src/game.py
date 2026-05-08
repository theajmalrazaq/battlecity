"""
Game State & Main Game Loop
Phase 1E: Game Loop (10-step sequence)
"""

import time
from enum import Enum
from config import (
    DIRECTIONS, TERRAIN, GAME_STATE, SPAWN_POINTS, PLAYER_SPAWN, EAGLE_POSITION,
    PLAYER_LIVES, MAX_ACTIVE_TANKS, SPAWN_DELAY, LEVEL_ENEMY_POOL,
    FPS, SPAWN_FAIRNESS_DISTANCE
)
import random
from grid import Grid
from tank import Tank, TankType, BossTank
from bullet import BulletManager
from collision import CollisionDetector
from map_generator import LevelGenerator
from ai.agents import AIAgentFactory


class GamePhase(Enum):
    """Enum for game state."""
    PLAYING = 'playing'
    PAUSED = 'paused'
    LEVEL_WIN = 'level_win'
    GAME_OVER = 'game_over'


class GameState:
    """
    Represents the complete state of a game session.
    """

    def __init__(self, level=1):
        """
        Initialize a new game.
        
        Args:
            level: Level number (1, 2, or 'BOSS')
        """
        self.level = level
        self.phase = GamePhase.PLAYING
        
        # Core systems
        self.grid = Grid()
        self.tanks = []  # All tanks (player + enemies)
        self.bullets = BulletManager()
        self.ai_agents = {}  # Tank -> AIAgent mapping
        self.collision_detector = CollisionDetector(
            self.grid, self.tanks, self.bullets, EAGLE_POSITION
        )
        
        # Generate level using CSP
        level_gen = LevelGenerator(level)
        level_data = level_gen.generate()
        
        if level_data is None:
            print(f"ERROR: Failed to generate level {level}")
            self.enemy_pool = []
        else:
            # Load generated map into grid
            for y in range(len(level_data['map'])):
                for x in range(len(level_data['map'][y])):
                    self.grid.set_terrain(x, y, level_data['map'][y][x])
            
            # Set enemy pool
            self.enemy_pool = level_data['enemy_pool'][:]
        
        # Game time
        self.elapsed_time = 0.0
        self.tick_count = 0
        
        # Events log (for debugging/replay)
        self.events = []
        
        # Player
        self.player = None
        self.player_lives = PLAYER_LIVES
        
        # Enemy management
        self.active_enemies = 0
        self.enemies_defeated = 0
        self.last_spawn_time = 0.0
        
        # Spawn boss immediately if boss level (before player so boss is at correct location)
        if self.level == 'BOSS' and self.enemy_pool:
            boss_type = self.enemy_pool.pop(0)
            # Pre-spawn boss at (13, 7) before player, so player doesn't collide
            self.active_enemies = 0  # Reset counter before spawning
            boss = self.spawn_enemy(boss_type)  # Spawn boss at (13, 7)
        
        # Now spawn player (will be at 13, 18 for boss level, which is clear)
        self.spawn_player()  # Spawn player at start

    def add_event(self, event_type, data):
        """Log a game event."""
        self.events.append({
            'time': self.elapsed_time,
            'tick': self.tick_count,
            'type': event_type,
            'data': data
        })

    def spawn_player(self, x=None, y=None):
        """
        Spawn the player tank.
        
        Args:
            x, y: Position (defaults to PLAYER_SPAWN, or top-left corner for BOSS level)
        """
        if x is None:
            if self.level == 'BOSS':
                # Boss level: spawn at top-left corner outside the arena (safe spawn zone)
                # Arena is at (7-18, 7-18), so (0,0) is far away and safe
                x, y = 0, 0
            else:
                x, y = PLAYER_SPAWN
        
        # Only create new player if we don't have one, or clear the old one
        if self.player and self.player.alive:
            self.player.alive = False  # Mark old player as dead
        
        self.player = Tank(TankType.PLAYER, x, y, is_player=True)
        
        # Remove dead players from tanks list before adding new one
        self.tanks = [t for t in self.tanks if t.alive or t == self.player]
        
        if self.player not in self.tanks:
            self.tanks.append(self.player)
        
        self.add_event('player_spawned', {'pos': (x, y)})

    def spawn_enemy(self, tank_type, x=None, y=None):
        """
        Spawn an enemy tank at a spawn point.
        
        Args:
            tank_type: TankType or string
            x, y: Optional specific position
        
        Returns:
            Tank object if spawned, None if fairness constraint violated
        """
        tank_type_str = tank_type.value if isinstance(tank_type, TankType) else tank_type
        
        # Special handling for BOSS level
        if self.level == 'BOSS' and tank_type_str == 'BOSS':
            # Boss spawns at center-top of arena (13, 7)
            x, y = 13, 7
        elif x is None:
            # Choose a random spawn point for variety (not predictable cycling)
            spawn_point = random.choice(SPAWN_POINTS)
            x, y = spawn_point
        
        # Check fairness constraint: no spawn within 5 tiles of player
        if self.player and self.level != 'BOSS':  # Skip fairness check for boss battle
            dist = abs(x - self.player.x) + abs(y - self.player.y)
            if dist < SPAWN_FAIRNESS_DISTANCE:
                return None  # Spawn blocked by fairness constraint
        
        # Spawn the tank (special handling for BOSS)
        if tank_type_str == 'BOSS':
            # Phase 3B: Create BossTank for boss level
            tank = BossTank(x, y)
        else:
            tank = Tank(tank_type, x, y, is_player=False)
        
        self.tanks.append(tank)
        self.active_enemies += 1
        
        # Create AI agent for this tank
        ai_agent = AIAgentFactory.create_agent(tank, self.grid, tank.tank_type.value, self.grid.eagle_pos if hasattr(self.grid, 'eagle_pos') else EAGLE_POSITION)
        self.ai_agents[tank] = ai_agent
        
        self.add_event('enemy_spawned', {
            'type': tank.tank_type.value,
            'pos': (x, y)
        })
        return tank

    def check_spawn(self, dt):
        """
        Check if it's time to spawn a new enemy (tick 8 in game loop).
        
        Args:
            dt: Delta time since last update
        """
        if not self.enemy_pool:
            return  # No more enemies to spawn
        
        if self.active_enemies >= MAX_ACTIVE_TANKS:
            return  # Max active tanks reached
        
        self.last_spawn_time += dt
        if self.last_spawn_time >= SPAWN_DELAY:
            self.last_spawn_time = 0.0
            
            # Spawn next enemy from pool
            tank_type = self.enemy_pool.pop(0)
            tank = self.spawn_enemy(tank_type)
            if tank:
                return
            else:
                # If fairness constraint blocked spawn, try again next cycle
                self.enemy_pool.insert(0, tank_type)

    def update_player_input(self, input_state):
        """
        Handle player input.
        
        Args:
            input_state: Dict with keys 'direction' and 'shoot'
        """
        if not self.player or not self.player.alive:
            return
        
        direction = input_state.get('direction', 'NONE')
        shoot = input_state.get('shoot', False)
        
        # Update direction
        if direction in DIRECTIONS:
            self.player.set_direction(direction)
        
        # Queue shot if requested
        if shoot and self.player.ready_to_shoot():
            self.player.shoot()

    def tick(self, dt, input_state=None):
        """
        Execute one game tick (10-step sequence from spec).
        
        Args:
            dt: Delta time in seconds
            input_state: Player input dict {'direction': ..., 'shoot': ...}
        """
        if self.phase != GamePhase.PLAYING:
            return
        
        self.tick_count += 1
        self.elapsed_time += dt
        
        # STEP 1: INPUT - Player keyboard input
        if input_state:
            # Update direction and shooting
            self.update_player_input(input_state)
        
        # STEP 2: AGENT DECISIONS - Each enemy AI runs its decision logic
        for tank in self.tanks:
            if tank.alive and not tank.is_player:
                # Get AI agent for this tank
                if tank in self.ai_agents:
                    agent = self.ai_agents[tank]
                    agent.decide(dt, self)
        
        # STEP 3: MOVE - All tanks attempt to move
        for tank in self.tanks:
            if not tank.alive:
                continue
            
            if tank.direction_name != 'NONE':
                # Player: move 1 tile per keypress with cooldown for controlled navigation
                if tank.is_player:
                    if tank.move_cooldown <= 0.0:
                        next_x = tank.x + tank.direction[0]
                        next_y = tank.y + tank.direction[1]
                        
                        if self.collision_detector.can_tank_move_to(tank, next_x, next_y):
                            tank.x = next_x
                            tank.y = next_y
                            tank.move_cooldown = 0.15  # 150ms cooldown between moves
                else:
                    # Enemies: use time-based movement (speed-based)
                    tank.move_progress += tank.speed * dt
                    
                    # Check if we've accumulated enough progress for a full tile move
                    while tank.move_progress >= 1.0:
                        next_x = tank.x + tank.direction[0]
                        next_y = tank.y + tank.direction[1]
                        
                        if self.collision_detector.can_tank_move_to(tank, next_x, next_y):
                            tank.x = next_x
                            tank.y = next_y
                            tank.move_progress -= 1.0
                        else:
                            # Blocked - don't move, but keep accumulated progress
                            # Next frame when path clears, we can continue immediately
                            break
        
        # Check for enemy collision with player (damage)
        if self.player and self.player.alive:
            for tank in self.tanks:
                if tank.alive and not tank.is_player and tank.x == self.player.x and tank.y == self.player.y:
                    # Enemy collided with player - damage player
                    self.player.take_damage(1)
        
        # Check for tank reaching eagle (game over)
        for tank in self.tanks:
            if tank.alive:
                terrain_at_tank = self.grid.get_terrain(int(tank.x), int(tank.y))
                if terrain_at_tank == TERRAIN['EAGLE']:
                    # Tank reached eagle - game over
                    if tank.is_player:
                        # Player reached enemy eagle - WIN!
                        self.phase = GamePhase.LEVEL_WIN
                        self.add_event('game_over', {'reason': 'player_reached_eagle'})
                    else:
                        # Enemy reached player eagle - LOSE!
                        self.phase = GamePhase.GAME_OVER
                        self.add_event('game_over', {'reason': 'eagle_destroyed'})
                    break
        
        # STEP 4: SHOOT - All tanks that chose to shoot fire a bullet
        for tank in self.tanks:
            if not tank.alive:
                continue
            
            if tank.has_bullet:  # Tank fired this tick
                bullet = self.bullets.spawn_bullet(tank)
        
        # STEP 5: BULLET UPDATE - All active bullets advance one tile
        self.bullets.update_bullets(dt)
        
        # STEP 6: COLLISION DETECTION - Check all collisions
        collision_events = self.collision_detector.check_all_bullet_collisions()
        
        # STEP 7: STATE UPDATE - Destroy walls, reduce tank HP, remove dead tanks
        for event in collision_events:
            result = self.collision_detector.resolve_collision(event)
            
            # Track enemy defeats
            if result.get('tank_destroyed') and not event['target'].is_player:
                self.enemies_defeated += 1
                self.active_enemies -= 1
                self.add_event('enemy_defeated', {
                    'type': event['target'].tank_type.value,
                    'count': self.enemies_defeated
                })
            
            # Check for eagle destruction
            if result.get('eagle_destroyed'):
                self.phase = GamePhase.GAME_OVER
                self.add_event('game_over', {'reason': 'eagle_destroyed'})
        
        # Remove dead tanks
        dead_tanks = [t for t in self.tanks if not t.alive]
        self.tanks = [t for t in self.tanks if t.alive]
        
        # Update collision detector's reference to tanks list
        self.collision_detector.tanks = self.tanks
        
        # Clean up AI agents for dead tanks
        for tank in dead_tanks:
            if tank in self.ai_agents:
                del self.ai_agents[tank]
        
        # Player death
        if self.player and not self.player.alive:
            self.player_lives -= 1
            if self.player_lives > 0:
                # Respawn player
                self.spawn_player()
                self.add_event('player_respawned', {'lives_remaining': self.player_lives})
            else:
                self.phase = GamePhase.GAME_OVER
                self.add_event('game_over', {'reason': 'out_of_lives'})
        
        # STEP 8: SPAWN CHECK - If fewer than 4 enemies active, spawn next
        self.check_spawn(dt)
        
        # STEP 9: RENDER - (Handled by UI/graphics layer, not here)
        
        # STEP 10: WIN/LOSE CHECK
        if self.enemies_defeated >= LEVEL_ENEMY_POOL and not self.enemy_pool:
            self.phase = GamePhase.LEVEL_WIN
            self.add_event('level_complete', {'level': self.level})
        
        # Update tank cooldowns
        for tank in self.tanks:
            tank.update(dt)

    def is_playing(self):
        """Check if game is actively running."""
        return self.phase == GamePhase.PLAYING

    def is_game_over(self):
        """Check if game has ended."""
        return self.phase == GamePhase.GAME_OVER

    def is_level_won(self):
        """Check if level was completed."""
        return self.phase == GamePhase.LEVEL_WIN

    def get_status(self):
        """Get human-readable game status."""
        return {
            'level': self.level,
            'phase': self.phase.value,
            'player_lives': self.player_lives,
            'enemies_defeated': self.enemies_defeated,
            'active_enemies': self.active_enemies,
            'enemies_remaining': len(self.enemy_pool),
            'bullets_active': self.bullets.get_bullet_count(),
            'time': self.elapsed_time,
            'ticks': self.tick_count
        }

    def get_end_reason(self):
        """Get human-readable reason for game end."""
        if self.phase == GamePhase.LEVEL_WIN:
            return "Level Complete!"
        elif self.phase == GamePhase.GAME_OVER:
            # Check why it ended
            if self.player_lives <= 0:
                return "Out of Lives!"
            else:
                # Find the last event that ended the game
                for event in reversed(self.events):
                    if event['type'] == 'game_over':
                        reason = event['data'].get('reason', 'Unknown')
                        if reason == 'eagle_destroyed':
                            return "Eagle Destroyed!"
                        elif reason == 'out_of_lives':
                            return "Out of Lives!"
                return "Game Over!"
        return "Game Over!"

    def __repr__(self):
        return f"GameState(Level {self.level}, Phase={self.phase.value}, Time={self.elapsed_time:.1f}s)"
