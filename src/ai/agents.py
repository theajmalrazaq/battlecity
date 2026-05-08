"""
AI Agents - Tank Decision Logic
Phase 2B: Agents & Behaviors - Module B
"""

import time
import random
from pathfinding import PathfindingFactory


class AIAgent:
    """Base class for tank AI agents."""

    def __init__(self, tank, grid, eagle_pos=None):
        """
        Initialize AI agent.
        
        Args:
            tank: Tank object to control
            grid: Grid object for pathfinding
            eagle_pos: Position of eagle for goal-seeking
        """
        self.tank = tank
        self.grid = grid
        self.eagle_pos = eagle_pos or (12, 24)  # Default eagle position
        self.last_decision_time = 0.0
        self.decision_interval = 0.1  # Decide every 0.1 seconds

    def decide(self, dt, game_state):
        """
        Make a decision (move direction and shoot).
        Must be implemented by subclasses.
        
        Args:
            dt: Delta time since last update
            game_state: GameState object (for other agents' positions, etc.)
        """
        raise NotImplementedError


class SimpleReflexAgent(AIAgent):
    """
    Simple Reflex Agent (Basic Tank).
    
    Agent Model: Simple Reflex (no memory, no planning)
    Search Algorithm: BFS
    Behavior: Move toward eagle via BFS, shoot if player in line-of-sight
    
    Rules:
    1. IF player in same row/column AND no wall between THEN shoot
    2. IF path to eagle via BFS exists THEN follow next step ELSE random direction
    3. IF next tile is brick THEN shoot to destroy it THEN move
    """

    def __init__(self, tank, grid, eagle_pos=None):
        """Initialize simple reflex agent."""
        super().__init__(tank, grid, eagle_pos)
        self.pathfinder = PathfindingFactory.create_pathfinder('BASIC', grid)
        self.current_path = []
        self.last_bfs_time = 0.0
        self.bfs_interval = 5.0  # Re-run BFS every 5 seconds

    def decide(self, dt, game_state):
        """
        Make decision using BFS pathfinding and simple rules.
        
        Args:
            dt: Delta time
            game_state: GameState object
        """
        if not self.tank.alive:
            return
        
        self.last_decision_time += dt
        self.last_bfs_time += dt
        
        # Update BFS path periodically
        if self.last_bfs_time >= self.bfs_interval or not self.current_path:
            self.current_path = self.pathfinder.find_path(
                self.tank.get_position(),
                self.eagle_pos  # Use self.eagle_pos instead of game_state.grid.eagle_pos
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

    def _can_see_and_shoot_player(self, player):
        """
        Check if player is in same row/column with no wall between.
        
        Returns:
            True if player is in line-of-sight
        """
        tank_x, tank_y = self.tank.get_position()
        player_x, player_y = player.get_position()
        
        # Same row (y)
        if tank_y == player_y:
            min_x, max_x = min(tank_x, player_x), max(tank_x, player_x)
            for x in range(min_x + 1, max_x):
                if self.grid.is_solid(x, tank_y):
                    return False
            return True
        
        # Same column (x)
        if tank_x == player_x:
            min_y, max_y = min(tank_y, player_y), max(tank_y, player_y)
            for y in range(min_y + 1, max_y):
                if self.grid.is_solid(tank_x, y):
                    return False
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
    """
    Goal-Based Agent (Fast Tank).
    
    Agent Model: Goal-Based (explicit goal, ignores other considerations)
    Search Algorithm: Greedy Best-First
    Behavior: Rushes toward eagle ignoring player, may get stuck
    
    Rules:
    1. Goal: Destroy the eagle (ignore player completely)
    2. Always move toward tile minimizing Manhattan distance to eagle
    3. If next tile is brick, shoot to clear path (never detour)
    
    Note: Greedy getting stuck in local minima is INTENTIONAL (teaches why greedy fails).
    """

    def __init__(self, tank, grid, eagle_pos=None):
        """Initialize goal-based agent."""
        super().__init__(tank, grid, eagle_pos)
        self.pathfinder = PathfindingFactory.create_pathfinder('FAST', grid)

    def decide(self, dt, game_state):
        """
        Make decision using Greedy Best-First (heuristic only).
        
        Args:
            dt: Delta time
            game_state: GameState object
        """
        if not self.tank.alive:
            return
        
        self.last_decision_time += dt
        
        # Get eagle position
        eagle_pos = game_state.grid.eagle_pos if hasattr(game_state.grid, 'eagle_pos') else (12, 24)
        eagle_x, eagle_y = eagle_pos
        tank_x, tank_y = self.tank.get_position()
        
        # Find best neighbor (greedy: lowest h(n))
        best_neighbor = None
        best_h = float('inf')
        
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = tank_x + dx, tank_y + dy
            
            # Check if passable
            if not game_state.collision_detector.can_tank_move_to(self.tank, nx, ny):
                continue
            
            # Calculate h(n) = Manhattan distance
            h = abs(nx - eagle_x) + abs(ny - eagle_y)
            
            if h < best_h:
                best_h = h
                best_neighbor = (nx, ny, dx, dy)
        
        if best_neighbor:
            nx, ny, dx, dy = best_neighbor
            
            # Set direction
            if dx > 0:
                self.tank.set_direction('RIGHT')
            elif dx < 0:
                self.tank.set_direction('LEFT')
            elif dy > 0:
                self.tank.set_direction('DOWN')
            elif dy < 0:
                self.tank.set_direction('UP')
            
            # Shoot if next tile is brick (never detour)
            next_x, next_y = self.tank.get_forward_tile()
            if game_state.grid.get_terrain(next_x, next_y) == 1:  # BRICK
                self.tank.shoot()
        else:
            # Stuck (no valid neighbors)
            self._move_random()

    def _move_random(self):
        """Move in a random direction."""
        directions = ['UP', 'DOWN', 'LEFT', 'RIGHT']
        direction = random.choice(directions)
        self.tank.set_direction(direction)


class ModelBasedReflexAgent(AIAgent):
    """
    Model-Based Reflex Agent (Armor Tank).
    
    Agent Model: Model-Based Reflex (maintains internal state)
    Search Algorithm: A* Search
    Behavior: Move toward eagle, retreat on 3rd hit, recover
    
    State Variable: hit_count (0-3) - tracks damage
    
    Rules:
    1. (0-2 hits): Navigate to eagle via A*, shoot if player in LOS
    2. (3rd hit): RETREAT - find nearest steel wall and hide
    3. (after retreat): Wait 2 seconds, re-compute A* path
    
    Key: A* recognizes shooting through brick is cheaper than detouring.
    """

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
        """
        Make decision based on hit count (state).
        
        Args:
            dt: Delta time
            game_state: GameState object
        """
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

    def _attack_mode(self, dt, game_state):
        """
        Attack mode: Move toward eagle via A*, shoot if possible.
        """
        # Get eagle position from game state
        eagle_pos = game_state.grid.eagle_pos if hasattr(game_state.grid, 'eagle_pos') else (12, 24)
        
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
        else:
            # No path, move randomly
            self._move_random()

    def _retreat_mode(self, dt, game_state):
        """
        Retreat mode: Find nearest steel wall and hide.
        """
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
            self.tank.ai_state['hit_count'] = 2  # Back to normal (not 3)

    def _find_nearest_steel_wall(self, grid):
        """
        Find the nearest steel wall using BFS.
        
        Returns:
            Position (x, y) of nearest steel wall, or None
        """
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
                
                # Add neighbors to queue
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


class AIAgentFactory:
    """Factory to create appropriate agent for a tank type."""

    @staticmethod
    def create_agent(tank, grid, tank_type=None, eagle_pos=None):
        """
        Create AI agent for tank.
        
        Args:
            tank: Tank object
            grid: Grid object
            tank_type: 'BASIC', 'FAST', 'ARMOR', 'BOSS' (defaults to tank.tank_type)
            eagle_pos: Position of eagle (default 12, 24)
        
        Returns:
            Appropriate AIAgent subclass instance
        """
        if tank_type is None:
            tank_type = tank.tank_type.value
        
        eagle_pos = eagle_pos or (12, 24)
        
        if tank_type == 'BASIC':
            return SimpleReflexAgent(tank, grid, eagle_pos)
        elif tank_type == 'FAST':
            return GoalBasedAgent(tank, grid, eagle_pos)
        elif tank_type == 'ARMOR':
            return ModelBasedReflexAgent(tank, grid, eagle_pos)
        elif tank_type == 'BOSS':
            from .boss import BossAgent
            return BossAgent(tank, grid, eagle_pos)
        else:
            return SimpleReflexAgent(tank, grid, eagle_pos)  # Default
