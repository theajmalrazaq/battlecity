import time
import random
from collections import deque
from pathfinding import PathfindingFactory
from config import DIRECTIONS


class AIAgent:
    

    def __init__(self, tank, grid, eagle_pos=None):
        
        self.tank = tank
        self.grid = grid
        self.eagle_pos = eagle_pos or (12, 24)  # Default eagle position
        self.last_decision_time = 0.0
        self.decision_interval = 0.1  # Decide every 0.1 seconds

    def decide(self, dt, game_state):
       
        raise NotImplementedError

    def _can_see_eagle(self, x1=None, y1=None):
        """Check if the eagle is in straight line-of-sight from a tile."""
        if x1 is None or y1 is None:
            x1, y1 = self.tank.get_position()

        eagle_x, eagle_y = self.eagle_pos

        if x1 == eagle_x:
            min_y, max_y = min(y1, eagle_y), max(y1, eagle_y)
            for y in range(min_y + 1, max_y):
                if self.grid.is_solid(x1, y):
                    return False
            return True

        if y1 == eagle_y:
            min_x, max_x = min(x1, eagle_x), max(x1, eagle_x)
            for x in range(min_x + 1, max_x):
                if self.grid.is_solid(x, y1):
                    return False
            return True

        return False


class SimpleReflexAgent(AIAgent):
    

    def __init__(self, tank, grid, eagle_pos=None):
        """Initialize simple reflex agent."""
        super().__init__(tank, grid, eagle_pos)
        self.pathfinder = PathfindingFactory.create_pathfinder('BASIC', grid)
        self.current_path = []
        self.last_bfs_time = 0.0
        self.bfs_interval = 5.0  # Re-run BFS every 5 seconds

    def decide(self, dt, game_state):
       
        if not self.tank.alive:
            return
        
        self.last_decision_time += dt
        self.last_bfs_time += dt
        
        # Invalidate path if any tile in current path is no longer passable (wall destroyed / new wall)
        if self.current_path and self._path_blocked():
            self.current_path = []
            self.last_bfs_time = self.bfs_interval  # Force immediate recompute
        
        # Update BFS path periodically or when path is empty
        if self.last_bfs_time >= self.bfs_interval or not self.current_path:
            self.current_path = self.pathfinder.find_path(
                self.tank.get_position(),
                self.eagle_pos
            )
            self.last_bfs_time = 0.0
        
        # Rule 1: Check if player is in line-of-sight
        player = game_state.player
        if player and player.alive:
            if self._can_see_and_shoot_player(player):
                self.tank.shoot()
                return
        
        # Rule 2: Follow BFS path or move randomly
        if self.current_path and len(self.current_path) > 1:
            next_pos = self.current_path[1]  # Next step (0 is current position)
            self._move_toward(next_pos)
            
            # Rule 3: If next tile is brick, shoot it
            next_x, next_y = self.tank.get_forward_tile()
            if self.grid.get_terrain(next_x, next_y) == 1:  # BRICK
                self.tank.shoot()
        else:
            # No path, move randomly
            self._move_random()
        
        # Rule 4: Shoot eagle if adjacent
        tank_x, tank_y = self.tank.get_position()
        eagle_x, eagle_y = self.eagle_pos
        if abs(tank_x - eagle_x) + abs(tank_y - eagle_y) <= 1:
            self.tank.shoot()

    def on_wall_destroyed(self, x, y):
        
        if self.current_path and (x, y) in self.current_path:
            self.current_path = []
            self.last_bfs_time = self.bfs_interval  # Force immediate recompute next tick

    def _can_see_and_shoot_player(self, player):
      
        tank_x, tank_y = self.tank.get_position()
        player_x, player_y = player.get_position()
        
        # Same row (y)
        if tank_y == player_y:
            min_x, max_x = min(tank_x, player_x), max(tank_x, player_x)
            for x in range(min_x + 1, max_x):
                # PDF Page 6: "Use forest tiles to dodge enemy fire"
                if self.grid.is_solid(x, tank_y) or self.grid.get_terrain(x, tank_y) == 4: # 4 = FOREST
                    return False
            return True
        
        # Same column (x)
        if tank_x == player_x:
            min_y, max_y = min(tank_y, player_y), max(tank_y, player_y)
            for y in range(min_y + 1, max_y):
                if self.grid.is_solid(tank_x, y) or self.grid.get_terrain(tank_x, y) == 4: # 4 = FOREST
                    return False
            return True
        
        return False

    def _path_blocked(self):
        """Check if any tile in current path is no longer passable (e.g., wall destroyed/added)."""
        for pos in self.current_path[1:]:  # Skip current position
            if not self.grid.is_passable_by_tank(pos[0], pos[1]):
                return True
        return False

    def _move_toward(self, target):
        """Move tank toward target position."""
        tank_x, tank_y = self.tank.get_position()
        target_x, target_y = target
        
        dx = target_x - tank_x
        dy = target_y - tank_y
        
        if abs(dx) > abs(dy):
            # Move horizontally
            direction = 'RIGHT' if dx > 0 else 'LEFT'
        else:
            # Move vertically
            direction = 'DOWN' if dy > 0 else 'UP'
        
        self.tank.set_direction(direction)

    def _move_random(self):
        """Move in a random direction."""
        directions = ['UP', 'DOWN', 'LEFT', 'RIGHT']
        direction = random.choice(directions)
        self.tank.set_direction(direction)

