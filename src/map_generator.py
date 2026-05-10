"""
Map Generator - Creates playable levels using CSP
Phase 2A: Map Generation - Module A
"""

from csp import CSPMapGenerator
from config import LEVEL_CONFIG, TERRAIN


class LevelGenerator:
    """
    Generates complete levels with:
    - Map (via CSP)
    - Enemy pool
    - Difficulty configuration
    """

    def __init__(self, level=1):
        """
        Initialize level generator.
        
        Args:
            level: 1, 2, or 'BOSS'
        """
        self.level = level
        self.config = LEVEL_CONFIG.get(level, LEVEL_CONFIG[1])
        self.map = None
        self.enemy_pool = None

    def generate(self, max_attempts=50):
        """
        Generate complete level.
        
        Args:
            max_attempts: CSP attempts before giving up
        
        Returns:
            Dict with 'map' and 'enemy_pool'
        """
        # Special handling for boss level
        if self.level == 'BOSS':
            return self._generate_boss_level()
        
        # Generate map using CSP
        csp_gen = CSPMapGenerator(self.level)
        self.map = csp_gen.generate(max_attempts)
        
        if self.map is None:
            print(f"ERROR: Failed to generate level {self.level}")
            return None
        
        # Build enemy pool based on level config
        self.enemy_pool = self._create_enemy_pool()
        
        return {
            'map': self.map,
            'enemy_pool': self.enemy_pool,
            'config': self.config
        }

    def _create_enemy_pool(self):
        """
        Create the list of enemies to spawn for this level.
        
        Returns:
            List of TankType enums in spawn order
        """
        from tank import TankType
        
        enemy_config = self.config.get('enemy_pool', {})
        pool = []
        
        # Build pool based on config
        for tank_type, count in enemy_config.items():
            for _ in range(count):
                pool.append(TankType[tank_type])
        
        return pool

    def _generate_boss_level(self):
        """
        Generate boss arena level (12x12 area) with randomized obstacles.
        Phase 3C: Boss Arena Level Generation - CSP-based with random variation
        
        Returns:
            Dict with 'map' and 'enemy_pool' (contains 1 BOSS)
        """
        from tank import TankType
        from config import GRID_WIDTH, GRID_HEIGHT
        import random
        
        # Create small arena (12x12 in center of map)
        arena_size = 12
        start_x = (GRID_WIDTH - arena_size) // 2
        start_y = (GRID_HEIGHT - arena_size) // 2
        
        # Initialize full grid with empty
        self.map = [[TERRAIN['EMPTY'] for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        
        # Create outer steel fortress walls (arena boundary)
        for x in range(start_x - 1, start_x + arena_size + 1):
            if 0 <= x < GRID_WIDTH:
                self.map[start_y - 1][x] = TERRAIN['STEEL']
                self.map[start_y + arena_size][x] = TERRAIN['STEEL']
        
        for y in range(start_y, start_y + arena_size):
            if 0 <= y < GRID_HEIGHT:
                self.map[y][start_x - 1] = TERRAIN['STEEL']
                self.map[y][start_x + arena_size] = TERRAIN['STEEL']
        
        # Create internal arena layout with obstacles - randomized pattern
        # Keep some predictability (pillars) but vary brick placement
        for y in range(start_y, start_y + arena_size):
            for x in range(start_x, start_x + arena_size):
                # Steel pillars at regular intervals (always in same spots)
                if (x - start_x) % 4 == 2 and (y - start_y) % 4 == 2:
                    self.map[y][x] = TERRAIN['STEEL']
                # Randomized brick obstacles (60% chance at regular intervals)
                elif (x - start_x) % 3 == 1 and (y - start_y) % 3 == 1:
                    if random.random() < 0.6:
                        self.map[y][x] = TERRAIN['BRICK']
        
        # Create exactly one water patch (random 2x2 or 1x2 area)
        water_x = start_x + random.randint(2, 8)
        water_y = start_y + random.randint(2, 8)
        for wy in range(water_y, water_y + 2):
            for wx in range(water_x, water_x + 2):
                if start_x <= wx < start_x + arena_size and start_y <= wy < start_y + arena_size:
                    self.map[wy][wx] = TERRAIN['WATER']
        
        # Boss arena has NO eagle tile — win/lose decided by boss HP and player lives only
        
        # Boss enemy pool - just 1 boss
        self.enemy_pool = [TankType.BOSS]
        
        print(f"Boss Arena Generated: 12x12 randomized arena with obstacles")
        
        return {
            'map': self.map,
            'enemy_pool': self.enemy_pool,
            'config': self.config,
            'is_boss_level': True
        }

    def get_map(self):
        """Return generated map."""
        return self.map

    def get_enemy_pool(self):
        """Return enemy pool."""
        return self.enemy_pool

    def get_config(self):
        """Return level configuration."""
        return self.config

    def print_stats(self):
        """Print level statistics for debugging."""
        if self.map is None:
            print("Map not generated yet")
            return
        
        print(f"\n=== Level {self.level} Statistics ===")
        
        # Count terrain types
        counts = {t: 0 for t in TERRAIN.values()}
        for row in self.map:
            for terrain in row:
                counts[terrain] = counts.get(terrain, 0) + 1
        
        terrain_names = {v: k for k, v in TERRAIN.items()}
        for terrain_type, count in counts.items():
            name = terrain_names.get(terrain_type, "UNKNOWN")
            pct = 100 * count / (26 * 26)
            print(f"  {name}: {count} tiles ({pct:.1f}%)")
        
        print(f"\nEnemy Pool: {len(self.enemy_pool)} enemies")
        if self.enemy_pool:
            from tank import TankType
            from collections import Counter
            type_counts = Counter(self.enemy_pool)
            for tank_type in sorted(type_counts.keys(), key=lambda x: x.value):
                count = type_counts[tank_type]
                print(f"  {tank_type.value}: {count}x")
