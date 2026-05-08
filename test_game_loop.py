#!/usr/bin/env python3
"""Test game logic without graphics."""

import sys
sys.path.insert(0, 'src')

from game import GameState, GamePhase
from config import PLAYER_LIVES

# Create a game and run for a few ticks
print("Creating BOSS level game...")
game = GameState('BOSS')

print(f"Game initialized:")
print(f"  - Level: {game.level}")
print(f"  - Phase: {game.phase.value}")
print(f"  - Player: {game.player}")
print(f"  - Player lives: {game.player_lives}")
print(f"  - Active tanks: {len(game.tanks)}")
print(f"  - Enemy pool: {len(game.enemy_pool)}")

# Run some ticks
print(f"\nRunning 20 game ticks...")
for tick in range(20):
    input_state = {'direction': 'NONE', 'shoot': False}
    game.tick(0.016, input_state)  # 60 FPS = ~16ms per frame
    
    print(f"  Tick {tick+1}: {len(game.tanks)} tanks, {len(game.bullets.bullets)} bullets, " +
          f"Enemies: {game.active_enemies}, Defeated: {game.enemies_defeated}")
    
    if game.is_game_over():
        print(f"    ✓ GAME OVER - {game.get_end_reason()}")
        break
    if game.is_level_won():
        print(f"    ✓ LEVEL WON")
        break

print("\nGame test complete!")
