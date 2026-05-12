
from collections import deque
import heapq
from config import A_STAR_COSTS, TERRAIN, GRID_WIDTH, GRID_HEIGHT


class Pathfinder:
    

    def __init__(self, grid):
       
        self.grid = grid

    def find_path(self, start, goal):
       
        raise NotImplementedError


class BFSPathfinder(Pathfinder):
   

    def find_path(self, start, goal):
       
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
                
                # Always allow reaching the goal tile (eagle is impassable but IS the target)
                if (nx, ny) == goal:
                    visited.add((nx, ny))
                    queue.append(((nx, ny), path + [(nx, ny)]))
                    continue
                
                # Can only pass through empty and forest (not brick)
                if not self.grid.is_passable_by_tank(nx, ny):
                    continue
                
                visited.add((nx, ny))
                queue.append(((nx, ny), path + [(nx, ny)]))
        
        return []  # No path found


class GreedyBestFirstPathfinder(Pathfinder):
   

    def __init__(self, grid):
        
        super().__init__(grid)
        self.heuristic = self._manhattan_distance

    def _manhattan_distance(self, pos, goal):
       
        return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])

    def find_path(self, start, goal):
       
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
                
                # Always allow reaching the goal tile
                if (nx, ny) == goal:
                    h = 0  # At goal, h = 0
                    neighbors.append((h, (nx, ny), path + [(nx, ny)]))
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
        elif terrain == TERRAIN['EAGLE']:
            return A_STAR_COSTS['EMPTY']  # BUG 5 fix: treat eagle as cost=1 (it's the goal)
        
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
        
        # Priority queue: (f, counter, pos)
        # Separated path tracking to avoid type comparison issues with lists
        counter = 0
        g_start = 0
        h_start = self._manhattan_distance(start, goal)
        
        pq = [(g_start + h_start, counter, start)]
        visited = {}  # pos -> best g_cost
        parent = {}  # pos -> (parent_pos, cost_to_get_here)
        
        while pq:
            f, _, (x, y) = heapq.heappop(pq)
            
            # Skip if we've already visited this with better cost
            if (x, y) in visited:
                continue
            visited[(x, y)] = True
            
            if (x, y) == goal:
                # Reconstruct path from parent pointers
                path = []
                current = goal
                while current in parent:
                    path.append(current)
                    current = parent[current][0]
                path.append(start)
                return list(reversed(path))
            
            # Get g cost from parent tracking
            current_g = 0
            if (x, y) in parent:
                current_g = parent[(x, y)][1]
            
            # Explore 4 neighbors
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                if not self.grid.is_valid(nx, ny):
                    continue
                
                if (nx, ny) in visited:
                    continue
                
                # Always allow reaching the goal tile (BUG 3 fix)
                if (nx, ny) == goal:
                    new_g = current_g + 1
                    parent[(nx, ny)] = ((x, y), new_g)
                    counter += 1
                    h = self._manhattan_distance((nx, ny), goal)
                    f = new_g + h
                    heapq.heappush(pq, (f, counter, (nx, ny)))
                    continue
                
                # Get tile cost
                move_cost = self._get_tile_cost(nx, ny)
                
                # Skip blocked tiles (cost infinity)
                if move_cost == float('inf'):
                    continue
                
                # Calculate new g cost
                new_g = current_g + move_cost
                
                # Only add if not visited or if we found a better path
                if (nx, ny) not in parent or parent[(nx, ny)][1] > new_g:
                    parent[(nx, ny)] = ((x, y), new_g)
                    
                    # Calculate f = g + h
                    h = self._manhattan_distance((nx, ny), goal)
                    f = new_g + h
                    
                    # Add to priority queue
                    counter += 1
                    heapq.heappush(pq, (f, counter, (nx, ny)))
        
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
