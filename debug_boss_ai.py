#!/usr/bin/env python3
"""
Debug boss AI decisions
"""

import sys
sys.path.insert(0, 'src')

from game import GameState

def test_boss_ai():
    """Test boss AI decisions."""
    print("Debug Boss AI Decisions...\n")
    
    state = GameState('BOSS')
    
    player = state.player
    boss = None
    for tank in state.tanks:
        if tank != state.player:
            boss = tank
            break
    
    print(f"Initial state:")
    print(f"  Player: ({player.x}, {player.y})")
    print(f"  Boss: ({boss.x}, {boss.y})")
    
    # Get the AI agent for the boss
    if boss in state.ai_agents:
        ai_agent = state.ai_agents[boss]
        print(f"  AI Agent: {ai_agent.__class__.__name__}")
        
        # Make a decision
        print(f"\nBoss AI decide():")
        ai_agent.decide(0.016, state)
        print(f"  Boss direction after decision: {boss.direction_name}")
        print(f"  Boss position after decision: ({boss.x}, {boss.y})")
    else:
        print(f"  No AI agent for boss!")

if __name__ == '__main__':
    test_boss_ai()
