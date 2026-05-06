"""
Test Suite for Phase 0 & Phase 1
Verifies core game systems work correctly.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import TERRAIN, DIRECTIONS, GRID_WIDTH, GRID_HEIGHT
from grid import Grid
from tank import Tank, TankType
from bullet import Bullet, BulletManager
from collision import CollisionDetector
from game import GameState


def test_grid():
    """Test Phase 0: Grid system."""
    print("Testing Grid System...")
    grid = Grid()
    
    # Test size
    assert grid.width == 26 and grid.height == 26, "Grid size incorrect"
    
    # Test terrain
    grid.set_terrain(5, 5, TERRAIN['BRICK'])
    assert grid.get_terrain(5, 5) == TERRAIN['BRICK'], "Terrain set/get failed"
    
    # Test passable
    assert not grid.is_passable_by_tank(5, 5), "Brick should not be passable"
    assert grid.is_passable_by_tank(10, 10), "Empty should be passable"
    
    # Test destroy brick
    assert grid.destroy_brick(5, 5), "Brick not destroyed"
    assert grid.get_terrain(5, 5) == TERRAIN['EMPTY'], "Brick not converted to empty"
    
    # Test bounds
    assert not grid.is_valid(26, 26), "Out of bounds not caught"
    assert grid.get_terrain(26, 26) == TERRAIN['EMPTY'], "Out of bounds should return empty"
    
    print("  ✓ Grid system working correctly")


def test_tanks():
    """Test Phase 1B: Tank entity system."""
    print("Testing Tank System...")
    
    tank_basic = Tank(TankType.BASIC, 5, 5)
    assert tank_basic.x == 5 and tank_basic.y == 5, "Tank position incorrect"
    assert tank_basic.hp == 1, "Basic tank HP should be 1"
    assert tank_basic.alive, "Tank should start alive"
    
    tank_armor = Tank(TankType.ARMOR, 10, 10)
    assert tank_armor.hp == 4, "Armor tank HP should be 4"
    
    # Test damage
    tank_basic.take_damage(1)
    assert not tank_basic.alive, "Tank should die from 1 damage"
    
    tank_armor.take_damage(2)
    assert tank_armor.hp == 2, "Armor tank should have 2 HP after 2 damage"
    assert tank_armor.alive, "Armor tank should still be alive"
    
    # Test direction
    tank_basic.set_direction('UP')
    assert tank_basic.direction == DIRECTIONS['UP'], "Direction not set correctly"
    
    # Test shooting
    assert tank_basic.ready_to_shoot(), "Tank should be ready to shoot"
    tank_basic.shoot()
    assert not tank_basic.ready_to_shoot(), "Tank should have cooldown"
    
    print("  ✓ Tank system working correctly")


def test_bullets():
    """Test Phase 1D: Bullet system."""
    print("Testing Bullet System...")
    
    tank = Tank(TankType.BASIC, 5, 5)
    tank.set_direction('UP')
    
    bullet = Bullet(5.0, 5.0, DIRECTIONS['UP'], tank)
    assert bullet.alive, "Bullet should start alive"
    assert bullet.direction == DIRECTIONS['UP'], "Bullet direction incorrect"
    
    # Test movement
    pos = bullet.update(1.0 / 60.0)
    assert pos[1] < 5, "Bullet should move upward"
    
    # Test bullet manager
    manager = BulletManager()
    manager.spawn_bullet(tank)
    assert manager.get_bullet_count() == 1, "Bullet not spawned"
    
    manager.update_bullets(1.0 / 60.0)
    assert manager.get_bullet_count() == 1, "Bullet should still be active"
    
    print("  ✓ Bullet system working correctly")


def test_collision():
    """Test Phase 1C: Collision detection."""
    print("Testing Collision System...")
    
    grid = Grid()
    grid.set_terrain(5, 5, TERRAIN['BRICK'])
    
    tank1 = Tank(TankType.BASIC, 3, 3)
    tank2 = Tank(TankType.BASIC, 5, 5)
    tanks = [tank1, tank2]
    
    bullets = BulletManager()
    
    detector = CollisionDetector(grid, tanks, bullets, (12, 24))
    
    # Test tank vs terrain
    assert detector.can_tank_move_to(tank1, 4, 4), "Should move to empty tile"
    assert not detector.can_tank_move_to(tank1, 5, 5), "Should not move to brick"
    
    # Test tank vs tank
    tank3 = Tank(TankType.BASIC, 4, 4)
    tanks.append(tank3)
    assert not detector.can_tank_move_to(tank1, 4, 4), "Should not move into another tank"
    
    # Test bullet vs terrain
    bullet = Bullet(5.0, 5.0, DIRECTIONS['RIGHT'], tank1)
    result = detector.check_bullet_vs_terrain(bullet)
    assert result == 'brick', "Should detect brick collision"
    
    # Test bullet vs tank
    bullet2 = Bullet(3.0, 3.0, DIRECTIONS['RIGHT'], tank1)
    hit = detector.check_bullet_vs_tank(bullet2)
    assert hit is None, "Bullet should not hit owner"
    
    bullet3 = Bullet(4.99, 4.0, DIRECTIONS['RIGHT'], tank1)
    hit = detector.check_bullet_vs_tank(bullet3)
    assert hit is tank3, "Bullet should hit tank3"
    
    print("  ✓ Collision system working correctly")


def test_game_loop():
    """Test Phase 1E: Game loop."""
    print("Testing Game Loop...")
    
    game = GameState(level=1)
    game.spawn_player()
    game.enemy_pool = [TankType.BASIC, TankType.FAST]
    
    assert game.player is not None, "Player not spawned"
    assert game.tick_count == 0, "Tick count should start at 0"
    
    # Run a few ticks
    input_state = {'direction': 'UP', 'shoot': False}
    game.tick(1.0 / 60.0, input_state)
    
    assert game.tick_count == 1, "Tick count should increment"
    assert game.player.direction_name == 'UP', "Player direction should update"
    
    # Test spawning
    initial_count = len(game.tanks)
    game.check_spawn(10.0)  # Force spawn
    assert len(game.tanks) > initial_count, "Enemy should spawn"
    
    # Test status
    status = game.get_status()
    assert 'level' in status and 'phase' in status, "Status missing keys"
    
    print("  ✓ Game loop working correctly")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*50)
    print("PHASE 0 & PHASE 1 TEST SUITE")
    print("="*50 + "\n")
    
    try:
        test_grid()
        test_tanks()
        test_bullets()
        test_collision()
        test_game_loop()
        
        print("\n" + "="*50)
        print("✓ ALL TESTS PASSED")
        print("="*50 + "\n")
        return True
    
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}\n")
        return False
    except Exception as e:
        print(f"\n✗ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
