# Battle City Game Guide

## How to Play

### CONTROLS
- **Arrow Keys** = Move your tank (UP, DOWN, LEFT, RIGHT)
- **Z or Ctrl** = Shoot a bullet
- **Space** = Pause/Resume game
- **ESC** = Quit game

### GAME OBJECTIVE
Protect the **EAGLE** (yellow square at the bottom center) from enemy tanks. Destroy all enemies to win the level.

### VISUAL GUIDE

**TANKS:**
- **Large gray/white circle with yellow border** = YOUR TANK (player)
- **Colored circles** = Enemy tanks
  - Green circles = BASIC tanks (slow, weak)
  - Orange circles = FAST tanks (quick, fragile)
  - Brown circles = ARMOR tanks (slow, tough - requires multiple hits)

**TERRAIN:**
- **Orange tiles** = Brick walls (destroyable by bullets)
- **Cyan tiles** = Steel walls (indestructible)
- **Green tiles** = Forest (passable, blocks line-of-sight)
- **Blue tiles** = Water (passable, blocks bullets)
- **Gray tiles** = Empty space (safe zone)
- **Yellow tile** = Eagle (protected structure - don't let enemies destroy it!)

**BULLETS:**
- **Yellow dots** = Active bullets (very fast projectiles)

### GAMEPLAY MECHANICS

1. **Movement**: Use arrow keys to move around the grid. Each tile is one square.

2. **Shooting**: 
   - Press Z or Ctrl to shoot
   - You can only have one bullet in the air at a time
   - After shooting, wait 3 seconds before you can shoot again (fire cooldown)
   - Bullets destroy brick walls instantly
   - Bullets cannot pass through steel walls or water

3. **Enemy AI**:
   - **BASIC tanks** use BFS (Breadth-First Search) pathfinding to navigate toward the eagle
   - **FAST tanks** use Greedy Best-First search - they rush toward the eagle but may get stuck
   - **ARMOR tanks** use A* pathfinding and retreat when damaged

4. **Victory**: Destroy all 20 enemies across levels 1-2
5. **Defeat**: Lose all 10 lives (starting lives) or let an enemy destroy the eagle

### STRATEGY TIPS

- **Protect the Eagle**: Build walls of bricks around the eagle to keep enemies away
- **Use terrain**: Hide behind walls to avoid enemy bullets
- **Destroy walls**: Brick walls can be destroyed to create new paths or reach enemies
- **Cooldown management**: Time your shots carefully - you'll need to reload after each shot
- **Watch enemy patterns**: Different tank types behave differently - use this to your advantage

### GAME STATS (HUD)

The top-left shows:
- **Level**: Current game level
- **Lives**: Remaining lives (starts at 10)
- **Enemies**: Number of enemies defeated / total
- **Active**: Number of enemy tanks currently on map (max 3)
- **Bullets**: Number of active bullets
- **Time**: Elapsed time for this level
- **Controls**: Quick reference for key bindings

---

**Good luck defending the eagle!** 🦅
