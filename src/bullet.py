"""
Bullet System
Phase 1D: Bullet Management
"""

from config import BULLET_SPEED, DIRECTIONS, TERRAIN


class Bullet:
   

    def __init__(self, x, y, direction, owner_tank):
       
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
       
        # Move by speed amount * delta time
        self.x += self.dx * self.speed * dt
        self.y += self.dy * self.speed * dt
        
        # Return current tile position
        return (int(self.x), int(self.y))

    def get_tile_position(self):
        
        return (int(self.x), int(self.y))

    def get_precise_position(self):
       
        return (self.x, self.y)

    def destroy(self):
      
        self.alive = False

    def __repr__(self):
        tile_x, tile_y = self.get_tile_position()
        return f"Bullet(at ({tile_x}, {tile_y}), dir={self.direction_name})"


class BulletManager:
   
    def __init__(self):
        
        self.bullets = []

    def spawn_bullet(self, tank):
       
        # Create bullet ahead of tank's position for visibility
        # Spawn 0.5 tiles ahead so it appears in front of the tank
        # Collision detection checks both current and next tile to catch bricks immediately
        spawn_x = tank.x + tank.direction[0] * 0.5
        spawn_y = tank.y + tank.direction[1] * 0.5
        bullet = Bullet(spawn_x, spawn_y, tank.direction, tank)
        self.bullets.append(bullet)
        tank.reset_shot()  # Reset has_bullet flag after creating bullet
        return bullet

    def update_bullets(self, dt):
       
        steps = 2
        sub_dt = dt / steps
        
        for _ in range(steps):
            for bullet in self.bullets[:]:
                if bullet.alive:
                    bullet.update(sub_dt)
                    # Boundary check
                    bx, by = int(bullet.x), int(bullet.y)
                    if bx < 0 or bx >= 26 or by < 0 or by >= 26:
                        bullet.destroy()
            
            # Clean up dead bullets after each sub-step
            self.bullets = [b for b in self.bullets if b.alive]

    def destroy_bullet(self, bullet):
        """Remove a bullet from play."""
        if bullet in self.bullets:
            bullet.destroy()
            self.bullets.remove(bullet)

    def get_active_bullets(self):
        
        return [b for b in self.bullets if b.alive]

    def get_bullet_count(self):
       
        return len(self.get_active_bullets())

    def clear(self):
    
        self.bullets.clear()

    def __repr__(self):
        return f"BulletManager({self.get_bullet_count()} active bullets)"
