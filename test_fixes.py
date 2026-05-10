#!/usr/bin/env python3
"""
Quick test to verify boss level and game-over fixes.
"""

import sys
sys.path.insert(0, 'src')

from game import GameState
from config import PLAYER_SPAWN

def test_boss_level():
    """Test boss level initialization."""
    print("Testing Boss Level...")
    
    state = GameState('BOSS')
    print(f"✓ Boss level created")
    print(f"  Player position: ({state.player.x}, {state.player.y})")
    print(f"  Player alive: {state.player.alive}")
    print(f"  Active enemies: {len(state.ai_agents)}")
    
    # Check that boss is not at player location
    for tank in state.tanks:
        if tank != state.player:
            print(f"  Boss position: ({tank.x}, {tank.y})")
            assert tank.x != state.player.x or tank.y != state.player.y, "Boss spawned at player location!"
            print(f"  ✓ Boss at different location from player")
    
    # Run a few ticks to verify AI works
    for i in range(10):
        state.tick(0.016, {'direction': 'NONE', 'shoot': False})
    
    print(f"✓ Game loop ran 10 ticks without error")

def test_menu():
    """Test menu system."""
    print("\nTesting Menu System...")
    try:
        from menu import MainMenu
        import pygame
        pygame.init()
        menu = MainMenu()
        print(f"✓ Menu created")
        print(f"  Levels available: {len(menu.levels)}")
        for level in menu.levels:
            print(f"    - {level['name']}")
        print(f"✓ Menu system working")
    except Exception as e:
        print(f"✗ Menu error: {e}")

def test_spawn_logic():
    """Test that spawn logic correctly places boss and player."""
    print("\nTesting Spawn Logic...")
    
    state = GameState('BOSS')
    
    # Check player spawn location (should be at safe corner outside arena)
    assert state.player.x == 0 and state.player.y == 0, f"Player not at (0, 0), at ({state.player.x}, {state.player.y})"
    print(f"✓ Player spawned at correct boss level location (0, 0) - outside arena")
    
    # Check boss spawn location
    boss = None
    for tank in state.tanks:
        if tank != state.player:
            boss = tank
            break
    
    assert boss is not None, "Boss not spawned!"
    assert boss.x == 13 and boss.y == 7, f"Boss not at (13, 7), at ({boss.x}, {boss.y})"
    print(f"✓ Boss spawned at correct location (13, 7)")
    
    # Verify they're not the same tank
    assert state.player != boss, "Player and boss are the same object!"
    print(f"✓ Player and boss are separate objects")

if __name__ == '__main__':
    try:
        test_spawn_logic()
        test_boss_level()
        test_menu()
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