class GoalBasedAgent(AIAgent):
   

    def __init__(self, tank, grid, eagle_pos=None):
        """Initialize goal-based agent."""
        super().__init__(tank, grid, eagle_pos)
        self.pathfinder = PathfindingFactory.create_pathfinder('FAST', grid)

    def decide(self, dt, game_state):
        
        if not self.tank.alive:
            return
        
        self.last_decision_time += dt
        
        # Get eagle position
        eagle_pos = game_state.grid.eagle_pos if hasattr(game_state.grid, 'eagle_pos') else (12, 24)
        eagle_x, eagle_y = eagle_pos
        tank_x, tank_y = self.tank.get_position()
        
        # Find best neighbor (greedy: lowest h(n) = Manhattan)
        # Fast Tanks ignore detour - they push STRAIGHT toward the eagle
        best_dir = None
        best_h = float('inf')
        
        for d_name, (dx, dy) in DIRECTIONS.items():
            if d_name == 'NONE': continue
            nx, ny = tank_x + dx, tank_y + dy
            
            # Distance to eagle
            h = abs(nx - eagle_x) + abs(ny - eagle_y)
            if h < best_h:
                best_h = h
                best_dir = (d_name, dx, dy)
        
        if best_dir:
            d_name, dx, dy = best_dir
            self.tank.set_direction(d_name)
            
            nx, ny = tank_x + dx, tank_y + dy
            # If next tile is brick, shoot it (never detour - spec Page 7)
            if self.grid.get_terrain(nx, ny) == 1: # BRICK
                if self.tank.ready_to_shoot():
                    self.tank.shoot()
            # If eagle is directly ahead, shoot it
            elif nx == eagle_x and ny == eagle_y:
                if self.tank.ready_to_shoot():
                    self.tank.shoot()
            elif self._can_see_eagle(tank_x, tank_y):
                if self.tank.ready_to_shoot():
                    self.tank.shoot()
            # If path is clear (Empty/Forest), the movement engine in GameState will handle the step
        else:
            # Stuck (no valid neighbors)
            self._move_random()

    def _move_random(self):
        """Move in a random direction."""
        directions = ['UP', 'DOWN', 'LEFT', 'RIGHT']
        direction = random.choice(directions)
        self.tank.set_direction(direction)


