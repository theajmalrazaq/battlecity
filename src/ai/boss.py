

import copy
from enum import Enum


class MoveType(Enum):
   
    MOVE_UP = 'UP'
    MOVE_DOWN = 'DOWN'
    MOVE_LEFT = 'LEFT'
    MOVE_RIGHT = 'RIGHT'
    SHOOT = 'SHOOT'
    WAIT = 'WAIT'


class BossAIEngine:
   

    def __init__(self, boss_tank, grid, player_pos=None, depth=4):
        
        self.boss_tank = boss_tank
        self.grid = grid
        self.player_pos = player_pos
        self.max_depth = depth
        self.nodes_explored = 0
        self.nodes_standard = 0
        self.nodes_pruned = 0
        self.cutoffs = 0  # Alpha-beta pruning cutoffs

    def decide(self, game_state):
       
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
            
            # Generate and ORDER moves (Combat actions first for faster pruning)
            possible_moves = self._generate_moves(game_state, is_boss=True)
            # Order: (SHOOT=True moves first, then moves towards player)
            possible_moves.sort(key=lambda m: (m[1], self._is_towards_player(m[0])), reverse=True)
            
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

    def benchmark_pruning(self, game_state):
        
        with_pruning = self._root_search_for_benchmark(game_state, use_pruning=True)
        without_pruning = self._root_search_for_benchmark(game_state, use_pruning=False)

        pruned_nodes = with_pruning['nodes']
        standard_nodes = without_pruning['nodes']
        speedup = (standard_nodes / pruned_nodes) if pruned_nodes > 0 else float('inf')

        return {
            'with_pruning': with_pruning,
            'without_pruning': without_pruning,
            'speedup': speedup,
        }

    def _root_search_for_benchmark(self, game_state, use_pruning):
        
        if use_pruning:
            self.nodes_pruned = 0
        else:
            self.nodes_standard = 0
        self.cutoffs = 0

        if not game_state.player:
            return {'nodes': 0, 'best_move': ('NONE', False), 'cutoffs': 0}

        orig_boss_x, orig_boss_y = self.boss_tank.x, self.boss_tank.y
        orig_player_x, orig_player_y = game_state.player.x, game_state.player.y

        best_score = float('-inf')
        best_move = ('NONE', False)
        alpha = float('-inf')
        beta = float('inf')

        possible_moves = self._generate_moves(game_state, is_boss=True)
        possible_moves.sort(key=lambda m: (m[1], self._is_towards_player(m[0])), reverse=True)

        for move in possible_moves:
            new_state = self._simulate_move(game_state, move, is_boss=True)
            score = self._minimax(
                new_state,
                self.max_depth - 1,
                alpha,
                beta,
                is_maximizing=False,
                use_pruning=use_pruning,
            )

            # Restore positions after each candidate evaluation
            self.boss_tank.x, self.boss_tank.y = orig_boss_x, orig_boss_y
            game_state.player.x, game_state.player.y = orig_player_x, orig_player_y

            if score > best_score:
                best_score = score
                best_move = move

            if use_pruning:
                alpha = max(alpha, score)
                if beta <= alpha:
                    break

        # Final restore guard
        self.boss_tank.x, self.boss_tank.y = orig_boss_x, orig_boss_y
        game_state.player.x, game_state.player.y = orig_player_x, orig_player_y

        nodes = self.nodes_pruned if use_pruning else self.nodes_standard
        return {'nodes': nodes, 'best_move': best_move, 'cutoffs': self.cutoffs}

    def _minimax(self, game_state, depth, alpha, beta, is_maximizing, use_pruning=True):
        
        if use_pruning:
            self.nodes_pruned += 1
        else:
            self.nodes_standard += 1
            
        # Terminal node or depth limit
        if depth == 0 or self._is_terminal(game_state):
            return self._evaluate(game_state)
        
        if is_maximizing:
            # Boss's turn - maximize score
            max_eval = float('-inf')
            moves = self._generate_moves(game_state, is_boss=True)
            
            for move in moves:
                new_state = self._simulate_move(game_state, move, is_boss=True)
                eval_score = self._minimax(new_state, depth - 1, alpha, beta, is_maximizing=False, use_pruning=use_pruning)
                max_eval = max(max_eval, eval_score)
                
                if use_pruning:
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
                eval_score = self._minimax(new_state, depth - 1, alpha, beta, is_maximizing=True, use_pruning=use_pruning)
                min_eval = min(min_eval, eval_score)
                
                if use_pruning:
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        self.cutoffs += 1
                        break  # Beta cutoff
            
            return min_eval

    def _evaluate(self, game_state):
       
        score = 0
        
        # Boss dead = worst possible position
        if not self.boss_tank.alive:
            return -1000
        
        # Player dead = best possible position
        if not game_state.player or not game_state.player.alive:
            return 1000
        
        player = game_state.player
        
        # Factor 1: Player within 3 tiles (+60) — high threat proximity
        dist_to_player = abs(self.boss_tank.x - player.x) + abs(self.boss_tank.y - player.y)
        if dist_to_player <= 3:
            score += 60
        
        # Factor 2: Player in line-of-sight (+50) — can shoot immediately
        if self._can_see(self.boss_tank, player):
            score += 50
        
        # Factor 3: Boss adjacent to steel wall (+30) — cover bonus
        if self._is_adjacent_to_steel():
            score += 30
        
        # Factor 4: Player HP missing (+20 per missing HP)
        score += (player.max_hp - player.hp) * 20
        
        # Factor 5: Boss HP missing (-40 per missing HP)
        score -= (self.boss_tank.max_hp - self.boss_tank.hp) * 40
        
        # Factor 6: Player in forest tile (-20) — uncertain visibility
        from config import TERRAIN
        player_terrain = game_state.grid.get_terrain(int(player.x), int(player.y))
        if player_terrain == TERRAIN['FOREST']:
            score -= 20
        
        # Factor 7: Facing player (+40) — proactive combat
        dx, dy = self.boss_tank.direction
        is_facing = False
        if dx > 0 and player.x > self.boss_tank.x and player.y == self.boss_tank.y: is_facing = True
        elif dx < 0 and player.x < self.boss_tank.x and player.y == self.boss_tank.y: is_facing = True
        elif dy > 0 and player.y > self.boss_tank.y and player.x == self.boss_tank.x: is_facing = True
        elif dy < 0 and player.y < self.boss_tank.y and player.x == self.boss_tank.x: is_facing = True
        
        if is_facing:
            score += 100  # Directional awareness
            if self.boss_tank.ready_to_shoot():
                score += 150  # URGENCY: Buffed from 70 to 150 to ensure immediate attack
        
        # Factor 8: Predictive Intercept (reward being on same axis as player)
        if self.boss_tank.x == player.x or self.boss_tank.y == player.y:
            score += 40
        
        return max(-1000, min(1000, score))

    def _generate_moves(self, game_state, is_boss):
       
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
       
            moves.append((direction, False))
            moves.append((direction, True))  # Rotate + shoot
        
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
     
        if not self.boss_tank.alive:
            return True
        if not game_state.player or not game_state.player.alive:
            return True
        return False

    def _can_see(self, tank1, tank2):
      
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

    def _is_adjacent_to_steel(self):
       
        from config import TERRAIN
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = self.boss_tank.x + dx, self.boss_tank.y + dy
            if self.grid.is_valid(nx, ny) and self.grid.get_terrain(nx, ny) == TERRAIN['STEEL']:
                return True
        return False

    def _is_towards_player(self, direction):
      
        if direction == 'NONE' or not self.player_pos:
            return False
        
        from config import DIRECTIONS
        dx, dy = DIRECTIONS[direction]
        target_x, target_y = self.boss_tank.x + dx, self.boss_tank.y + dy
        
        old_dist = abs(self.boss_tank.x - self.player_pos[0]) + abs(self.boss_tank.y - self.player_pos[1])
        new_dist = abs(target_x - self.player_pos[0]) + abs(target_y - self.player_pos[1])
        
        return new_dist < old_dist

    def _is_enclosed(self, tank):
      
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
   
    
    def __init__(self, tank, grid, eagle_pos=None):
       
        self.tank = tank
        self.grid = grid
        self.eagle_pos = eagle_pos or (12, 24)
        self.ai_engine = BossAIEngine(tank, grid, depth=2)  # Phase 1: depth 2 (PDF spec)
        self.phase = 1  # 1, 2, or 3
        self.last_phase_update = 0.0
        self.pruning_stats_timer = 0.0
    
    def decide(self, dt, game_state):
       
        # Update phase based on HP
        self.last_phase_update += dt
        self.pruning_stats_timer += dt
        if self.last_phase_update >= 0.5:  # Check every 0.5 seconds
            self._update_phase()
            self.last_phase_update = 0.0

        # Print pruning benchmark periodically during boss play
        if self.pruning_stats_timer >= 1.0:
            stats = self.ai_engine.benchmark_pruning(game_state)
            with_nodes = stats['with_pruning']['nodes']
            without_nodes = stats['without_pruning']['nodes']
            speedup = stats['speedup']
            cutoffs = stats['with_pruning']['cutoffs']
            print(
                f"[Boss Pruning] with={with_nodes} without={without_nodes} "
                f"speedup={speedup:.2f}x cutoffs={cutoffs}"
            )
            self.pruning_stats_timer = 0.0
        
        # PERFORMANCE: Decision cycle buffed to 0.05s for "Twitch" reactions
        self.decision_timer = getattr(self, 'decision_timer', 0.0) + dt
        if self.decision_timer < 0.05:
            # Continue current direction but still check reactive shooting
            self._check_shooting(game_state)
            return
        
        self.decision_timer = 0.0
        
        # --- COMBINED DECISION: use Minimax for both movement and shooting ---
        # This fixes the "only shooting down" glitch by following the search results
        move_result = self.ai_engine.decide(game_state)
        
        if move_result:
            direction, should_shoot = move_result
            
            # Apply movement
            if direction != 'NONE':
                self.tank.set_direction(direction)
            
            # Apply shooting (Minimax's strategic choice)
            if should_shoot and self.tank.ready_to_shoot():
                self.tank.shoot()
            
        # --- REACTIVE BACKUP: Always shoot if player is in LOS (Reflex) ---
        self._check_shooting(game_state)

    def _check_shooting(self, game_state):
        """Standard shooting logic for Boss."""
        if not self.tank.ready_to_shoot():
            return
        
        player = game_state.player
        if not player or not player.alive:
            return
        
        # Always shoot if player is in line-of-sight
        if self.ai_engine._can_see(self.tank, player):
            self.tank.shoot()
            return
        
        # Phase 3 (Desperate): also shoot randomly even without LOS
        if self.phase == 3:
            import random
            if random.random() < 0.2:
                self.tank.shoot()
    
    def _update_phase(self):
      
        old_phase = self.phase
        
        # Determine phase and stats from current HP
        if self.tank.hp >= 7:
            new_phase = 1
            new_depth = 2
            new_speed = 1.5   # Phase 1: Slow
            new_fire = 2.0    # Phase 1: 1 bullet per 2s
        elif self.tank.hp >= 3:
            new_phase = 2
            new_depth = 3
            new_speed = 2.5   # Phase 2: Medium
            new_fire = 1.5    # Phase 2: 1 bullet per 1.5s
        else:
            new_phase = 3
            new_depth = 4
            new_speed = 3.5   # Phase 3: Fast
            new_fire = 0.8    # Phase 3: 1 bullet per 0.8s
        
       
        new_phase = max(old_phase, new_phase)
        
   
        self.phase = new_phase
        self.tank.phase = new_phase  
        self.ai_engine.max_depth = new_depth
        self.tank.speed = new_speed
        self.tank.fire_rate = new_fire
        
        if new_phase != old_phase:
            p_names = {1: "AGGRESSIVE", 2: "TACTICAL", 3: "DESPERATE"}
            print(f"Boss entering Phase {new_phase} - {p_names.get(new_phase)} MODE! (Depth {new_depth})")

