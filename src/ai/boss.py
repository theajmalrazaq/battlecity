"""
Boss AI - Adversarial Engine with Minimax & Alpha-Beta Pruning
Phase 3A: Adversarial AI - Boss Tank Decision Logic

Implements:
- Minimax algorithm with game tree search
- Alpha-Beta pruning for optimization
- Evaluation heuristic function
- Depth-limited search (4-6 levels)
- Move generation from current board state
"""

import copy
from enum import Enum


class MoveType(Enum):
    """Possible moves the boss can make."""
    MOVE_UP = 'UP'
    MOVE_DOWN = 'DOWN'
    MOVE_LEFT = 'LEFT'
    MOVE_RIGHT = 'RIGHT'
    SHOOT = 'SHOOT'
    WAIT = 'WAIT'


class BossAIEngine:
    """
    Minimax-based adversarial AI for Boss Tank.
    Uses alpha-beta pruning to optimize search.
    """

    def __init__(self, boss_tank, grid, player_pos=None, depth=4):
        """
        Initialize Boss AI Engine.
        
        Args:
            boss_tank: Tank object (the boss)
            grid: Grid object for pathfinding
            player_pos: Player position for heuristic
            depth: Search depth (4-6 recommended)
        """
        self.boss_tank = boss_tank
        self.grid = grid
        self.player_pos = player_pos
        self.max_depth = depth
        self.nodes_explored = 0
        self.cutoffs = 0  # Alpha-beta pruning cutoffs

    def decide(self, game_state):
        """
        Make optimal boss decision using minimax with alpha-beta pruning.
        
        Args:
            game_state: GameState object
        
        Returns:
            Best action: (direction, shoot) tuple
        """
        self.nodes_explored = 0
        self.cutoffs = 0
        self.player_pos = game_state.player.get_position() if game_state.player else None
        
        # Save original positions (to prevent modification during simulation)
        orig_boss_x, orig_boss_y = self.boss_tank.x, self.boss_tank.y
        orig_player_x, orig_player_y = game_state.player.x, game_state.player.y
        
        try:
            # Minimax search with alpha-beta pruning
            best_score = float('-inf')
            best_move = ('NONE', False)
            
            alpha = float('-inf')
            beta = float('inf')
            
            # Generate possible moves
            possible_moves = self._generate_moves(game_state, is_boss=True)
            
            for move in possible_moves:
                # Simulate move (this will modify tank positions temporarily)
                new_state = self._simulate_move(game_state, move, is_boss=True)
                
                # Score the move (opponent's turn - minimizing)
                score = self._minimax(new_state, self.max_depth - 1, alpha, beta, is_maximizing=False)
                
                # Restore positions after evaluation
                self.boss_tank.x, self.boss_tank.y = orig_boss_x, orig_boss_y
                game_state.player.x, game_state.player.y = orig_player_x, orig_player_y
                
                if score > best_score:
                    best_score = score
                    best_move = move
                
                alpha = max(alpha, score)
                if beta <= alpha:
                    break  # Beta cutoff
            
            return best_move
        finally:
            # Ensure positions are restored
            self.boss_tank.x, self.boss_tank.y = orig_boss_x, orig_boss_y
            game_state.player.x, game_state.player.y = orig_player_x, orig_player_y

    def _minimax(self, game_state, depth, alpha, beta, is_maximizing):
        """
        Minimax algorithm with alpha-beta pruning.
        
        Args:
            game_state: Current game state
            depth: Remaining search depth
            alpha: Best score for maximizer
            beta: Best score for minimizer
            is_maximizing: True if maximizing (boss's turn), False if minimizing (player's turn)
        
        Returns:
            Evaluation score of current position
        """
        self.nodes_explored += 1
        
        # Terminal node or depth limit
        if depth == 0 or self._is_terminal(game_state):
            return self._evaluate(game_state)
        
        if is_maximizing:
            # Boss's turn - maximize score
            max_eval = float('-inf')
            moves = self._generate_moves(game_state, is_boss=True)
            
            for move in moves:
                new_state = self._simulate_move(game_state, move, is_boss=True)
                eval_score = self._minimax(new_state, depth - 1, alpha, beta, is_maximizing=False)
                max_eval = max(max_eval, eval_score)
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    self.cutoffs += 1
                    break  # Alpha cutoff
            
            return max_eval
        else:
            # Player's turn - minimize score
            min_eval = float('inf')
            moves = self._generate_moves(game_state, is_boss=False)
            
            for move in moves:
                new_state = self._simulate_move(game_state, move, is_boss=False)
                eval_score = self._minimax(new_state, depth - 1, alpha, beta, is_maximizing=True)
                min_eval = min(min_eval, eval_score)
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    self.cutoffs += 1
                    break  # Beta cutoff
            
            return min_eval

    def _evaluate(self, game_state):
        """
        Evaluation heuristic - score the current board position.
        
        Higher score = better for boss.
        Lower score = worse for boss (better for player).
        
        Factors:
        - Distance to player (closer = better for boss)
        - Distance to eagle (closer = better for boss)
        - Player HP (lower = better for boss)
        - Boss HP (higher = better for boss)
        - Player line-of-sight (can see = better for boss)
        
        Args:
            game_state: GameState object
        
        Returns:
            Score (-1000 to +1000 range)
        """
        score = 0
        
        # Boss health (max 10 HP)
        if self.boss_tank.alive:
            score += self.boss_tank.hp * 30  # +30 per HP point
        else:
            return -1000  # Boss dead = worst position
        
        # Player existence
        if not game_state.player or not game_state.player.alive:
            return 1000  # Player dead = best position
        
        player = game_state.player
        
        # Distance to player (closer = better, but not too punishing if far)
        dist_to_player = abs(self.boss_tank.x - player.x) + abs(self.boss_tank.y - player.y)
        if dist_to_player < 3:
            score += 100  # Very close, good for attacking
        elif dist_to_player < 8:
            score += 50   # Medium distance
        else:
            score -= 20   # Too far away
        
        # Distance to eagle (closer = better)
        dist_to_eagle = abs(self.boss_tank.x - 12) + abs(self.boss_tank.y - 24)
        if dist_to_eagle < 5:
            score += 80   # Close to eagle, can destroy it
        
        # Line-of-sight to player (can attack = better)
        if self._can_see(self.boss_tank, player):
            score += 60
        
        # Player HP (lower = better for boss)
        score += (10 - player.hp) * 20  # Reward damaging player
        
        # Boss HP loss penalty (try to stay healthy)
        score -= (10 - self.boss_tank.hp) * 25
        
        # Position safety (stay away from corners/dead ends if at low HP)
        if self.boss_tank.hp <= 3:
            # Prefer open areas when low health
            if self._is_enclosed(self.boss_tank):
                score -= 50
        
        return max(-1000, min(1000, score))  # Clamp to reasonable range

    def _generate_moves(self, game_state, is_boss):
        """
        Generate all legal moves from current state.
        
        For boss: All direction + shoot combinations
        For player: Simulated moves (heuristic-based, not reading actual input)
        
        Args:
            game_state: GameState object
            is_boss: True if generating boss moves, False for player moves
        
        Returns:
            List of (direction, shoot) tuples
        """
        moves = []
        
        if is_boss:
            tank = self.boss_tank
        else:
            tank = game_state.player
        
        if not tank or not tank.alive:
            return [('NONE', False)]
        
        # Direction moves
        directions = ['UP', 'DOWN', 'LEFT', 'RIGHT', 'NONE']
        
        for direction in directions:
            # Can this tank move in this direction?
            if direction == 'NONE':
                moves.append((direction, False))
                moves.append((direction, True))  # Shoot while idle
            else:
                # Check if move is valid
                if self._can_move(tank, direction, game_state):
                    moves.append((direction, False))
                    moves.append((direction, True))  # Move + shoot
        
        return moves

    def _can_move(self, tank, direction, game_state):
        """Check if tank can move in direction."""
        from config import DIRECTIONS
        
        if direction == 'NONE':
            return True
        
        dx, dy = DIRECTIONS[direction]
        next_x = tank.x + dx
        next_y = tank.y + dy
        
        # Check if in bounds
        if not self.grid.is_valid(next_x, next_y):
            return False
        
        # Check if passable
        if not self.grid.is_passable_by_tank(next_x, next_y):
            return False
        
        # Check for other tanks
        for other in game_state.tanks:
            if other is not tank and other.alive:
                if other.x == next_x and other.y == next_y:
                    return False
        
        return True

    def _simulate_move(self, game_state, move, is_boss):
        """
        Simulate a move and return new game state (shallow copy).
        
        Args:
            game_state: GameState object
            move: (direction, shoot) tuple
            is_boss: True if simulating boss move
        
        Returns:
            New game state after move
        """
        # Create shallow copy of state
        new_state = copy.copy(game_state)
        
        # Don't modify original tank - just return the state
        # The minimax evaluation will work with the original positions
        tank = self.boss_tank if is_boss else game_state.player
        direction, should_shoot = move
        
        # Apply movement (position will be restored after evaluation in decide())
        if direction != 'NONE' and self._can_move(tank, direction, game_state):
            from config import DIRECTIONS
            dx, dy = DIRECTIONS[direction]
            tank.x += dx
            tank.y += dy
        
        return new_state

    def _is_terminal(self, game_state):
        """Check if this is a terminal state (game over)."""
        if not self.boss_tank.alive:
            return True
        if not game_state.player or not game_state.player.alive:
            return True
        return False

    def _can_see(self, tank1, tank2):
        """Check if tank1 can see tank2 (line-of-sight)."""
        x1, y1 = tank1.x, tank1.y
        x2, y2 = tank2.x, tank2.y
        
        # Same row
        if y1 == y2:
            min_x, max_x = min(x1, x2), max(x1, x2)
            for x in range(min_x + 1, max_x):
                if self.grid.is_solid(x, y1):
                    return False
            return True
        
        # Same column
        if x1 == x2:
            min_y, max_y = min(y1, y2), max(y1, y2)
            for y in range(min_y + 1, max_y):
                if self.grid.is_solid(x1, y):
                    return False
            return True
        
        return False

    def _is_enclosed(self, tank):
        """Check if tank is enclosed (surrounded by walls/tanks)."""
        from config import DIRECTIONS
        
        enclosed_count = 0
        for direction in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
            dx, dy = DIRECTIONS[direction]
            next_x, next_y = tank.x + dx, tank.y + dy
            
            if not self.grid.is_valid(next_x, next_y):
                enclosed_count += 1
            elif not self.grid.is_passable_by_tank(next_x, next_y):
                enclosed_count += 1
        
        return enclosed_count >= 3  # 3+ sides blocked


