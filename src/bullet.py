"""
Bullet System
Phase 1D: Bullet Management
"""

from config import BULLET_SPEED, DIRECTIONS, TERRAIN


class Bullet:
    """
    Represents a single bullet in flight.
    
    Properties:
    - Position (x, y): Grid coordinates (floats for sub-tile precision during travel)
    - Direction: Cardinal direction (UP, DOWN, LEFT, RIGHT)
    - Owner: Reference to the tank that fired it
    - Speed: 2x tank movement speed
    - Status: Active vs destroyed
    """

    def __init__(self, x, y, direction, owner_tank):
        """
        Initialize a bullet.
        
        Args:
            x, y: Starting position (float coordinates for sub-tile movement)
            direction: Direction tuple (dx, dy) or direction name
            owner_tank: Reference to Tank that fired this bullet
        """
        self.x = float(x)
        self.y = float(y)
        
        # Direction
        if isinstance(direction, str):
            self.direction = DIRECTIONS[direction]
            self.direction_name = direction
        else:
            self.direction = direction
            # Find direction name
            for name, dir_tuple in DIRECTIONS.items():
                if dir_tuple == direction:
                    self.direction_name = name
                    break
        
        self.dx, self.dy = self.direction
        
        # Properties
        self.speed = BULLET_SPEED  # Tiles per tick (2.0)
        self.owner = owner_tank
        self.alive = True

    def update(self, dt):
        """
        Move bullet one step forward.
        Bullets travel continuously (not tile-by-tile like tanks).
        
        Args:
            dt: Delta time in seconds
        
        Returns:
            Current position as (tile_x, tile_y) integers
        """
        # Move by speed amount * delta time
        self.x += self.dx * self.speed * dt
        self.y += self.dy * self.speed * dt
        
        # Return current tile position
        return (int(self.x), int(self.y))

    def get_tile_position(self):
        """Get current bullet position as integer tile coordinates."""
        return (int(self.x), int(self.y))

    def get_precise_position(self):
        """Get bullet position with sub-tile precision."""
        return (self.x, self.y)

    def destroy(self):
        """Mark bullet as destroyed."""
        self.alive = False

    def __repr__(self):
        tile_x, tile_y = self.get_tile_position()
        return f"Bullet(at ({tile_x}, {tile_y}), dir={self.direction_name})"


class BulletManager:
    """
    Manages all active bullets in the game.
    Handles bullet updates, collisions, and cleanup.
    """

    def __init__(self):
        """Initialize empty bullet list."""
        self.bullets = []

    def spawn_bullet(self, tank):
        """
        Create and register a new bullet from a tank.
        
        Args:
            tank: Tank object that is firing
        
        Returns:
            Bullet object, or None if tank can't shoot
        """
        # Create bullet slightly ahead of tank's position for better visibility
        # Note: tank.shoot() already called in update_player_input(),
        # has_bullet flag signals that a bullet should be spawned this tick
        spawn_x = tank.x + tank.direction[0] * 0.5
        spawn_y = tank.y + tank.direction[1] * 0.5
        bullet = Bullet(spawn_x, spawn_y, tank.direction, tank)
        self.bullets.append(bullet)
        tank.reset_shot()  # Reset has_bullet flag after creating bullet
        return bullet

    def update_bullets(self, dt):
        """
        Update all active bullets and remove destroyed ones.
        
        Args:
            dt: Delta time in seconds
        """
        for bullet in self.bullets[:]:  # Iterate over copy
            if bullet.alive:
                bullet.update(dt)
            else:
                self.bullets.remove(bullet)

    def destroy_bullet(self, bullet):
        """Remove a bullet from play."""
        if bullet in self.bullets:
            bullet.destroy()
            self.bullets.remove(bullet)

    def get_active_bullets(self):
        """Return list of all active bullets."""
        return [b for b in self.bullets if b.alive]

    def get_bullet_count(self):
        """Return number of active bullets."""
        return len(self.get_active_bullets())

    def clear(self):
        """Remove all bullets."""
        self.bullets.clear()

    def __repr__(self):
        return f"BulletManager({self.get_bullet_count()} active bullets)"
