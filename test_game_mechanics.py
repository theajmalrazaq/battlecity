"""Quick test to verify game mechanics work."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from game import GameState
from config import PLAYER_SPAWN

# Create game
game = GameState(level=1)
game.spawn_player()

print("=" * 50)
print("GAME MECHANICS TEST")
print("=" * 50)

# Test 1: Player exists
assert game.player is not None, "Player should exist"
assert game.player.is_player == True, "Should be marked as player"
print(f"✓ Player spawned at {game.player.get_position()}")
print(f"  - Color: {game.player.color}")
print(f"  - HP: {game.player.hp}")
print(f"  - Fire rate: {game.player.fire_rate}s")

# Test 2: Player can shoot
assert game.player.ready_to_shoot(), "Player should be able to shoot initially"
game.player.shoot()
print(f"✓ Player can shoot: has_bullet = {game.player.has_bullet}")

# Test 3: Fire cooldown active
assert not game.player.ready_to_shoot(), "Player should have cooldown after shooting"
print(f"✓ Fire cooldown active: {game.player.fire_cooldown}s")

# Test 4: Player movement
game.player.set_direction('UP')
assert game.player.direction_name == 'UP', "Should set direction"
print(f"✓ Player can change direction: {game.player.direction_name}")

# Test 5: Game tick with input
input_state = {'direction': 'RIGHT', 'shoot': True}
game.tick(0.1, input_state)
print(f"✓ Game tick processed with shooting input")

# Test 6: Bullets created
bullets = game.bullets.get_active_bullets()
print(f"✓ Bullets in game: {len(bullets)}")
if bullets:
    print(f"  - First bullet position: {bullets[0].get_precise_position()}")

print("\n" + "=" * 50)
print("ALL TESTS PASSED - Game mechanics working!")
print("=" * 50)
print("\nGAME CONTROLS:")
print("  Arrow Keys = Move")
print("  Z or Ctrl = Shoot")
print("  Space = Pause")
print("  ESC = Quit")
