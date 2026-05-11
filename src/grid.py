
from config import GRID_WIDTH, GRID_HEIGHT, TERRAIN


class Grid:
   

    def __init__(self):
        
        self.width = GRID_WIDTH
        self.height = GRID_HEIGHT
        self.tiles = [[TERRAIN['EMPTY'] for _ in range(self.width)] for _ in range(self.height)]

    def set_terrain(self, x, y, terrain_type):
     
        if self.is_valid(x, y):
            self.tiles[y][x] = terrain_type
        else:
            raise ValueError(f"Invalid coordinates: ({x}, {y})")

    def get_terrain(self, x, y):
   
        if self.is_valid(x, y):
            return self.tiles[y][x]
        return TERRAIN['EMPTY']  # Out of bounds = empty

    def is_valid(self, x, y):
       
        return 0 <= x < self.width and 0 <= y < self.height

    def is_passable_by_tank(self, x, y):
    
        if not self.is_valid(x, y):
            return False
        terrain = self.get_terrain(x, y)
        # Tanks can move through EMPTY and FOREST
        return terrain in [TERRAIN['EMPTY'], TERRAIN['FOREST']]

    def is_passable_by_bullet(self, x, y):
        
        if not self.is_valid(x, y):
            return False
        terrain = self.get_terrain(x, y)
  
        return terrain in [TERRAIN['EMPTY'], TERRAIN['FOREST'], TERRAIN['WATER']]

    def is_solid(self, x, y):

        if not self.is_valid(x, y):
            return True  # Out of bounds = solid
        terrain = self.get_terrain(x, y)
        return terrain in [TERRAIN['BRICK'], TERRAIN['STEEL']]

    def destroy_brick(self, x, y):
      
        if self.is_valid(x, y) and self.get_terrain(x, y) == TERRAIN['BRICK']:
            self.set_terrain(x, y, TERRAIN['EMPTY'])
            return True
        return False

    def get_neighbors(self, x, y, include_diagonals=False):
       
        if include_diagonals:
            offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        else:
            offsets = [(0, -1), (0, 1), (-1, 0), (1, 0)]  # UP, DOWN, LEFT, RIGHT

        neighbors = []
        for dx, dy in offsets:
            nx, ny = x + dx, y + dy
            if self.is_valid(nx, ny):
                neighbors.append((nx, ny))
        return neighbors

    def clear(self):
      
        self.tiles = [[TERRAIN['EMPTY'] for _ in range(self.width)] for _ in range(self.height)]

    def __repr__(self):
       
        return f"Grid({self.width}x{self.height})"

    def get_grid_state(self):
    
        return [row[:] for row in self.tiles]
