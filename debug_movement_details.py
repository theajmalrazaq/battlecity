#!/usr/bin/env python3
"""
Deep debug of tank movement
"""

import sys
sys.path.insert(0, 'src')

from game import GameState

def test_movement_details():
    """Test movement with detailed logging."""
    print("Deep Debug of Tank Movement...\n")
    
    state = GameState('BOSS')
    
    # Find tanks
    player = state.player
    boss = None
    for tank in state.tanks:
        if tank != state.player:
            boss = tank
            break
    
    print(f"Initial state:")
    print(f"  Player: pos=({player.x}, {player.y}), dir={player.direction_name}, move_cooldown={player.move_cooldown}")
    print(f"  Boss: pos=({boss.x}, {boss.y}), dir={boss.direction_name}, move_cooldown={boss.move_cooldown}")
    
    # Check move_cooldown update
    print(f"\nUpdating tank time (0.016s)...")
    for tank in state.tanks:
        tank.update(0.016)
        print(f"  {tank.__class__.__name__}: move_cooldown={tank.move_cooldown}")
    
    # Check collision detection
    print(f"\nChecking collision for player movement RIGHT:")
    next_x = player.x + 1  # RIGHT
    next_y = player.y
    can_move = state.collision_detector.can_tank_move_to(player, next_x, next_y)
    print(f"  Player at ({player.x}, {player.y}), next=({next_x}, {next_y}), can_move={can_move}")
    
    # Check for boss
    print(f"\nChecking collision for boss movement:")
    next_x = boss.x + boss.direction[0]
    next_y = boss.y + boss.direction[1]
    can_move = state.collision_detector.can_tank_move_to(boss, next_x, next_y)
    print(f"  Boss at ({boss.x}, {boss.y}), next=({next_x}, {next_y}), dir={boss.direction_name}, can_move={can_move}")

if __name__ == '__main__':
    test_movement_details()
