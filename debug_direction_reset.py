"""Debug direction change reset."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from game import GameState

game = GameState(level=1)
game.spawn_player()

print("=" * 60)
print("DIRECTION RESET DEBUG")
print("=" * 60)

# Move RIGHT
print(f"\nMoving RIGHT for 3 frames:")
for frame in range(3):
    print(f"  Before tick: direction={game.player.direction_name}, progress={game.player.move_progress:.3f}")
    game.tick(0.016, {'direction': 'RIGHT', 'shoot': False})
    print(f"  After tick: direction={game.player.direction_name}, progress={game.player.move_progress:.3f}")

# Change to UP
print(f"\nChanging direction to UP:")
print(f"  Before tick: direction={game.player.direction_name}, progress={game.player.move_progress:.3f}")
print(f"  Input: direction='UP'")

# Let's trace what should happen
input_state = {'direction': 'UP', 'shoot': False}
new_direction = input_state.get('direction', 'NONE')
old_direction = game.player.direction_name
print(f"  Comparison: new_direction='{new_direction}' != old_direction='{old_direction}' ? {new_direction != old_direction}")

game.tick(0.016, input_state)
print(f"  After tick: direction={game.player.direction_name}, progress={game.player.move_progress:.3f}")

print("\n" + "=" * 60)
