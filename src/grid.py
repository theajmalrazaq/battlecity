"""
Grid System - 26x26 Tile-Based Game World
Phase 0: Grid & Coordinate System
"""

from config import GRID_WIDTH, GRID_HEIGHT, TERRAIN


class Grid:
    """
    Represents the 26x26 game world.
    Each tile has a terrain type (0-5).
    Coordinate system: (0,0) is top-left. X increases right, Y increases down.
    """

    def __init__(self):
        """Initialize empty grid with all tiles as EMPTY (0)."""
        self.width = GRID_WIDTH
        self.height = GRID_HEIGHT
        self.tiles = [[TERRAIN['EMPTY'] for _ in range(self.width)] for _ in range(self.height)]

    def set_terrain(self, x, y, terrain_type):
        """Set a tile's terrain type. Validates coordinates."""
        if self.is_valid(x, y):
            self.tiles[y][x] = terrain_type
        else:
            raise ValueError(f"Invalid coordinates: ({x}, {y})")

    def get_terrain(self, x, y):
        """Get terrain type at (x, y). Returns EMPTY if out of bounds."""
        if self.is_valid(x, y):
            return self.tiles[y][x]
        return TERRAIN['EMPTY']  # Out of bounds = empty

    def is_valid(self, x, y):
        """Check if coordinates are within grid bounds."""
        return 0 <= x < self.width and 0 <= y < self.height

    def is_passable_by_tank(self, x, y):
        """Check if a tank can move to this tile."""
        if not self.is_valid(x, y):
            return False
        terrain = self.get_terrain(x, y)
        # Tanks can move through EMPTY and FOREST
        return terrain in [TERRAIN['EMPTY'], TERRAIN['FOREST']]

    def is_passable_by_bullet(self, x, y):
        """Check if a bullet can pass through this tile."""
        if not self.is_valid(x, y):
            return False
        terrain = self.get_terrain(x, y)
        # Bullets pass through EMPTY, FOREST, and WATER (bullets fly over water)
        # Blocked by: BRICK (destroys it), STEEL, EAGLE
        # Original Battle City rules: water stops tanks but NOT bullets
        return terrain in [TERRAIN['EMPTY'], TERRAIN['FOREST'], TERRAIN['WATER']]

    def is_solid(self, x, y):
        """Check if tile is solid (blocks bullets/vision)."""
        if not self.is_valid(x, y):
            return True  # Out of bounds = solid
        terrain = self.get_terrain(x, y)
        return terrain in [TERRAIN['BRICK'], TERRAIN['STEEL']]

    def destroy_brick(self, x, y):
        """
        Destroy a brick wall at (x, y).
        Permanently replaces it with EMPTY tile.
        This is a one-way operation (key game mechanic).
        """
        if self.is_valid(x, y) and self.get_terrain(x, y) == TERRAIN['BRICK']:
            self.set_terrain(x, y, TERRAIN['EMPTY'])
            return True
        return False

    def get_neighbors(self, x, y, include_diagonals=False):
        """
        Get all valid neighboring tiles.
        Args:
            x, y: Center tile
            include_diagonals: If True, includes 8 neighbors; else 4 cardinal neighbors
        Returns:
            List of (x, y) tuples for valid neighbors
        """
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
        """Reset grid to all EMPTY tiles."""
        self.tiles = [[TERRAIN['EMPTY'] for _ in range(self.width)] for _ in range(self.height)]

    def __repr__(self):
        """String representation of grid (for debugging)."""
        return f"Grid({self.width}x{self.height})"

    def get_grid_state(self):
        """Return a copy of the grid state (for agents/pathfinding)."""
        return [row[:] for row in self.tiles]
