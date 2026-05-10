"""
Collision Detection System
Phase 1C: Movement & Collision
"""

from config import TERRAIN


class CollisionDetector:
  

    def __init__(self, grid, tanks, bullets, eagle_pos):
        
        self.grid = grid
        self.tanks = tanks
        self.bullets = bullets
        self.eagle_pos = eagle_pos

    def can_tank_move_to(self, tank, target_x, target_y):
      
        # Check terrain
        if not self.grid.is_passable_by_tank(target_x, target_y):
            return False
        
        # Check for other tanks currently occupying the target tile
        for other_tank in self.tanks:
            if other_tank is tank:
                continue  # Skip self
            if other_tank.alive and other_tank.x == target_x and other_tank.y == target_y:
                return False  # Tile occupied by another tank
        
        return True

    def check_bullet_vs_terrain(self, bullet):
      
        bx, by = bullet.get_tile_position()
        
        # Check bounds
        if not self.grid.is_valid(bx, by):
            return 'bounds'
        
        terrain = self.grid.get_terrain(bx, by)
        
        if terrain == TERRAIN['BRICK']:
            return 'brick'
        elif terrain == TERRAIN['STEEL']:
            return 'steel'
        elif terrain == TERRAIN['WATER']:
            return None  # Bullets pass OVER water (tanks blocked, bullets fly through)
        elif terrain == TERRAIN['EAGLE']:
            return 'eagle'
        
        return None

    def check_bullet_vs_tank(self, bullet):
       
        bx, by = bullet.get_tile_position()
        
        for tank in self.tanks:
            if not tank.alive:
                continue
            if tank is bullet.owner:
                continue  # Bullet doesn't hit its owner
            if tank.x == bx and tank.y == by:
                return tank
        
        return None

    def check_bullet_vs_bullet(self, bullet1, bullet2):
      
        b1x, b1y = bullet1.get_tile_position()
        b2x, b2y = bullet2.get_tile_position()
        
        return b1x == b2x and b1y == b2y

    def check_all_bullet_collisions(self):
      
        events = []
        active_bullets = self.bullets.get_active_bullets()
        
        for bullet in active_bullets[:]:
            if not bullet.alive:
                continue
            
            # Check vs terrain
            terrain_hit = self.check_bullet_vs_terrain(bullet)
            if terrain_hit == 'brick':
                events.append({
                    'type': 'terrain',
                    'bullet': bullet,
                    'target': 'brick',
                    'position': bullet.get_tile_position()
                })
                continue
            elif terrain_hit in ['steel', 'water', 'bounds']:
                events.append({
                    'type': 'terrain',
                    'bullet': bullet,
                    'target': terrain_hit,
                })
                continue
            elif terrain_hit == 'eagle':
                events.append({
                    'type': 'eagle',
                    'bullet': bullet,
                    'owner': bullet.owner
                })
                continue
            
            # Check vs tank
            tank_hit = self.check_bullet_vs_tank(bullet)
            if tank_hit:
                events.append({
                    'type': 'tank',
                    'bullet': bullet,
                    'target': tank_hit
                })
                continue
            
            # Check vs other bullets
            for other_bullet in active_bullets:
                if other_bullet is bullet or not other_bullet.alive:
                    continue
                if self.check_bullet_vs_bullet(bullet, other_bullet):
                    events.append({
                        'type': 'bullet',
                        'bullet1': bullet,
                        'bullet2': other_bullet
                    })
                    break  # One collision per bullet per frame
        
        return events

    def resolve_collision(self, event):
       
        result = {}
        
        if event['type'] == 'terrain':
            bullet = event['bullet']
            target = event['target']
            
            if target == 'brick':
                # Destroy brick AND bullet (original Battle City rules)
                bx, by = event['position']
                self.grid.destroy_brick(bx, by)
                self.bullets.destroy_bullet(bullet)
                result['destroyed_brick'] = True
                result['destroyed_bullet'] = True
            else:
                # Steel, water, bounds - destroy bullet
                self.bullets.destroy_bullet(bullet)
                result['destroyed_bullet'] = True
        
        elif event['type'] == 'tank':
            bullet = event['bullet']
            tank_hit = event['target']
            
            # Bullet destroys tank (if it has 1 HP)
            tank_destroyed = tank_hit.take_damage(1)
            self.bullets.destroy_bullet(bullet)
            
            result['destroyed_bullet'] = True
            result['tank_damaged'] = True
            result['damaged_tank'] = tank_hit
            result['tank_destroyed'] = tank_destroyed
        
        elif event['type'] == 'bullet':
            bullet1 = event['bullet1']
            bullet2 = event['bullet2']
            
            # Both bullets destroyed
            self.bullets.destroy_bullet(bullet1)
            self.bullets.destroy_bullet(bullet2)
            
            result['destroyed_bullet1'] = True
            result['destroyed_bullet2'] = True
        
        elif event['type'] == 'eagle':
            bullet = event['bullet']
            owner = event['owner']
            
            # Eagle destroyed - game over
            self.bullets.destroy_bullet(bullet)
            result['destroyed_bullet'] = True
            result['eagle_destroyed'] = True
            result['destroyedby'] = owner
        
        return result