class BossAgent:
    """Wrapper agent for boss tank using minimax AI."""
    
    def __init__(self, tank, grid, eagle_pos=None):
        """Initialize boss agent."""
        self.tank = tank
        self.grid = grid
        self.eagle_pos = eagle_pos or (12, 24)
        self.ai_engine = BossAIEngine(tank, grid, depth=4)
        self.phase = 1  # 1, 2, or 3
        self.last_phase_update = 0.0
    
    def decide(self, dt, game_state):
        """
        Make decision using minimax AI.
        Update phase based on health.
        
        Args:
            dt: Delta time
            game_state: GameState object
        """
        # Update phase based on HP
        self.last_phase_update += dt
        if self.last_phase_update >= 0.5:  # Check every 0.5 seconds
            self._update_phase()
            self.last_phase_update = 0.0
        
        # Get best move from minimax
        direction, shoot = self.ai_engine.decide(game_state)
        
        # Apply move
        self.tank.set_direction(direction)
        if shoot and self.tank.ready_to_shoot():
            self.tank.shoot()
    
    def _update_phase(self):
        """Update boss phase based on current HP and adjust minimax depth."""
        old_phase = self.phase
        
        if self.tank.hp >= 7:
            self.phase = 1  # Aggressive (10-7 HP)
            self.ai_engine.max_depth = 2  # Phase 1: depth 2
        elif self.tank.hp >= 3:
            self.phase = 2  # Tactical (6-3 HP)
            self.ai_engine.max_depth = 3  # Phase 2: depth 3
        else:
            self.phase = 3  # Desperate (2-1 HP)
            self.ai_engine.max_depth = 4  # Phase 3: depth 4
        
        if old_phase != self.phase:
            print(f"Boss entering Phase {self.phase}!")
