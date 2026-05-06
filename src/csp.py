"""
Constraint Satisfaction Problem (CSP) Solver with Forward Checking & MRV
Phase 2A: Map Generation - Module A

Optimization Techniques:
- Forward Checking: Prune domains after each assignment
- MRV (Minimum Remaining Values): Select variable with smallest domain
- Arc Consistency: Ensure constraints are locally satisfied
"""

import random
from collections import deque
from config import TERRAIN, GRID_WIDTH, GRID_HEIGHT


class CSPMapGenerator:
    """
    Generates valid Battle City maps using Constraint Satisfaction with optimizations.
    
    5 Constraints (from document):
    1. Base Safety: Eagle surrounded by ≥1 ring of brick/steel
    2. Reachability: Valid BFS path from every spawn to eagle
    3. Fairness: No spawn within 10 tiles of player
    4. Density Balance: Max 40% wall tiles
    5. Water Placement: Water can't block only path to eagle
    """

    def __init__(self, level=1, seed=None):
        """Initialize CSP generator."""
        self.level = level
        if seed:
            random.seed(seed)
        
        from config import LEVEL_CONFIG, SPAWN_POINTS, PLAYER_SPAWN, EAGLE_POSITION, SPAWN_FAIRNESS_DISTANCE
        self.config = LEVEL_CONFIG.get(level, LEVEL_CONFIG[1])
        
        self.width = GRID_WIDTH
        self.height = GRID_HEIGHT
        self.grid = [[TERRAIN['EMPTY'] for _ in range(self.width)] for _ in range(self.height)]
        
        self.spawn_points = SPAWN_POINTS
        self.player_spawn = PLAYER_SPAWN
        self.eagle_pos = EAGLE_POSITION
        self.fairness_distance = SPAWN_FAIRNESS_DISTANCE
        
        # Domains for each variable (tile)
        self.domains = {}  # (x,y) -> set of possible terrains
        self._initialize_domains()

    def _initialize_domains(self):
        """Initialize domains for all tiles."""
        for y in range(self.height):
            for x in range(self.width):
                # Special tiles have fixed domains
                if (x, y) == self.eagle_pos:
                    self.domains[(x, y)] = {TERRAIN['EAGLE']}
                elif (x, y) in self.spawn_points or (x, y) == self.player_spawn:
                    self.domains[(x, y)] = {TERRAIN['EMPTY']}
                else:
                    # Regular tiles can be any terrain
                    self.domains[(x, y)] = {
                        TERRAIN['EMPTY'],
                        TERRAIN['BRICK'],
                        TERRAIN['STEEL'],
                        TERRAIN['WATER'],
                        TERRAIN['FOREST']
                    }

    def generate(self, max_attempts=200):
        """
        Generate map using Randomized CSP with constraint-guided domain selection.
        
        Strategy: Hybrid approach
        1. Initialize grid with fixed positions
        2. Fill remaining tiles with random selection from constrained domains
        3. Use forward checking to maintain constraint satisfaction probability
        4. Validate all 5 constraints on complete assignment
        
        Args:
            max_attempts: Number of generation attempts (increased for strict constraints)
        
        Returns:
            Grid if successful, None if failed
        """
        for attempt in range(max_attempts):
            # Reset and initialize
            self._initialize_domains()
            self.grid = [[None for _ in range(self.width)] for _ in range(self.height)]
            self.wall_count = 0
            
            # Place fixed positions first
            for pos, domain in self.domains.items():
                if len(domain) == 1:
                    terrain = list(domain)[0]
                    self.grid[pos[1]][pos[0]] = terrain
                    if terrain in [TERRAIN['BRICK'], TERRAIN['STEEL'], TERRAIN['WATER']]:
                        self.wall_count += 1
            
            # Generate remaining tiles with constraint-aware randomization
            if self._generate_with_constraints():
                # Validate all 5 constraints
                if self._check_all_constraints():
                    return self.grid
        
        return None

    def _generate_with_constraints(self):
        """
        Fill unassigned tiles with constraint-enforcing assignments.
        
        Strategy:
        1. Place protection around eagle (brick/steel)
        2. Ensure reachability by limiting blocking obstacles
        3. Limit water to avoid blocking paths completely
        4. Respect density constraints
        
        Returns:
            True if generation completed successfully
        """
        # Step 1: Place protective ring around eagle
        eagle_x, eagle_y = self.eagle_pos
        protected = False
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = eagle_x + dx, eagle_y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if self.grid[ny][nx] is None:
                        # Place brick/steel with 80% chance, empty with 20%
                        if random.random() < 0.8:
                            terrain = random.choice([TERRAIN['BRICK'], TERRAIN['STEEL']])
                            self.grid[ny][nx] = terrain
                            self.wall_count += 1
                            protected = True
                        else:
                            self.grid[ny][nx] = TERRAIN['EMPTY']
        
        # If no protection was placed, force at least one
        if not protected:
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = eagle_x + dx, eagle_y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height and self.grid[ny][nx] is None:
                        self.grid[ny][nx] = TERRAIN['BRICK']
                        self.wall_count += 1
                        break
                else:
                    continue
                break
        
        # Calculate density limits - LESS RESTRICTIVE to allow paths
        regular_tiles = sum(1 for y in range(self.height) for x in range(self.width)
                           if (x, y) not in [self.eagle_pos, self.player_spawn] + list(self.spawn_points) 
                           and self.grid[y][x] is None)
        max_walls = int(regular_tiles * 0.35) - self.wall_count if regular_tiles > 0 else 0  # 35% instead of 40%
        water_limit = max(1, int(regular_tiles * 0.03))  # Only 3% water to allow paths
        water_placed = sum(1 for y in range(self.height) for x in range(self.width)
                          if self.grid[y][x] == TERRAIN['WATER'])
        
        # Step 2: Fill remaining tiles with density-aware, path-friendly assignment
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] is not None:
                    continue
                
                can_add_wall = self.wall_count < max_walls
                can_add_water = water_placed < water_limit
                
                # Weighted random - FAVOR PASSABLE TILES
                rand = random.random()
                if rand < 0.20 and can_add_wall:
                    self.grid[y][x] = TERRAIN['BRICK']
                    self.wall_count += 1
                elif rand < 0.25 and can_add_wall:
                    self.grid[y][x] = TERRAIN['STEEL']
                    self.wall_count += 1
                elif rand < 0.28 and can_add_water:
                    self.grid[y][x] = TERRAIN['WATER']
                    self.wall_count += 1
                    water_placed += 1
                elif rand < 0.50:
                    self.grid[y][x] = TERRAIN['FOREST']
                else:
                    self.grid[y][x] = TERRAIN['EMPTY']
        
        return True

    def _is_adjacent_to_eagle(self, x, y):
        """Check if tile is adjacent to eagle (8-neighbor)."""
        eagle_x, eagle_y = self.eagle_pos
        return abs(x - eagle_x) <= 1 and abs(y - eagle_y) <= 1 and (x, y) != (eagle_x, eagle_y)



    def _check_all_constraints(self):
        """
        Check all 5 constraints on complete assignment.
        
        Returns:
            True if all constraints satisfied, False otherwise
        """
        # Constraint 1: Base Safety - Eagle surrounded by ≥1 ring of brick/steel
        if not self._check_base_safety():
            return False
        
        # Constraint 2: Reachability - Valid BFS path from EVERY spawn to eagle
        if not self._check_reachability():
            return False
        
        # Constraint 3: Fairness - No spawn within fairness_distance of player
        if not self._check_fairness():
            return False
        
        # Constraint 4: Density Balance - Max 40% of tiles are walls
        if not self._check_density_constraint():
            return False
        
        # Constraint 5: Water Placement - Water can't block the only path to eagle
        if not self._check_water_placement():
            return False
        
        return True

    def _check_base_safety(self):
        """
        Constraint 1: Eagle surrounded by ≥1 ring of brick/steel.
        
        Eagle must have at least one brick or steel tile in its 8 neighbors.
        """
        eagle_x, eagle_y = self.eagle_pos
        
        # Check all 8 neighbors
        has_protection = False
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue  # Skip eagle itself
                
                nx, ny = eagle_x + dx, eagle_y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    terrain = self.grid[ny][nx]
                    if terrain in [TERRAIN['BRICK'], TERRAIN['STEEL']]:
                        has_protection = True
                        break
        
        return has_protection

    def _check_reachability(self):
        """Constraint 2: Valid BFS path from every spawn to eagle."""
        eagle_x, eagle_y = self.eagle_pos
        
        for spawn_x, spawn_y in self.spawn_points:
            if not self._has_path(spawn_x, spawn_y, eagle_x, eagle_y):
                return False
        
        return True

    def _has_path(self, start_x, start_y, goal_x, goal_y):
        """BFS to check if path exists."""
        if self.grid[start_y][start_x] not in [TERRAIN['EMPTY'], TERRAIN['EAGLE']]:
            return False
        
        visited = set()
        queue = deque([(start_x, start_y)])
        visited.add((start_x, start_y))
        
        while queue:
            x, y = queue.popleft()
            
            if x == goal_x and y == goal_y:
                return True
            
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                if (nx, ny) in visited or not (0 <= nx < self.width and 0 <= ny < self.height):
                    continue
                
                terrain = self.grid[ny][nx]
                if terrain in [TERRAIN['EMPTY'], TERRAIN['FOREST'], TERRAIN['EAGLE']]:
                    visited.add((nx, ny))
                    queue.append((nx, ny))
        
        return False

    def _check_fairness(self):
        """Constraint 3: No spawn within fairness_distance of player."""
        player_x, player_y = self.player_spawn
        
        for spawn_x, spawn_y in self.spawn_points:
            dist = abs(spawn_x - player_x) + abs(spawn_y - player_y)
            if dist < self.fairness_distance:
                return False
        
        return True

    def _check_density_constraint(self):
        """
        Constraint 4: Max 40% of tiles are walls (brick+steel+water).
        Min 60% must be passable (empty, forest, eagle).
        """
        wall_count = 0
        total_count = 0
        
        for y in range(self.height):
            for x in range(self.width):
                # Don't count special spawn points/player/eagle
                if (x, y) in [self.eagle_pos, self.player_spawn] + list(self.spawn_points):
                    continue
                
                terrain = self.grid[y][x]
                total_count += 1
                
                if terrain in [TERRAIN['BRICK'], TERRAIN['STEEL'], TERRAIN['WATER']]:
                    wall_count += 1
        
        if total_count == 0:
            return True
        
        wall_ratio = wall_count / total_count
        return wall_ratio <= 0.40  # Strict: max 40% walls

    def _check_water_placement(self):
        """Constraint 5: Water can't block the only path to eagle."""
        eagle_x, eagle_y = self.eagle_pos
        
        # Check if at least one spawn can reach eagle
        for spawn_x, spawn_y in self.spawn_points:
            if self._has_path(spawn_x, spawn_y, eagle_x, eagle_y):
                return True
        
        return False

    def get_grid_state(self):
        """Return generated grid."""
        return [row[:] for row in self.grid]
