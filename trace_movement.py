#!/usr/bin/env python3
"""
Trace player movement in detail
"""

import sys
sys.path.insert(0, 'src')

from game import GameState

def trace_player_movement():
    """Trace player movement step by step."""
    print("Tracing Player Movement...")
    
    state = GameState('BOSS')
    
    player = state.player
    print(f"\nInitial player state:")
    print(f"  Position: ({player.x}, {player.y})")
    print(f"  Direction: {player.direction_name}")
    print(f"  Move cooldown: {player.move_cooldown}")
    
    # Manually do what tick() does
    input_state = {'direction': 'RIGHT', 'shoot': False}
    
    print(f"\nStep 1: INPUT")
    print(f"  Setting direction to RIGHT")
    state.update_player_input(input_state)
    print(f"  Player direction: {player.direction_name}")
    print(f"  Player position: ({player.x}, {player.y})")
    
    print(f"\nStep 2: AGENT DECISIONS")
    for tank in state.tanks:
        if tank.alive and not tank.is_player:
            if tank in state.ai_agents:
                agent = state.ai_agents[tank]
                print(f"  Boss making decision...")
                agent.decide(0.016, state)
                print(f"  Boss direction: {tank.direction_name}")
                print(f"  Boss position: ({tank.x}, {tank.y})")
    
    print(f"\nStep 3: MOVE")
    print(f"  Player state before move:")
    print(f"    Position: ({player.x}, {player.y})")
    print(f"    Direction: {player.direction_name}")
    print(f"    Move cooldown: {player.move_cooldown}")
    
    # Check if player will move
    if player.direction_name != 'NONE':
        if player.move_cooldown <= 0.0:
            next_x = player.x + player.direction[0]
            next_y = player.y + player.direction[1]
            can_move = state.collision_detector.can_tank_move_to(player, next_x, next_y)
            print(f"    Next position: ({next_x}, {next_y})")
            print(f"    Can move: {can_move}")
    
    # Now run the actual tick to see what happens
    print(f"\nRunning actual tick()...")
    state.tick(0.016, input_state)
    
    print(f"\nPlayer state after tick:")
    print(f"  Position: ({player.x}, {player.y})")
    print(f"  Direction: {player.direction_name}")

if __name__ == '__main__':
    trace_player_movement()
