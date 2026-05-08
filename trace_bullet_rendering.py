"""Detailed trace of bullet rendering pipeline."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from game import GameState
from config import TILE_SIZE

game = GameState(level=1)
game.spawn_player()

print("=" * 60)
print("BULLET RENDERING PIPELINE TRACE")
print("=" * 60)

# Shoot
print("\n1. SHOOTING UP")
game.tick(0.016, {'direction': 'UP', 'shoot': True})

# Check game state
bullets = game.bullets.get_active_bullets()
print(f"   Bullets in game.bullets.bullets list: {len(game.bullets.bullets)}")
print(f"   Bullets from get_active_bullets(): {len(bullets)}")

if bullets:
    bullet = bullets[0]
    print(f"\n2. BULLET PROPERTIES")
    print(f"   Position (game coords): x={bullet.x:.3f}, y={bullet.y:.3f}")
    print(f"   Alive: {bullet.alive}")
    print(f"   Direction: {bullet.direction_name}")
    
    # Simulate rendering calculation
    bx, by = bullet.get_precise_position()
    x = bx * TILE_SIZE + TILE_SIZE // 2
    y = by * TILE_SIZE + TILE_SIZE // 2
    
    print(f"\n3. RENDERING CALCULATION")
    print(f"   get_precise_position(): ({bx:.3f}, {by:.3f})")
    print(f"   x = {bx:.3f} * {TILE_SIZE} + {TILE_SIZE//2} = {x:.1f}")
    print(f"   y = {by:.3f} * {TILE_SIZE} + {TILE_SIZE//2} = {y:.1f}")
    print(f"   Final render position (pixels): ({int(x)}, {int(y)})")
    print(f"   Window size: 780 x 780")
    print(f"   Bullet visible: {0 <= x < 780 and 0 <= y < 780}")
    
    # Simulate a few frames
    print(f"\n4. MOVEMENT OVER 5 FRAMES")
    for frame in range(5):
        game.tick(0.016, {'direction': 'NONE', 'shoot': False})
        if game.bullets.get_active_bullets():
            bullet = game.bullets.get_active_bullets()[0]
            bx, by = bullet.get_precise_position()
            x = bx * TILE_SIZE + TILE_SIZE // 2
            y = by * TILE_SIZE + TILE_SIZE // 2
            print(f"   Frame {frame+1}: pos=({bx:.3f}, {by:.3f}) → pixel=({int(x)}, {int(y)}) alive={bullet.alive}")
        else:
            print(f"   Frame {frame+1}: BULLET DESTROYED")
            break
else:
    print("ERROR: No bullets created!")

print("\n" + "=" * 60)
