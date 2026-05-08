"""Debug why tank can't move."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from game import GameState

game = GameState(level=1)
game.spawn_player()

print("=" * 60)
print("MOVEMENT BLOCKING DEBUG")
print("=" * 60)

player = game.player
print(f"\nPlayer initial state:")
print(f"  Position: {player.get_position()}")
print(f"  Direction: {player.direction}")
print(f"  Direction name: {player.direction_name}")
print(f"  Speed: {player.speed}")

# Try to move RIGHT
print(f"\n--- Testing movement to RIGHT ---")
player.set_direction('RIGHT')
print(f"  Direction after set: {player.direction}")

# Check if the tank CAN move right
x, y = player.get_position()
next_x = x + player.direction[0]
next_y = y + player.direction[1]
can_move = game.collision_detector.can_tank_move_to(player, next_x, next_y)

print(f"  Current pos: ({x}, {y})")
print(f"  Target pos: ({next_x}, {next_y})")
print(f"  Can move there: {can_move}")

# Check what's at the target position
terrain = game.grid.get_terrain(next_x, next_y)
print(f"  Terrain at target: {terrain}")

# Check if there are other tanks there
other_tanks = [t for t in game.tanks if t != player and t.get_position() == (next_x, next_y)]
print(f"  Other tanks at target: {len(other_tanks)}")

# Now let's manually step through one tick
print(f"\n--- Running one tick ---")
player.move_progress = 0.0
player.set_direction('RIGHT')

# Manually do what tick() should do
dt = 0.016
player.move_progress += player.speed * dt
print(f"  After accumulation: move_progress = {player.move_progress}")
print(f"  Is move_progress >= 1.0? {player.move_progress >= 1.0}")

# If >= 1.0, check if we can move
if player.move_progress >= 1.0:
    x, y = player.get_position()
    next_x = x + player.direction[0]
    next_y = y + player.direction[1]
    can_move = game.collision_detector.can_tank_move_to(player, next_x, next_y)
    print(f"  Can move to ({next_x}, {next_y})? {can_move}")
    if can_move:
        player.x = next_x
        player.y = next_y
        player.move_progress -= 1.0
        print(f"  MOVED! New position: {player.get_position()}")
    else:
        print(f"  BLOCKED! Keeping progress for next frame")

print("\n" + "=" * 60)
