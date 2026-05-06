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

    def generate(self, max_attempts=20):
        """
        Generate complete level.
        
        Args:
            max_attempts: CSP attempts before giving up
        
        Returns:
            Dict with 'map' and 'enemy_pool'
        """
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
