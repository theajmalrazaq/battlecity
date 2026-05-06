"""
Pathfinding Algorithms - BFS, Greedy Best-First, A*
Phase 2B: Search Algorithms - Module B
"""

from collections import deque
import heapq
from config import A_STAR_COSTS, TERRAIN


class Pathfinder:
    """
    Base class for pathfinding algorithms.
    Subclasses implement BFS, Greedy, and A*.
    """

    def __init__(self, grid):
        """
        Initialize pathfinder.
        
        Args:
            grid: Grid object with terrain information
        """
        self.grid = grid

    def find_path(self, start, goal):
        """
        Find path from start to goal.
        Must be implemented by subclasses.
        
        Args:
            start: (x, y) tuple
            goal: (x, y) tuple
        
        Returns:
            List of (x, y) positions from start to goal, or [] if no path
        """
        raise NotImplementedError


class BFSPathfinder(Pathfinder):
    """
    Breadth-First Search Pathfinder (Basic Tank).
    
    Properties:
    - Finds shortest path by number of hops
    - Treats all passable tiles as cost 1
    - Ignores brick walls (doesn't shoot through them)
    - Optimal for unweighted grids
    """

    def find_path(self, start, goal):
        """
        BFS: Find shortest path (by hops).
        
        Args:
            start: (x, y)
            goal: (x, y)
        
        Returns:
            Path as list of (x, y), or [] if no path
        """
        if not self.grid.is_passable_by_tank(start[0], start[1]):
            return []
        
        visited = set([start])
        queue = deque([(start, [start])])
        
        while queue:
            (x, y), path = queue.popleft()
            
            if (x, y) == goal:
                return path
            
            # Explore 4 neighbors
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                if (nx, ny) in visited:
                    continue
                
                # Can only pass through empty and forest (not brick)
                if not self.grid.is_passable_by_tank(nx, ny):
                    continue
                
                visited.add((nx, ny))
                queue.append(((nx, ny), path + [(nx, ny)]))
        
        return []  # No path found


class GreedyBestFirstPathfinder(Pathfinder):
    """
    Greedy Best-First Search Pathfinder (Fast Tank).
    
    Properties:
    - Uses only heuristic (Manhattan distance)
    - No cost awareness (ignores A* costs)
    - Very fast but NOT optimal
    - Can get stuck in local minima ⭐ (INTENTIONAL for teaching)
    
    This demonstrates why greedy is not optimal.
    """

    def __init__(self, grid):
        """Initialize greedy pathfinder."""
        super().__init__(grid)
        self.heuristic = self._manhattan_distance

    def _manhattan_distance(self, pos, goal):
        """
        Manhattan distance heuristic.
        
        Args:
            pos: (x, y)
            goal: (x, y)
        
        Returns:
            Manhattan distance (|dx| + |dy|)
        """
        return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])

    def find_path(self, start, goal):
        """
        Greedy Best-First: Use only heuristic to guide search.
        
        Args:
            start: (x, y)
            goal: (x, y)
        
        Returns:
            Path as list of (x, y), or [] if no path
        """
        if not self.grid.is_passable_by_tank(start[0], start[1]):
            return []
        
        # Priority queue: (h(n), counter, pos, path)
        # Counter for tie-breaking to maintain FIFO order
        counter = 0
        pq = [(self.heuristic(start, goal), counter, start, [start])]
        visited = set()
        
        while pq:
            _, _, (x, y), path = heapq.heappop(pq)
            
            if (x, y) in visited:
                continue
            visited.add((x, y))
            
            if (x, y) == goal:
                return path
            
            # Explore 4 neighbors
            neighbors = []
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                if (nx, ny) in visited:
                    continue
                
                # Can only pass through empty and forest
                if not self.grid.is_passable_by_tank(nx, ny):
                    continue
                
                h = self.heuristic((nx, ny), goal)
                neighbors.append((h, (nx, ny), path + [(nx, ny)]))
            
            # Add neighbors sorted by heuristic (greedy: prefer best heuristic first)
            for h, pos, new_path in sorted(neighbors):
                counter += 1
                heapq.heappush(pq, (h, counter, pos, new_path))
        
        return []  # No path found


