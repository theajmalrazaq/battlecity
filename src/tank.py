"""
Tank Entity System
Phase 1B: Tank Classes & Properties
"""

from enum import Enum
from config import TANK_TYPES, DIRECTIONS, TERRAIN


class TankType(Enum):
    """Enumeration of tank types."""
    BASIC = 'BASIC'
    FAST = 'FAST'
    ARMOR = 'ARMOR'
    BOSS = 'BOSS'
    PLAYER = 'PLAYER'


class Tank:
    """
    Base Tank class. Represents any tank in the game (player or enemy).
    
    Properties:
    - Position (x, y): Grid coordinates
    - Direction: Current facing direction (UP, DOWN, LEFT, RIGHT)
    - HP: Health points
    - Movement: Tile-based movement (1 tile at a time)
    - Shooting: Can fire one bullet at a time
    """

    def __init__(self, tank_type, x, y, is_player=False):
        """
        Initialize a tank.
        
        Args:
            tank_type: TankType enum or string ('BASIC', 'FAST', 'ARMOR', 'BOSS', 'PLAYER')
            x, y: Starting position on grid
            is_player: True if this is the player's tank
        """
        self.tank_type = tank_type if isinstance(tank_type, TankType) else TankType[tank_type]
        self.is_player = is_player
        
        # Get tank properties from config
        type_name = self.tank_type.value
        if type_name == 'PLAYER':
            props = TANK_TYPES['BASIC']  # Player uses BASIC stats (or customize as needed)
        else:
            props = TANK_TYPES[type_name]
        
        # Position
        self.x = x
        self.y = y
        
        # Health & stats
        self.max_hp = props['hp']
        self.hp = self.max_hp
        self.speed = props['speed']  # Tiles per tick (0.25 = 1 tile per 4 ticks)
        self.fire_rate = props['fire_rate']  # Seconds between shots
        
        # Direction & movement
        self.direction = DIRECTIONS['UP']  # (dx, dy)
        self.direction_name = 'UP'
        self.move_progress = 0.0  # Progress toward next tile (0.0 to 1.0)
        self.is_moving = False
        self.target_x = x  # Target tile for current movement
        self.target_y = y
        
        # Shooting
        self.fire_cooldown = 0.0  # Seconds until next shot available
        self.has_bullet = False  # Is there a bullet in flight?
        
        # AI
        self.ai_type = props['ai_type']
        self.ai_state = {}  # For model-based agents to store state (e.g., hit_count)
        
        # Rendering
        self.color = props['color']
        self.sprite = None
        
        # Alive flag
        self.alive = True

    def take_damage(self, amount=1):
        """Reduce HP by amount. Returns True if tank is destroyed."""
        self.hp -= amount
        if self.hp <= 0:
            self.alive = False
            return True
        return False

    def heal(self, amount=1):
        """Increase HP (capped at max_hp)."""
        self.hp = min(self.hp + amount, self.max_hp)

    def set_direction(self, direction_name):
        """
        Set tank's facing direction without moving.
        
        Args:
            direction_name: 'UP', 'DOWN', 'LEFT', 'RIGHT', or 'NONE'
        """
        if direction_name in DIRECTIONS:
            self.direction = DIRECTIONS[direction_name]
            self.direction_name = direction_name

    def get_position(self):
        """Return current grid position as (x, y)."""
        return (self.x, self.y)

    def set_position(self, x, y):
        """Directly set tank position (used during initialization/spawning)."""
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = y
        self.move_progress = 0.0

    def get_forward_tile(self):
        """
        Get the tile in front of this tank (in its facing direction).
        
        Returns:
            (x, y) of the next tile in direction, or current position if no direction
        """
        dx, dy = self.direction
        return (self.x + dx, self.y + dy)

    def ready_to_shoot(self):
        """Check if tank can shoot (cooldown expired)."""
        return self.fire_cooldown <= 0.0 and not self.has_bullet

    def shoot(self):
        """
        Mark this tank as having fired a bullet.
        Returns cooldown time before next shot.
        """
        if self.ready_to_shoot():
            self.has_bullet = True
            self.fire_cooldown = self.fire_rate
            return True
        return False

    def reset_shot(self):
        """Reset bullet state after bullet is destroyed or hits something."""
        self.has_bullet = False

    def update(self, dt):
        """
        Update tank state for this tick.
        
        Args:
            dt: Delta time in seconds since last update
        """
        # Update fire cooldown
        if self.fire_cooldown > 0.0:
            self.fire_cooldown -= dt

    def __repr__(self):
        return f"Tank({self.tank_type.value} at ({self.x}, {self.y}), HP={self.hp}/{self.max_hp})"
