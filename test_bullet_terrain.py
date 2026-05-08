"""Test terrain at bullet path."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from game import GameState
from config import TERRAIN

game = GameState(level=1)
game.spawn_player()

print("Player position:", game.player.get_position())
print("\nTerrain in front of player (UP direction):")
for y in range(game.player.y - 10, game.player.y + 1):
    if 0 <= y < 26:
        terrain = game.grid.get_terrain(game.player.x, y)
        terrain_name = {v: k for k, v in TERRAIN.items()}.get(terrain, f"Unknown({terrain})")
        print(f"  ({game.player.x}, {y}): {terrain_name}")

# Shoot and trace bullet
print("\n" + "=" * 50)
print("SHOOTING AND TRACING BULLET")
print("=" * 50)

input_state = {'direction': 'UP', 'shoot': True}
game.tick(0.016, input_state)

bullet = game.bullets.get_active_bullets()[0] if game.bullets.get_active_bullets() else None
if bullet:
    print(f"\nBullet spawned at ({bullet.x:.2f}, {bullet.y:.2f})")
    print(f"Direction: {bullet.direction_name}")

# Tick 10 times and check if bullet is still alive
for i in range(10):
    game.tick(0.016, {'direction': 'NONE', 'shoot': False})
    if game.bullets.get_active_bullets():
        print(f"Tick {i+1}: Bullet at ({bullet.x:.2f}, {bullet.y:.2f}) - ALIVE")
    else:
        print(f"Tick {i+1}: Bullet DESTROYED")
        break
