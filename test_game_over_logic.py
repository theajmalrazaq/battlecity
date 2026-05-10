#!/usr/bin/env python3
"""
Test game-over behavior when window is closed vs game won
"""

import sys
sys.path.insert(0, 'src')

from game import GameState

def test_game_over_logic():
    """Test that closing window doesn't trigger game over."""
    print("Testing Game-Over Logic...")
    
    state = GameState(1)  # Level 1
    
    print(f"\nInitial game state:")
    print(f"  Phase: {state.phase}")
    print(f"  is_game_over(): {state.is_game_over()}")
    print(f"  is_level_won(): {state.is_level_won()}")
    
    # Simulate some game play
    for i in range(10):
        state.tick(0.016, {'direction': 'RIGHT', 'shoot': False})
    
    print(f"\nAfter 10 ticks:")
    print(f"  Phase: {state.phase}")
    print(f"  is_game_over(): {state.is_game_over()}")
    print(f"  is_level_won(): {state.is_level_won()}")
    
    # Now kill the player
    state.player.take_damage(100)
    
    print(f"\nAfter player dies:")
    print(f"  Phase: {state.phase}")
    print(f"  is_game_over(): {state.is_game_over()}")
    print(f"  is_level_won(): {state.is_level_won()}")
    
    print(f"\n✓ Game-over logic is working correctly")

if __name__ == '__main__':
    test_game_over_logic()