class AStarPathfinder(Pathfinder):
    """
    A* Search Pathfinder (Armor Tank).
    
    Properties:
    - Optimal: f(n) = g(n) + h(n)
    - g(n) = cost so far (movement cost)
    - h(n) = heuristic (Manhattan distance)
    - Cost-aware: recognizes shooting through brick is cheaper than detouring
    
    Cost Matrix (from config):
    - Empty/Forest: 1 (normal movement)
    - Brick: 3 (shoot + wait penalty)
    - Steel/Water: infinity (blocked)
    
    This is the "smart" pathfinder used by Armor Tanks.
    """

    def __init__(self, grid):
        """Initialize A* pathfinder."""
        super().__init__(grid)

    def _get_tile_cost(self, x, y):
        """
        Get movement cost for a tile.
        
        Args:
            x, y: Tile position
        
        Returns:
            Cost (1, 3, or infinity)
        """
        if not self.grid.is_valid(x, y):
            return float('inf')
        
        terrain = self.grid.get_terrain(x, y)
        
        # Use config costs
        if terrain == TERRAIN['EMPTY']:
            return A_STAR_COSTS['EMPTY']
        elif terrain == TERRAIN['FOREST']:
            return A_STAR_COSTS['FOREST']
        elif terrain == TERRAIN['BRICK']:
            return A_STAR_COSTS['BRICK']
        elif terrain == TERRAIN['STEEL']:
            return A_STAR_COSTS['STEEL']
        elif terrain == TERRAIN['WATER']:
            return A_STAR_COSTS['WATER']
        
        return float('inf')

    def _manhattan_distance(self, pos, goal):
        """Manhattan distance heuristic."""
        return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])

    def find_path(self, start, goal):
        """
        A*: Find optimal path using g(n) + h(n).
        
        Args:
            start: (x, y)
            goal: (x, y)
        
        Returns:
            Path as list of (x, y), or [] if no path
        """
        if not self.grid.is_valid(start[0], start[1]):
            return []
        
        # Priority queue: (f, counter, pos, path, g_cost)
        counter = 0
        g_start = 0
        h_start = self._manhattan_distance(start, goal)
        
        pq = [(g_start + h_start, counter, start, [start], g_start)]
        visited = {}  # pos -> best g_cost
        
        while pq:
            f, _, (x, y), path, g_cost = heapq.heappop(pq)
            
            # Skip if we've already visited this with better cost
            if (x, y) in visited and visited[(x, y)] <= g_cost:
                continue
            visited[(x, y)] = g_cost
            
            if (x, y) == goal:
                return path
            
            # Explore 4 neighbors
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                if not self.grid.is_valid(nx, ny):
                    continue
                
                # Get tile cost
                move_cost = self._get_tile_cost(nx, ny)
                
                # Skip blocked tiles (cost infinity)
                if move_cost == float('inf'):
                    continue
                
                # Calculate new g cost
                new_g = g_cost + move_cost
                
                # Skip if we've visited this with better cost
                if (nx, ny) in visited and visited[(nx, ny)] <= new_g:
                    continue
                
                # Calculate f = g + h
                h = self._manhattan_distance((nx, ny), goal)
                f = new_g + h
                
                # Add to priority queue
                counter += 1
                heapq.heappush(pq, (f, counter, (nx, ny), path + [(nx, ny)], new_g))
        
        return []  # No path found


class PathfindingFactory:
    """Factory to create appropriate pathfinder for a tank type."""

    @staticmethod
    def create_pathfinder(tank_type, grid):
        """
        Create pathfinder for tank type.
        
        Args:
            tank_type: 'BASIC', 'FAST', or 'ARMOR'
            grid: Grid object
        
        Returns:
            Appropriate Pathfinder subclass instance
        """
        if tank_type == 'BASIC':
            return BFSPathfinder(grid)
        elif tank_type == 'FAST':
            return GreedyBestFirstPathfinder(grid)
        elif tank_type == 'ARMOR':
            return AStarPathfinder(grid)
        else:
            return BFSPathfinder(grid)  # Default
