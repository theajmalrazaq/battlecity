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
            props = TANK_TYPES['FAST']  # Player uses FAST stats (speed) for responsive controls
            props = props.copy()
            props['color'] = (200, 200, 200)   # Light gray/white for player
            props['fire_rate'] = 0.8            # Faster fire rate than enemies (0.8s vs 1.5s)
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
        self.move_cooldown = 0.0  # Cooldown timer between moves (for player)
        
        # Shooting
        self.fire_cooldown = 0.0  # Seconds until next shot available
        self.has_bullet = False  # Is there a bullet in flight?
        
        # AI
        self.ai_type = props['ai_type']
        self.ai_state = {}  # For model-based agents to store state (e.g., hit_count)
        
        # Rendering
        self.color = props['color']
        self.sprite = None
        
        # Hit flash (GAP 14 - PDF: Armor tank flashes on each hit to show damage stage)
        self.hit_flash_timer = 0.0  # Counts down from 0.3s after each hit
        
        # Alive flag
        self.alive = True

    def take_damage(self, amount=1):
        """Reduce HP by amount. Returns True if tank is destroyed."""
        self.hp -= amount
        # Trigger hit-flash visual (rendering layer reads hit_flash_timer > 0 to draw white)
        self.hit_flash_timer = 0.3
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
        
        # Update movement cooldown (for player)
        if self.move_cooldown > 0.0:
            self.move_cooldown -= dt
        
        # Decay hit-flash visual timer (GAP 14 - flash on hit)
        if self.hit_flash_timer > 0.0:
            self.hit_flash_timer -= dt

    def __repr__(self):
        return f"Tank({self.tank_type.value} at ({self.x}, {self.y}), HP={self.hp}/{self.max_hp})"


class BossTank(Tank):
    """
    Boss Tank subclass with special abilities and phase mechanics.
    Phase 3B: Boss Tank Implementation
    
    Special features:
    - High HP (10)
    - Fast fire rate that increases with phase
    - Regeneration in Phase 3
    - Phase-based behavior changes
    - Aura effect (damages nearby player)
    """
    
    def __init__(self, x, y):
        """
        Initialize boss tank.
        
        Args:
            x, y: Starting position on grid
        """
        super().__init__(TankType.BOSS, x, y, is_player=False)
        
        # Boss-specific stats
        self.max_hp = 10
        self.hp = 10
        self.speed = 0.2  # Adjusted per phase
        self.fire_rate = 2.0  # Phase 1 fire rate (1 bullet every 2 seconds)
        self.color = (200, 0, 0)  # Bright red for boss
        self.ai_type = 'adversarial'
        
        # Boss phases
        self.phase = 1  # 1 (aggressive), 2 (tactical), 3 (desperate)
        self.phase_transition_time = 0.0
        
        # Boss abilities
        self.regeneration_active = False
        self.regeneration_timer = 0.0
        self.regeneration_rate = 0.5  # HP per second in phase 3
        self.aura_damage = 0.2  # Damage per tick to nearby player
        self.aura_range = 2  # Tiles
        self.rapid_fire_mode = False
        self.rapid_fire_timer = 0.0
        self.rapid_fire_cooldown = 0.3  # Faster fire in phase 2+
    
    def update(self, dt):
        """
        Update boss tank state (override parent).
        
        Args:
            dt: Delta time in seconds
        """
        super().update(dt)
        
        # Update phase based on health (spec: Phase 1: 10-7, Phase 2: 6-3, Phase 3: 2-1)
        old_phase = self.phase
        if self.hp >= 7:
            self.phase = 1  # Aggressive (10-7 HP)
        elif self.hp >= 3:
            self.phase = 2  # Tactical (6-3 HP)
        else:
            self.phase = 3  # Desperate (2-1 HP)
        
        # Activate/deactivate abilities based on phase
        if self.phase == 1:
            # Phase 1 (Aggressive): Normal fire rate
            self.fire_rate = 2.0  # 1 bullet every 2 seconds
            self.regeneration_active = False
            self.rapid_fire_mode = False
        elif self.phase == 2:
            # Phase 2 (Tactical): Faster fire rate
            self.fire_rate = 1.5  # 1 bullet every 1.5 seconds (33% faster)
            self.regeneration_active = False
            self.rapid_fire_mode = True
        else:
            # Phase 3 (Desperate): Fastest fire rate + regeneration
            self.fire_rate = 0.8  # 1 bullet every 0.8 seconds (60% faster than Phase 1)
            self.regeneration_active = True
            self.rapid_fire_mode = True
            
            # Heal over time
            self.regeneration_timer += dt
            if self.regeneration_timer >= 1.0:
                if self.hp < self.max_hp:
                    self.hp = min(self.hp + 1, self.max_hp)
                    self.regeneration_timer = 0.0
        
        # Update rapid fire cooldown
        if self.rapid_fire_mode:
            self.rapid_fire_timer += dt
    
    def take_damage(self, amount=1):
        """
        Override take_damage to handle boss phase transitions.
        
        Args:
            amount: Damage amount
        
        Returns:
            True if boss is destroyed
        """
        old_hp = self.hp
        destroyed = super().take_damage(amount)
        
        # Update phase immediately after damage (spec: Phase 1: 10-7, Phase 2: 6-3, Phase 3: 2-1)
        if self.hp >= 7:
            self.phase = 1
            self.regeneration_active = False
            self.rapid_fire_mode = False
            self.fire_rate = 2.0  # Phase 1: 1 bullet every 2 seconds
        elif self.hp >= 3:
            self.phase = 2
            self.regeneration_active = False
            self.fire_rate = 1.5  # Phase 2: 1 bullet every 1.5 seconds
            self.rapid_fire_mode = True
        else:
            self.phase = 3
            self.regeneration_active = True
            self.fire_rate = 0.8  # Phase 3: 1 bullet every 0.8 seconds
            self.rapid_fire_mode = True
        
        # Print phase change notification
        if old_hp > 7 and self.hp <= 7:
            print("Boss entering Phase 2 - TACTICAL MODE!")
        elif old_hp > 3 and self.hp <= 3:
            print("Boss entering Phase 3 - DESPERATE MODE with regeneration!")
        
        return destroyed
    
    def get_phase_description(self):
        """Get human-readable phase description."""
        descriptions = {
            1: "Aggressive (Normal stats)",
            2: "Tactical (Faster fire rate)",
            3: "Desperate (Regeneration + Rapid fire)"
        }
        return f"Phase {self.phase}: {descriptions.get(self.phase, 'Unknown')}"
    
    def __repr__(self):
        return f"BossTank(HP={self.hp}/{self.max_hp}, {self.get_phase_description()})"