class ModelBasedReflexAgent(AIAgent):
   

    def __init__(self, tank, grid, eagle_pos=None):
        """Initialize model-based reflex agent."""
        super().__init__(tank, grid, eagle_pos)
        self.pathfinder = PathfindingFactory.create_pathfinder('ARMOR', grid)
        self.current_path = []
        self.last_a_star_time = 0.0
        self.a_star_interval = 5.0  # Re-run A* every 5 seconds
        
        # State variables
        self.tank.ai_state['hit_count'] = 0
        self.tank.ai_state['retreat_time'] = 0.0
        self.tank.ai_state['retreat_target'] = None

    def decide(self, dt, game_state):
       
        if not self.tank.alive:
            return
        
        self.last_decision_time += dt
        self.last_a_star_time += dt
        
        # Get hit count from state
        hit_count = self.tank.ai_state.get('hit_count', 0)
        
        if hit_count < 3:
            # Rule 1: Normal attack mode (0-2 hits)
            self._attack_mode(dt, game_state)
        else:
            # Rule 2 & 3: Retreat mode (3rd hit)
            self._retreat_mode(dt, game_state)

    def _path_blocked(self):
        """Check if any tile in current path is no longer passable."""
        for pos in self.current_path[1:]:
            if not self.grid.is_passable_by_tank(pos[0], pos[1]):
                # Also allow brick tiles (A* can plan through them by shooting)
                from config import TERRAIN
                terrain = self.grid.get_terrain(pos[0], pos[1])
                if terrain not in [TERRAIN['BRICK']]:  # Only hard-block on Steel/Water
                    return True
        return False

    def _attack_mode(self, dt, game_state):
       
        # Get eagle position from game state
        eagle_pos = game_state.grid.eagle_pos if hasattr(game_state.grid, 'eagle_pos') else (12, 24)
        
        # Invalidate path if a Steel/Water wall has been placed on path (rare) or path is stale
        if self.current_path and self._path_blocked():
            self.current_path = []
            self.last_a_star_time = self.a_star_interval  # Force recompute
        
        # Update A* path periodically
        if self.last_a_star_time >= self.a_star_interval or not self.current_path:
            self.current_path = self.pathfinder.find_path(
                self.tank.get_position(),
                eagle_pos
            )
            self.last_a_star_time = 0.0
        
        # Check if player in line-of-sight
        player = game_state.player
        if player and player.alive:
            if self._can_see_and_shoot_player(player):
                self.tank.shoot()
                return
        
        # Follow A* path
        if self.current_path and len(self.current_path) > 1:
            next_pos = self.current_path[1]
            self._move_toward(next_pos)
            
            # BUG 4 fix: if next tile is brick, SHOOT it (A* planned through it with cost=3)
            # The Armor tank clears its own path by shooting obstacles
            from config import TERRAIN as T
            next_x, next_y = self.tank.get_forward_tile()
            if self.grid.get_terrain(next_x, next_y) == T['BRICK']:
                if self.tank.ready_to_shoot():
                    self.tank.shoot()
        else:
            # No path, move randomly
            self._move_random()
        
        # Shoot eagle if in straight line-of-sight or adjacent
        tank_x, tank_y = self.tank.get_position()
        eagle_x, eagle_y = eagle_pos
        if abs(tank_x - eagle_x) + abs(tank_y - eagle_y) <= 1 or self._can_see_eagle(tank_x, tank_y):
            if self.tank.ready_to_shoot():
                self.tank.shoot()

    def on_wall_destroyed(self, x, y):
       
        if self.current_path and (x, y) in self.current_path:
            self.current_path = []
            self.last_a_star_time = self.a_star_interval  # Force immediate recompute next tick

    def _retreat_mode(self, dt, game_state):
       
        retreat_time = self.tank.ai_state.get('retreat_time', 0.0)
        retreat_target = self.tank.ai_state.get('retreat_target', None)
        
        # If already retreating, just move toward steel wall
        if retreat_target is None:
            # Find nearest steel wall
            retreat_target = self._find_nearest_steel_wall(game_state.grid)
            self.tank.ai_state['retreat_target'] = retreat_target
        
        if retreat_target:
            self._move_toward(retreat_target)
        else:
            # No steel wall found, move randomly
            self._move_random()
        
        # Update retreat timer
        self.tank.ai_state['retreat_time'] += dt
        
        # After 2 seconds, recover
        if self.tank.ai_state['retreat_time'] >= 2.0:
            self.tank.ai_state['retreat_time'] = 0.0
            self.tank.ai_state['retreat_target'] = None
            self.tank.ai_state['hit_count'] = 0  # Reset to 0 (not 2) to exit retreat mode

    def _find_nearest_steel_wall(self, grid):
       
        from collections import deque
        
        tank_x, tank_y = self.tank.get_position()
        visited = set()
        queue = deque([(tank_x, tank_y)])
        visited.add((tank_x, tank_y))
        
        while queue:
            x, y = queue.popleft()
            
            # Check neighbors for steel
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                if (nx, ny) in visited:
                    continue
                if not grid.is_valid(nx, ny):
                    continue
                
                visited.add((nx, ny))
                
                # Found steel?
                if grid.get_terrain(nx, ny) == 2:  # STEEL
                    # Return adjacent empty tile near steel
                    for dx2, dy2 in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        sx, sy = nx + dx2, ny + dy2
                        if grid.is_valid(sx, sy) and grid.is_passable_by_tank(sx, sy):
                            return (sx, sy)
                    return (nx, ny)
                
                # Add neighbors to queue if passable (so we can reach the steel)
                if grid.is_passable_by_tank(nx, ny):
                    queue.append((nx, ny))
        
        return None

    def _can_see_and_shoot_player(self, player):
        """Check if player is in line-of-sight."""
        tank_x, tank_y = self.tank.get_position()
        player_x, player_y = player.get_position()
        
        if tank_y == player_y:
            min_x, max_x = min(tank_x, player_x), max(tank_x, player_x)
            for x in range(min_x + 1, max_x):
                if self.grid.is_solid(x, tank_y):
                    return False
            return True
        
        if tank_x == player_x:
            min_y, max_y = min(tank_y, player_y), max(tank_y, player_y)
            for y in range(min_y + 1, max_y):
                if self.grid.is_solid(tank_x, y):
                    return False
            return True
        
        return False

    def _move_toward(self, target):
        """Move toward target."""
        tank_x, tank_y = self.tank.get_position()
        target_x, target_y = target
        
        dx = target_x - tank_x
        dy = target_y - tank_y
        
        if abs(dx) > abs(dy):
            direction = 'RIGHT' if dx > 0 else 'LEFT'
        else:
            direction = 'DOWN' if dy > 0 else 'UP'
        
        self.tank.set_direction(direction)

    def _move_random(self):
        """Move randomly."""
        directions = ['UP', 'DOWN', 'LEFT', 'RIGHT']
        direction = random.choice(directions)
        self.tank.set_direction(direction)


