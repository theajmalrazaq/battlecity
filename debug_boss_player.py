#!/usr/bin/env python3
"""
Debug boss movement affecting player
"""

import sys
sys.path.insert(0, 'src')

from game import GameState

def test_boss_affects_player():
    """Test if boss movement affects player."""
    print("Debugging Boss Level Movement...")
    
    state = GameState('BOSS')
    
    print(f"Initial state:")
    print(f"  Player: ({state.player.x}, {state.player.y}), direction={state.player.direction_name}")
    
    # Find boss
    boss = None
    for tank in state.tanks:
        if tank != state.player:
            boss = tank
            break
    
    if boss:
        print(f"  Boss: ({boss.x}, {boss.y}), direction={boss.direction_name}")
    
    # Set player direction to RIGHT
    print(f"\nSetting player direction to RIGHT")
    state.player.set_direction('RIGHT')
    print(f"  Player direction_name: {state.player.direction_name}")
    print(f"  Player direction: {state.player.direction}")
    
    # Run one tick with RIGHT input
    print(f"\nRunning tick with RIGHT input...")
    input_state = {'direction': 'RIGHT', 'shoot': False}
    
    print(f"Before tick:")
    print(f"  Player: ({state.player.x}, {state.player.y})")
    if boss:
        print(f"  Boss: ({boss.x}, {boss.y})")
    
    state.tick(0.016, input_state)
    
    print(f"After tick:")
    print(f"  Player: ({state.player.x}, {state.player.y}), direction={state.player.direction_name}")
    if boss:
        print(f"  Boss: ({boss.x}, {boss.y}), direction={boss.direction_name}")

if __name__ == '__main__':
    test_boss_affects_player()
