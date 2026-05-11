

import random
from collections import deque
from config import TERRAIN, GRID_WIDTH, GRID_HEIGHT


class CSPMapGenerator:
  

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
      
        eagle_x, eagle_y = self.eagle_pos
        
        cardinal_neighbors = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        diagonal_neighbors = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        
        if self.level == 1:
            # Level 1 (PDF spec: 2-layer protection):
            # Protect 3 of 4 cardinal neighbors with brick/steel, leave 1 open as corridor
            # (all 4 blocked = eagle unreachable = reachability check fails every time)
            shuffled_cardinals = list(cardinal_neighbors)
            random.shuffle(shuffled_cardinals)
            for i, (dx, dy) in enumerate(shuffled_cardinals):
                nx, ny = eagle_x + dx, eagle_y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height and self.grid[ny][nx] is None:
                    if i < 3:  # Protect 3 out of 4 cardinal neighbors
                        terrain = random.choice([TERRAIN['BRICK'], TERRAIN['STEEL']])
                        self.grid[ny][nx] = terrain
                        self.wall_count += 1
                    else:       # Leave the 4th open as a corridor
                        self.grid[ny][nx] = TERRAIN['EMPTY']
        else:
            # Other levels: 90% chance protection on each cardinal neighbor
            for dx, dy in cardinal_neighbors:
                nx, ny = eagle_x + dx, eagle_y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height and self.grid[ny][nx] is None:
                    if random.random() < 0.9:
                        terrain = random.choice([TERRAIN['BRICK'], TERRAIN['STEEL']])
                        self.grid[ny][nx] = terrain
                        self.wall_count += 1
                    else:
                        self.grid[ny][nx] = TERRAIN['EMPTY']
        
        # Diagonal neighbors: 70% protection chance for both levels
        for dx, dy in diagonal_neighbors:
            nx, ny = eagle_x + dx, eagle_y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height and self.grid[ny][nx] is None:
                if random.random() < 0.7:
                    terrain = random.choice([TERRAIN['BRICK'], TERRAIN['STEEL']])
                    self.grid[ny][nx] = terrain
                    self.wall_count += 1
                else:
                    self.grid[ny][nx] = TERRAIN['EMPTY']
        
        # Layer 2 (Level 1 only): Seed protection in the 2-tile outer ring
        if self.level == 1:
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    if abs(dx) != 2 and abs(dy) != 2:
                        continue  # Only process the outer ring
                    nx, ny = eagle_x + dx, eagle_y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height and self.grid[ny][nx] is None:
                        if random.random() < 0.6:  # 60% chance in outer ring
                            terrain = random.choice([TERRAIN['BRICK'], TERRAIN['STEEL']])
                            self.grid[ny][nx] = terrain
                            self.wall_count += 1
        
        # Ensure at least one neighbor has protection (fallback for all levels)
        has_any_protection = any(
            0 <= eagle_x + dx < self.width and 0 <= eagle_y + dy < self.height and
            self.grid[eagle_y + dy][eagle_x + dx] in [TERRAIN['BRICK'], TERRAIN['STEEL']]
            for dx, dy in cardinal_neighbors + diagonal_neighbors
        )
        if not has_any_protection:
            nx, ny = eagle_x, eagle_y - 1
            if 0 <= nx < self.width and 0 <= ny < self.height and self.grid[ny][nx] is None:
                self.grid[ny][nx] = TERRAIN['BRICK']
                self.wall_count += 1
        
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
       
        eagle_x, eagle_y = self.eagle_pos
        
        # Count inner ring (distance 1) protection
        inner_protected = 0
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = eagle_x + dx, eagle_y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if self.grid[ny][nx] in [TERRAIN['BRICK'], TERRAIN['STEEL']]:
                        inner_protected += 1
        
        if self.level == 1:
            # Level 1: need both inner AND outer ring protection
            if inner_protected < 2:
                return False
            # Count outer ring (distance 2) protection
            outer_protected = 0
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    if abs(dx) != 2 and abs(dy) != 2:
                        continue
                    nx, ny = eagle_x + dx, eagle_y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        if self.grid[ny][nx] in [TERRAIN['BRICK'], TERRAIN['STEEL']]:
                            outer_protected += 1
            return outer_protected >= 2
        else:
            # Other levels: at least 1 inner ring neighbor is protected
            return inner_protected >= 1

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
       
        player_x, player_y = self.player_spawn
        
        for spawn_x, spawn_y in self.spawn_points:
            dist = abs(spawn_x - player_x) + abs(spawn_y - player_y)
            if dist < self.fairness_distance:
                return False
        
        return True

    def _check_density_constraint(self):
        
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
       
        eagle_x, eagle_y = self.eagle_pos
        
        # Check if at least one spawn can reach eagle
        for spawn_x, spawn_y in self.spawn_points:
            if self._has_path(spawn_x, spawn_y, eagle_x, eagle_y):
                return True
        
        return False

    def get_grid_state(self):
       
        return [row[:] for row in self.grid]
