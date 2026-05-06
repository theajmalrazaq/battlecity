"""
Battle City Configuration - Global Constants
AL2002 Artificial Intelligence Lab | Spring 2026
"""

# ============ GRID & MAP SYSTEM ============
GRID_WIDTH = 26
GRID_HEIGHT = 26
TILE_SIZE = 30  # pixels (for rendering)

# ============ TERRAIN TYPES ============
TERRAIN = {
    'EMPTY': 0,      # Passable by tanks and bullets
    'BRICK': 1,      # Destructible by bullets
    'STEEL': 2,      # Indestructible
    'WATER': 3,      # Impassable by tanks; bullets pass through
    'FOREST': 4,     # Passable by tanks; hides tanks; bullets pass through
    'EAGLE': 5       # Base/Goal - destroying it = LOSE
}

# ============ TANK PROPERTIES ============
TANK_TYPES = {
    'BASIC': {
        'hp': 1,
        'speed': 0.25,        # 1 tile per 4 ticks
        'fire_rate': 3.0,     # 1 bullet per 3 seconds
        'color': (50, 200, 50),
        'ai_type': 'simple_reflex'
    },
    'FAST': {
        'hp': 1,
        'speed': 0.5,         # 1 tile per 2 ticks
        'fire_rate': 1.5,     # 1 bullet per 1.5 seconds
        'color': (255, 165, 0),
        'ai_type': 'goal_based'
    },
    'ARMOR': {
        'hp': 4,
        'speed': 0.333,       # 1 tile per 3 ticks
        'fire_rate': 2.0,     # 1 bullet per 2 seconds
        'color': (200, 100, 50),
        'ai_type': 'model_based_reflex'
    },
    'BOSS': {
        'hp': 10,
        'speed': 0.25,        # Varies by phase
        'fire_rate': 2.0,     # Varies by phase (1/2s, 1/1.5s, 1/0.8s)
        'color': (200, 0, 0),
        'ai_type': 'adversarial'
    }
}

# ============ BULLET PROPERTIES ============
BULLET_SPEED = 1.0  # 2x tank movement speed (travels 2 tiles per tick)

# ============ SPAWN SYSTEM ============
SPAWN_POINTS = [
    (0, 0),      # Top-left
    (12, 0),     # Top-center
    (24, 0)      # Top-right
]
PLAYER_SPAWN = (4, 24)
EAGLE_POSITION = (12, 24)
SPAWN_FAIRNESS_DISTANCE = 10  # Manhattan distance

# ============ GAME RULES ============
PLAYER_LIVES = 10
MAX_ACTIVE_TANKS = 3
SPAWN_DELAY = 1.0  # seconds between spawns
LEVEL_ENEMY_POOL = 20  # Total enemies per level

# ============ DIRECTIONS ============
DIRECTIONS = {
    'UP': (0, -1),
    'DOWN': (0, 1),
    'LEFT': (-1, 0),
    'RIGHT': (1, 0),
    'NONE': (0, 0)
}

# ============ GAME STATES ============
GAME_STATE = {
    'PLAYING': 'playing',
    'PAUSED': 'paused',
    'LEVEL_WIN': 'level_win',
    'GAME_OVER': 'game_over'
}

# ============ FPS & TIMING ============
FPS = 60
TICK_RATE = 60  # Game ticks per second

# ============ LEVEL CONFIGURATIONS ============
LEVEL_CONFIG = {
    1: {
        'name': 'Brick Maze',
        'enemy_pool': {'BASIC': 7, 'FAST': 5},
        'max_active': 3,
        'brick_density': 0.35,
        'steel_density': 0.10,
        'forest_density': 0.15,
        'water_density': 0.05,
        'eagle_protection': 2  # layers of brick
    },
    2: {
        'name': 'Steel Fortress',
        'enemy_pool': {'FAST': 4, 'ARMOR': 3, 'BASIC': 2},
        'max_active': 3,
        'brick_density': 0.25,
        'steel_density': 0.20,
        'forest_density': 0.10,
        'water_density': 0.10,
        'eagle_protection': 2
    },
    'BOSS': {
        'name': 'Tank Commander',
        'enemy_pool': {'BOSS': 1},
        'max_active': 1,
        'arena_size': 12,  # 12x12
        'brick_density': 0.15,
        'steel_density': 0.20,
        'forest_density': 0.05,
        'water_density': 0.05
    }
}

# ============ BOSS PHASES ============
BOSS_PHASES = {
    1: {'hp_min': 7, 'hp_max': 10, 'depth': 2, 'speed': 0.25, 'fire_rate': 2.0},
    2: {'hp_min': 3, 'hp_max': 6, 'depth': 3, 'speed': 0.333, 'fire_rate': 1.5},
    3: {'hp_min': 1, 'hp_max': 2, 'depth': 4, 'speed': 0.5, 'fire_rate': 0.8}
}

# ============ A* PATHFINDING COSTS ============
A_STAR_COSTS = {
    'EMPTY': 1,
    'FOREST': 1,
    'BRICK': 3,        # shoot + wait penalty
    'STEEL': float('inf'),  # blocked
    'WATER': float('inf'),  # blocked
    'TANK': float('inf')    # blocked
}

# ============ MINIMAX HEURISTIC SCORES ============
MINIMAX_HEURISTIC = {
    'player_within_3': 60,
    'player_los': 50,
    'boss_near_steel': 30,
    'player_hp_missing': 20,
    'boss_hp_missing': -40,
    'player_in_forest': -20
}
