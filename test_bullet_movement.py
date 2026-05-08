"""Test bullet movement."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from game import GameState

# Create game
game = GameState(level=1)
game.spawn_player()

print("=" * 50)
print("BULLET MOVEMENT TEST")
print("=" * 50)

# Player shoots
input_state = {'direction': 'UP', 'shoot': True}
game.tick(0.016, input_state)  # ~60 FPS frame

print(f"After first tick:")
print(f"  Bullets in game: {len(game.bullets.get_active_bullets())}")

if game.bullets.get_active_bullets():
    bullet = game.bullets.get_active_bullets()[0]
    print(f"  Bullet position: ({bullet.x:.2f}, {bullet.y:.2f})")
    print(f"  Bullet direction: {bullet.direction_name}")
    print(f"  Bullet speed: {bullet.speed} tiles/sec")
    print(f"  Bullet alive: {bullet.alive}")

# Tick several more times to see movement
print(f"\nAfter 10 more ticks (0.16 seconds total):")
for i in range(10):
    game.tick(0.016, {'direction': 'NONE', 'shoot': False})

if game.bullets.get_active_bullets():
    bullet = game.bullets.get_active_bullets()[0]
    print(f"  Bullet position: ({bullet.x:.2f}, {bullet.y:.2f})")
    print(f"  Expected movement: 4.0 * 0.16 = {4.0 * 0.16:.2f} tiles")
else:
    print(f"  Bullet destroyed (no bullets left)")

print("\n" + "=" * 50)
