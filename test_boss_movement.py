#!/usr/bin/env python3
"""
Test player movement in boss arena
"""

import sys
sys.path.insert(0, 'src')

from game import GameState
from config import TERRAIN

def test_player_movement():
    """Test that player can move in boss arena."""
    print("Testing Player Movement in Boss Arena...")
    
    state = GameState('BOSS')
    
    # Initial position
    print(f"Player starting at: ({state.player.x}, {state.player.y})")
    print(f"Player direction: {state.player.direction_name}")
    
    # Try to move right
    print("\nTesting RIGHT movement...")
    input_state = {'direction': 'RIGHT', 'shoot': False}
    
    for i in range(5):
        print(f"  Tick {i}: Position ({state.player.x}, {state.player.y})", end="")
        
        # Check if next position is valid
        next_x = state.player.x + 1
        next_y = state.player.y
        terrain = state.grid.get_terrain(next_x, next_y)
        terrain_name = [k for k, v in TERRAIN.items() if v == terrain][0]
        can_move = state.collision_detector.can_tank_move_to(state.player, next_x, next_y)
        
        print(f" -> next ({next_x}, {next_y}) is {terrain_name}, can_move={can_move}")
        
        state.tick(0.016, input_state)
    
    print(f"\nFinal position: ({state.player.x}, {state.player.y})")
    
    # Try to move up
    print("\nTesting UP movement...")
    input_state = {'direction': 'UP', 'shoot': False}
    initial_y = state.player.y
    
    for i in range(5):
        state.tick(0.016, input_state)
    
    if state.player.y < initial_y:
        print(f"✓ Player moved UP successfully (y: {initial_y} -> {state.player.y})")
    else:
        print(f"✗ Player did not move UP (y: {initial_y} -> {state.player.y})")

if __name__ == '__main__':
    test_player_movement()
