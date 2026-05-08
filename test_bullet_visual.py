"""Visual test of bullet rendering."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    import pygame
    print("Pygame available - running visual test")
    
    from config import TILE_SIZE
    from main import GameWindow
    import time
    
    # Create window
    window = GameWindow()
    
    # Spawn player
    window.state.spawn_player()
    
    # Shoot up
    print("Shooting UP...")
    window.state.tick(0.016, {'direction': 'UP', 'shoot': True})
    
    # Render
    window._render()
    
    # Check bullets
    bullets = window.state.bullets.get_active_bullets()
    print(f"\nBullets in game: {len(bullets)}")
    if bullets:
        b = bullets[0]
        print(f"Bullet 0: pos=({b.x:.2f}, {b.y:.2f}), alive={b.alive}")
        bx, by = b.get_precise_position()
        px = bx * TILE_SIZE + TILE_SIZE // 2
        py = by * TILE_SIZE + TILE_SIZE // 2
        print(f"Rendered at pixel: ({int(px)}, {int(py)})")
    
    # Keep rendering for 2 seconds so we can see the window
    print("\nGame window will be open for 2 seconds...")
    start = time.time()
    while time.time() - start < 2:
        window.state.tick(0.016, {'direction': 'NONE', 'shoot': False})
        window._render()
        pygame.time.delay(16)
    
    pygame.quit()
    
except ImportError:
    print("Pygame not available - skipping visual test")