class UtilityAgent(AIAgent):
    
    def __init__(self, tank, grid, eagle_pos=None):
        super().__init__(tank, grid, eagle_pos)
        self.weights = {
            'eagle': 4.0,       # Balanced priority for eagle
            'player': 6.0,      # HIGH priority - engage player aggressively
            'combat': 10.0,     # Very high combat bonus - power tanks hunt
            'forest': 0.5,      # Low stealth value - power tanks are aggressive
            'eagle_los': 3.0,   # Moderate bonus for eagle LOS
            'player_los': 8.0   # HUGE bonus for player line-of-sight (hunting)
        }
        # Recent target tiles to avoid cyclic back-and-forth
        self.recent_positions = deque(maxlen=6)
        self.last_direction = 'NONE'  # Track last chosen direction to reduce oscillation
        self.target_player = None  # Track if actively hunting a player

    def decide(self, dt, game_state):
        if not self.tank.alive: return
        self.last_decision_time += dt
        
        # Only make new decisions at intervals (prevents jittering)
        if self.last_decision_time < self.decision_interval:
            # But always shoot aggressively while moving toward target
            if self.target_player and game_state.player and game_state.player.alive:
                if self._can_see(self.tank.x, self.tank.y, game_state.player.x, game_state.player.y):
                    if self.tank.ready_to_shoot():
                        self.tank.shoot()
            return
        
        self.last_decision_time = 0.0
        
        best_action = 'NONE'
        max_utility = -float('inf')
        
        tank_x, tank_y = self.tank.get_position()
        player = game_state.player
        
        # Track if we're hunting the player
        self.target_player = player and player.alive

        # Evaluate directions - prefer to continue in current direction if utility is close
        current_utility = -float('inf')
        current_direction = self.tank.direction_name
        
        for d_name, (dx, dy) in DIRECTIONS.items():
            if d_name == 'NONE': continue
            nx, ny = tank_x + dx, tank_y + dy
            # Use collision detector to ensure move is allowed (handles moving tanks too)
            try:
                can_move = game_state.collision_detector.can_tank_move_to(self.tank, nx, ny)
            except Exception:
                # Fallback to grid/passable check + check for occupying tanks
                can_move = self.grid.is_valid(nx, ny) and self.grid.is_passable_by_tank(nx, ny)
                # Also check for other tanks blocking
                if can_move:
                    for other_tank in game_state.tanks:
                        if other_tank != self.tank and other_tank.alive:
                            if int(other_tank.x) == int(nx) and int(other_tank.y) == int(ny):
                                can_move = False
                                break
            if not can_move:
                continue
            
            # 1. Eagle Utility (Inverse Manhattan)
            eagle_dist = abs(nx - self.eagle_pos[0]) + abs(ny - self.eagle_pos[1])
            u_eagle = (1.0 / (eagle_dist + 1)) * self.weights['eagle']
            
            # 2. Player Engagement Utility (HIGH priority for power tanks)
            u_player = 0
            u_player_los = 0
            if player and player.alive:
                p_dist = abs(nx - player.x) + abs(ny - player.y)
                u_player = (1.0 / (p_dist + 1)) * self.weights['player']
                
                # HUGE bonus for line-of-sight (power tanks hunt aggressively)
                if self._can_see(nx, ny, player.x, player.y):
                    u_player_los = self.weights['player_los']  # 8.0
                    u_player += self.weights['combat']  # Additional combat bonus
            
            # 3. Stealth Utility (Forest) - low value for aggressive power tank
            u_stealth = 0
            if self.grid.get_terrain(nx, ny) == 4: # FOREST
                u_stealth = self.weights['forest']
            
            total_utility = u_eagle + u_player + u_player_los + u_stealth

            # Moderate bonus if the eagle would be in straight LOS from this candidate tile
            try:
                if self._can_see_eagle(nx, ny):
                    total_utility += self.weights.get('eagle_los', 0)
            except Exception:
                pass
            
            # Track current direction's utility (without randomness for comparison)
            if d_name == current_direction:
                current_utility = total_utility
            
            # Reduce randomness for power tanks (more predictable/focused)
            if d_name != current_direction:
                total_utility += random.uniform(0, 0.02)
            
            if total_utility > max_utility:
                max_utility = total_utility
                best_action = d_name

        # Lower hysteresis threshold (0.2 instead of 0.3) - power tanks are more reactive
        # Only keep direction if it's nearly as good as the best option
        if best_action != current_direction and current_utility >= 0:
            if (max_utility - current_utility) < 0.2:
                best_action = current_direction

        # Set new direction
        self.tank.set_direction(best_action)
        if best_action and best_action != 'NONE':
            bdx, bdy = DIRECTIONS.get(best_action, (0, 0))
            expect_pos = (tank_x + bdx, tank_y + bdy)
            self.recent_positions.append(expect_pos)
        
        # AGGRESSIVE SHOOTING: Check all shooting opportunities
        tank_x, tank_y = self.tank.get_position()
        
        # Priority 1: Player is in line-of-sight (ALWAYS SHOOT)
        if player and player.alive:
            if self._can_see(self.tank.x, self.tank.y, player.x, player.y):
                if self.tank.ready_to_shoot():
                    self.tank.shoot()
                    return
        
        # Priority 2: Eagle is nearby or in LOS
        eagle_x, eagle_y = self.eagle_pos
        if (abs(tank_x - eagle_x) + abs(tank_y - eagle_y) <= 1) or self._can_see_eagle(tank_x, tank_y):
            if self.tank.ready_to_shoot():
                self.tank.shoot()

    def _can_see(self, x1, y1, x2, y2):
        if x1 == x2:
            for y in range(int(min(y1, y2)) + 1, int(max(y1, y2))):
                # FOREST blocks utility vision
                if self.grid.is_solid(x1, y) or self.grid.get_terrain(x1, y) == 4: return False
            return True
        if y1 == y2:
            for x in range(int(min(x1, x2)) + 1, int(max(x1, x2))):
                if self.grid.is_solid(x, y1) or self.grid.get_terrain(x, y1) == 4: return False
            return True
        return False


class AIAgentFactory:
   

    @staticmethod
    def create_agent(tank, grid, tank_type=None, eagle_pos=None):
       
        if tank_type is None:
            tank_type = tank.tank_type.value
        
        eagle_pos = eagle_pos or (12, 24)
        
        if tank_type == 'BASIC':
            return SimpleReflexAgent(tank, grid, eagle_pos)
        elif tank_type == 'FAST':
            return GoalBasedAgent(tank, grid, eagle_pos)
        elif tank_type == 'ARMOR':
            return ModelBasedReflexAgent(tank, grid, eagle_pos)
        elif tank_type == 'POWER':
            return UtilityAgent(tank, grid, eagle_pos)
        elif tank_type == 'BOSS':
            from .boss import BossAgent
            return BossAgent(tank, grid, eagle_pos)
        else:
            return SimpleReflexAgent(tank, grid, eagle_pos)  # Default
