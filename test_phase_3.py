"""
Test Suite for Phase 3
Tests: Boss AI Engine, Boss Tank, and Boss Arena Level Generation
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import TERRAIN, GRID_WIDTH, GRID_HEIGHT
from tank import Tank, TankType, BossTank
from game import GameState
from ai.boss import BossAIEngine, BossAgent
from map_generator import LevelGenerator


def test_boss_tank():
    """Test Phase 3B: Boss Tank Implementation."""
    print("Testing Boss Tank...")
    
    boss = BossTank(12, 12)
    
    # Test initial properties
    assert boss.tank_type == TankType.BOSS, "Boss type incorrect"
    assert boss.max_hp == 10, "Boss max HP incorrect"
    assert boss.hp == 10, "Boss initial HP incorrect"
    assert boss.phase == 1, "Boss initial phase incorrect"
    assert boss.color == (200, 0, 0), "Boss color incorrect (should be red)"
    
    # Test phase transitions (spec: Phase 1: 10-7, Phase 2: 6-3, Phase 3: 2-1)
    boss.take_damage(4)  # 10 → 6 HP (Phase 2 threshold)
    assert boss.phase == 2, "Boss should enter Phase 2 at 6 HP"
    assert boss.fire_rate == 1.5, "Phase 2 fire rate should be 1.5s (1 bullet every 1.5 seconds)"
    
    boss.take_damage(4)  # 6 → 2 HP (Phase 3 threshold)
    assert boss.phase == 3, "Boss should enter Phase 3 at 2 HP"
    assert boss.regeneration_active, "Regeneration should be active in Phase 3"
    assert boss.fire_rate == 0.8, "Phase 3 fire rate should be 0.8s (1 bullet every 0.8 seconds)"
    
    print("  ✓ Boss Tank working correctly (phases, HP, stats)")


def test_boss_ai_engine():
    """Test Phase 3A: Minimax AI Engine."""
    print("Testing Boss AI Engine...")
    
    # Create test setup
    boss = BossTank(12, 12)
    from grid import Grid
    grid = Grid()
    
    # Create engine
    engine = BossAIEngine(boss, grid, depth=2)
    
    # Test evaluation heuristic
    from game import GameState
    game_state = GameState(level=1)
    game_state.spawn_player()
    
    # Initial evaluation
    score = engine._evaluate(game_state)
    assert isinstance(score, (int, float)), "Evaluation should return numeric score"
    assert -1000 <= score <= 1000, f"Score out of range: {score}"
    
    # Test move generation
    moves = engine._generate_moves(game_state, is_boss=True)
    assert len(moves) > 0, "Should generate moves for boss"
    assert all(isinstance(m, tuple) and len(m) == 2 for m in moves), "Moves should be (direction, shoot) tuples"
    
    print(f"  ✓ Minimax AI Engine working (depth=2, nodes_explored={engine.nodes_explored}, pruning={engine.cutoffs})")


def test_boss_arena():
    """Test Phase 3C: Boss Arena Level Generation."""
    print("Testing Boss Arena Level...")
    
    level_gen = LevelGenerator('BOSS')
    level_data = level_gen.generate()
    
    assert level_data is not None, "Boss level generation failed"
    assert 'map' in level_data and 'enemy_pool' in level_data, "Missing map or enemy_pool"
    assert level_data.get('is_boss_level'), "Should be marked as boss level"
    
    # Verify map
    arena_map = level_data['map']
    assert len(arena_map) == GRID_HEIGHT, "Map height incorrect"
    assert len(arena_map[0]) == GRID_WIDTH, "Map width incorrect"
    
    # Verify arena has obstacles
    brick_count = sum(row.count(TERRAIN['BRICK']) for row in arena_map)
    steel_count = sum(row.count(TERRAIN['STEEL']) for row in arena_map)
    water_count = sum(row.count(TERRAIN['WATER']) for row in arena_map)
    
    assert brick_count > 0, "Arena should have brick obstacles"
    assert steel_count > 0, "Arena should have steel walls"
    assert water_count > 0, "Arena should have water obstacles"
    
    # Verify enemy pool has exactly 1 boss
    assert len(level_data['enemy_pool']) == 1, "Boss arena should have exactly 1 boss"
    assert level_data['enemy_pool'][0] == TankType.BOSS, "Enemy pool should contain BOSS type"
    
    print(f"  ✓ Boss Arena working correctly")
    print(f"    - Bricks: {brick_count}, Steel: {steel_count}, Water: {water_count}")


def test_boss_agent_integration():
    """Test Phase 3 integration: Boss Agent in game."""
    print("Testing Boss Agent Integration...")
    
    # Create game state for boss level
    game_state = GameState(level='BOSS')
    game_state.spawn_player()
    
    # Manually spawn the boss (since check_spawn() happens during tick)
    if game_state.enemy_pool:
        boss_tank = game_state.spawn_enemy(game_state.enemy_pool[0], x=12, y=12)
    
    assert boss_tank is not None, "Boss should be spawned"
    assert boss_tank.tank_type == TankType.BOSS, "Spawned tank should be BOSS type"
    assert boss_tank in game_state.ai_agents, "Boss should have AI agent"
    
    # Get agent
    agent = game_state.ai_agents[boss_tank]
    assert agent is not None, "Boss agent should be created"
    
    # Test agent decision
    agent.decide(0.016, game_state)  # ~60 FPS
    
    # Boss should have made a move or decision
    assert boss_tank.direction_name in ['UP', 'DOWN', 'LEFT', 'RIGHT', 'NONE'], "Boss should have valid direction"
    
    print("  ✓ Boss Agent integration working")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("PHASE 3 TEST SUITE")
    print("="*60 + "\n")
    
    try:
        test_boss_tank()
        test_boss_ai_engine()
        test_boss_arena()
        test_boss_agent_integration()
        
        print("\n" + "="*60)
        print("ALL PHASE 3 TESTS PASSED ✓")
        print("="*60)
        print("\nPhase 3 Implementation Complete:")
        print("  - 3A: Minimax with Alpha-Beta Pruning ✓")
        print("  - 3B: Boss Tank with Phase Mechanics ✓")
        print("  - 3C: Boss Arena Level Generation ✓")
        print("\nRun: python main.py --level BOSS")
        print("="*60 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
