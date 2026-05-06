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
from grid import Grid
from tank import Tank, TankType
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
        
        # Player
        self.player = None
        self.player_lives = PLAYER_LIVES
        
        # Enemy management
        self.active_enemies = 0
        self.enemies_defeated = 0
        self.last_spawn_time = 0.0
        
        # Game time
        self.elapsed_time = 0.0
        self.tick_count = 0
        
        # Events log (for debugging/replay)
        self.events = []

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
            x, y: Position (defaults to PLAYER_SPAWN)
        """
        if x is None:
            x, y = PLAYER_SPAWN
        
        self.player = Tank(TankType.PLAYER, x, y, is_player=True)
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
        if x is None:
            # Choose a spawn point
            spawn_idx = self.enemies_defeated % len(SPAWN_POINTS)
            x, y = SPAWN_POINTS[spawn_idx]
        
        # Check fairness constraint: no spawn within 10 tiles of player
        if self.player:
            dist = abs(x - self.player.x) + abs(y - self.player.y)
            if dist < SPAWN_FAIRNESS_DISTANCE:
                return None  # Spawn blocked by fairness constraint
        
        # Spawn the tank
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
        
        # STEP 1: INPUT - Player keyboard input (with direction change reset for responsiveness)
        if input_state:
            # Reset movement progress if direction changed (makes controls feel responsive)
            new_direction = input_state.get('direction', 'NONE')
            if self.player and new_direction != self.player.direction_name:
                self.player.move_progress = 0.0
            
            # Update direction and shooting
            self.update_player_input(input_state)
        
        # STEP 2: AGENT DECISIONS - Each enemy AI runs its decision logic
        for tank in self.tanks:
            if tank.alive and not tank.is_player:
                # Get AI agent for this tank
                if tank in self.ai_agents:
                    agent = self.ai_agents[tank]
                    agent.decide(dt, self)
        
        # STEP 3: MOVE - All tanks attempt to move (with speed-based fractional movement)
        for tank in self.tanks:
            if not tank.alive:
                continue
            
            if tank.direction_name != 'NONE':
                # Accumulate movement progress based on speed
                # Speed is in tiles/second, dt is in seconds
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

    def __repr__(self):
        return f"GameState(Level {self.level}, Phase={self.phase.value}, Time={self.elapsed_time:.1f}s)"
