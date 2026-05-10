#!/usr/bin/env python3
"""
Test player movement - simpler version
"""

import sys
sys.path.insert(0, 'src')

from tank import Tank, TankType
from grid import Grid
from map_generator import LevelGenerator
from config import DIRECTIONS, TERRAIN

def test_player_direct():
    """Test player movement directly without game state."""
    print("Testing Direct Player Movement...")
    
    # Create grid and load boss level
    gen = LevelGenerator('BOSS')
    level_data = gen.generate()
    
    grid = Grid()
    for y in range(len(level_data['map'])):
        for x in range(len(level_data['map'][y])):
            grid.set_terrain(x, y, level_data['map'][y][x])
    
    # Create player
    player = Tank(TankType.PLAYER, 13, 18, is_player=True)
    
    print(f"Player spawned at: ({player.x}, {player.y})")
    print(f"Player direction: {player.direction_name}")
    print(f"Player direction vector: {player.direction}")
    
    # Check what's around the player
    print("\nSurrounding terrain:")
    for dy in [-1, 0, 1]:
        for dx in [-1, 0, 1]:
            x, y = 13 + dx, 18 + dy
            terrain = grid.get_terrain(x, y)
            terrain_name = [k for k, v in TERRAIN.items() if v == terrain][0]
            marker = " <player>" if (dx == 0 and dy == 0) else ""
            print(f"  ({x}, {y}): {terrain_name}{marker}")
    
    # Manually set direction and update position
    print("\nManual movement test:")
    player.set_direction('RIGHT')
    print(f"Set direction to RIGHT: {player.direction_name}, vector={player.direction}")
    
    # Calculate next position
    next_x = player.x + player.direction[0]
    next_y = player.y + player.direction[1]
    
    terrain = grid.get_terrain(next_x, next_y)
    terrain_name = [k for k, v in TERRAIN.items() if v == terrain][0]
    print(f"Next position ({next_x}, {next_y}) is {terrain_name}")
    
    # Move manually
    player.x = next_x
    player.y = next_y
    print(f"Player moved to ({player.x}, {player.y})")

if __name__ == '__main__':
    test_player_direct()
