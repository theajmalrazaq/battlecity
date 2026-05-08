"""Debug CSP generation to see which constraints are failing."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from csp import CSPMapGenerator
from config import TERRAIN

def debug_generation():
    """Test map generation and show which constraints fail."""
    csp = CSPMapGenerator(level=1)
    
    # Try to generate and see what fails
    for attempt in range(5):
        print(f"\n=== Attempt {attempt + 1} ===")
        
        # Reset
        csp._initialize_domains()
        csp.grid = [[None for _ in range(csp.width)] for _ in range(csp.height)]
        csp.wall_count = 0
        
        # Place fixed positions
        for pos, domain in csp.domains.items():
            if len(domain) == 1:
                terrain = list(domain)[0]
                csp.grid[pos[1]][pos[0]] = terrain
                if terrain in [TERRAIN['BRICK'], TERRAIN['STEEL'], TERRAIN['WATER']]:
                    csp.wall_count += 1
        
        # Generate
        if csp._generate_with_constraints():
            print("Grid generated, checking constraints...")
            
            # Check each constraint individually
            result1 = csp._check_base_safety()
            print(f"  Base Safety: {result1}")
            
            result2 = csp._check_reachability()
            print(f"  Reachability: {result2}")
            
            result3 = csp._check_fairness()
            print(f"  Fairness: {result3}")
            
            result4 = csp._check_density_constraint()
            print(f"  Density: {result4}")
            
            result5 = csp._check_water_placement()
            print(f"  Water Placement: {result5}")
            
            # Print density info
            wall_count = 0
            total = 0
            for y in range(csp.height):
                for x in range(csp.width):
                    if (x, y) in [csp.eagle_pos, csp.player_spawn] + list(csp.spawn_points):
                        continue
                    total += 1
                    if csp.grid[y][x] in [TERRAIN['BRICK'], TERRAIN['STEEL'], TERRAIN['WATER']]:
                        wall_count += 1
            print(f"  Density: {wall_count}/{total} = {wall_count/total*100:.1f}% walls (limit 40%)")

if __name__ == '__main__':
    debug_generation()
