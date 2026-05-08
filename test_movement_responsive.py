"""Test movement responsiveness with direction changes."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from game import GameState

game = GameState(level=1)
game.spawn_player()

print("=" * 60)
print("MOVEMENT RESPONSIVENESS TEST")
print("=" * 60)

print(f"\nInitial player position: {game.player.get_position()}")
print(f"Initial direction: {game.player.direction_name}")
print(f"Initial move_progress: {game.player.move_progress}")

# Move RIGHT
print("\n--- Moving RIGHT ---")
for frame in range(3):
    game.tick(0.016, {'direction': 'RIGHT', 'shoot': False})
    pos = game.player.get_position()
    print(f"Frame {frame+1}: pos={pos}, direction={game.player.direction_name}, progress={game.player.move_progress:.3f}")

# Change to UP - should reset progress for responsive controls
print("\n--- Changing direction to UP ---")
for frame in range(3):
    game.tick(0.016, {'direction': 'UP', 'shoot': False})
    pos = game.player.get_position()
    print(f"Frame {frame+1}: pos={pos}, direction={game.player.direction_name}, progress={game.player.move_progress:.3f}")

# Change back to RIGHT
print("\n--- Changing direction back to RIGHT ---")
for frame in range(3):
    game.tick(0.016, {'direction': 'RIGHT', 'shoot': False})
    pos = game.player.get_position()
    print(f"Frame {frame+1}: pos={pos}, direction={game.player.direction_name}, progress={game.player.move_progress:.3f}")

# Move without direction changes (should accumulate progress and move smoothly)
print("\n--- Continuous RIGHT movement (no direction changes) ---")
for frame in range(10):
    game.tick(0.016, {'direction': 'RIGHT', 'shoot': False})
    pos = game.player.get_position()
    print(f"Frame {frame+1}: pos={pos}, progress={game.player.move_progress:.3f}")

print("\n" + "=" * 60)
