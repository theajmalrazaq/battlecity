#!/usr/bin/env python3
"""
Debug boss arena spawn locations
"""

import sys
sys.path.insert(0, 'src')

from map_generator import LevelGenerator
from config import TERRAIN

def debug_boss_arena():
    """Check terrain at spawn locations."""
    gen = LevelGenerator('BOSS')
    level_data = gen.generate()
    terrain_map = level_data['map']
    
    print("Boss Arena Debug:")
    print(f"Arena spans x: 7-18, y: 7-18")
    print()
    
    # Check player spawn (13, 18)
    player_x, player_y = 13, 18
    terrain = terrain_map[player_y][player_x]
    terrain_name = [k for k, v in TERRAIN.items() if v == terrain][0]
    print(f"Player spawn at ({player_x}, {player_y}): {terrain_name} (value={terrain})")
    
    # Check boss spawn (13, 7)
    boss_x, boss_y = 13, 7
    terrain = terrain_map[boss_y][boss_x]
    terrain_name = [k for k, v in TERRAIN.items() if v == terrain][0]
    print(f"Boss spawn at ({boss_x}, {boss_y}): {terrain_name} (value={terrain})")
    
    # Check surrounding areas
    print("\nSurrounding player spawn:")
    for dy in [-1, 0, 1]:
        for dx in [-1, 0, 1]:
            x, y = player_x + dx, player_y + dy
            terrain = terrain_map[y][x]
            terrain_name = [k for k, v in TERRAIN.items() if v == terrain][0]
            marker = " *" if (dx == 0 and dy == 0) else ""
            print(f"  ({x}, {y}): {terrain_name}{marker}")
    
    # Check for eagle position
    print("\nSearching for eagle...")
    for y in range(7, 19):
        for x in range(7, 19):
            if terrain_map[y][x] == TERRAIN['EAGLE']:
                print(f"  Eagle found at ({x}, {y})")

if __name__ == '__main__':
    debug_boss_arena()
