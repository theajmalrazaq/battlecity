
GRID_WIDTH = 26
GRID_HEIGHT = 26
TILE_SIZE = 26  # Adjusted for vertical fit (fits comfortably on all screens)


TERRAIN = {
    'EMPTY': 0,      # Passable by tanks and bullets
    'BRICK': 1,      # Destructible by bullets
    'STEEL': 2,      # Indestructible
    'WATER': 3,      # Impassable by tanks; bullets pass through
    'FOREST': 4,     # Passable by tanks; hides tanks; bullets pass through
    'EAGLE': 5       # Base/Goal - destroying it = LOSE
}


TANK_TYPES = {
    'BASIC': {
        'hp': 1,
        'speed': 1.2,         # Slowed (Original 1.5)
        'fire_rate': 3.0,     # 1 bullet per 3 seconds (spec)
        'color': (50, 200, 50),
        'ai_type': 'simple_reflex'
    },
    'FAST': {
        'hp': 1,
        'speed': 2.5,         # Slowed (Original 3.0)
        'fire_rate': 1.5,     # 1 bullet per 1.5 seconds (spec)
        'color': (255, 165, 0),
        'ai_type': 'goal_based'
    },
    'ARMOR': {
        'hp': 4,
        'speed': 0.65,        # Slowed for better balance in Level 2
        'fire_rate': 2.0,
        'color': (200, 100, 50),
        'ai_type': 'model_based_reflex'
    },
    'POWER': {
        'hp': 1,
        'speed': 2.0,         # Restored original speed
        'fire_rate': 0.6,     # Much faster firing (more lethal)
        'color': (255, 50, 255), # Magenta/Purple for Power tanks
        'ai_type': 'utility_based'
    },
    'BOSS': {
        'hp': 10,
        'speed': 2.0,
        'fire_rate': 1.5,
        'color': (200, 0, 0),
        'ai_type': 'adversarial'
    }
}


BULLET_SPEED = 6.0  

SPAWN_POINTS = [
    (0, 0),      # Top-left
    (12, 0),     # Top-center
    (24, 0),     # Top-right
]
PLAYER_SPAWN = (4, 24)
EAGLE_POSITION = (12, 24)
SPAWN_FAIRNESS_DISTANCE = 10 


PLAYER_LIVES = 10
MAX_ACTIVE_TANKS = 4
SPAWN_DELAY = 0.5  
LEVEL_ENEMY_POOL = 20  

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


FPS = 60
TICK_RATE = 60  # Game ticks per second

LEVEL_CONFIG = {
    1: {
        'name': 'Brick Maze',
        'enemy_pool': {'BASIC': 7, 'FAST': 5},
        'max_active': 3, # Adjusted to match PDF Page 5
        'brick_density': 0.35,
        'steel_density': 0.10,
        'forest_density': 0.15,
        'water_density': 0.05,
        'eagle_protection': 2  # layers of brick
    },
    2: {
        'name': 'Steel Fortress',
        'enemy_pool': {'FAST': 4, 'ARMOR': 3, 'POWER': 2}, # Exact pool from PDF Page 5
        'max_active': 3, # Adjusted to match PDF Page 5
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


BOSS_PHASES = {
    1: {'hp_min': 7, 'hp_max': 10, 'depth': 2, 'speed': 0.25, 'fire_rate': 2.0},   # Aggressive
    2: {'hp_min': 3, 'hp_max': 6,  'depth': 3, 'speed': 0.333, 'fire_rate': 1.5},  # Tactical
    3: {'hp_min': 1, 'hp_max': 2,  'depth': 4, 'speed': 0.5, 'fire_rate': 0.8}     # Desperate
}


A_STAR_COSTS = {
    'EMPTY': 1,
    'FOREST': 1,
    'BRICK': 3,        # shoot + wait penalty
    'STEEL': float('inf'),  # blocked
    'WATER': float('inf'),  # blocked
    'TANK': float('inf')    # blocked
}

MINIMAX_HEURISTIC = {
    'player_within_3': 60,
    'player_los': 50,
    'boss_near_steel': 30,
    'player_hp_missing': 20,
    'boss_hp_missing': -40,
    'player_in_forest': -20
}
