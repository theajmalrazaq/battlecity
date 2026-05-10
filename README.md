# Battle City AI

A modern recreation of the classic Battle City (Tank 1990) with advanced Artificial Intelligence modules, including CSP map generation, diverse search algorithms, and an adversarial Boss AI.

## How to Run

1. **Install Requirements**:
   ```bash
   pip install pygame
   ```

2. **Start the Game**:
   ```bash
   python menu.py
   ```
   *Use the menu to select between Level 1, Level 2, and the Boss Battle.*

---

## How to Play

### Controls
| Key | Action |
| :--- | :--- |
| **Arrow Keys** | Move Tank |
| **B / L-Shift** | Shoot Bullet |
| **Space** | Pause / Resume |
| **ESC** | Quit Game |

### Game Objective
Protect the **Eagle (Base)** at the bottom of the map. If an enemy bullet or tank reaches the Eagle, you lose! Destroy all 20 enemy tanks to win the level.

---

## AI Modules Implemented

This project features three core AI modules as part of the Artificial Intelligence Lab (AL 2002):

### 1. Module A: CSP Map Generator
Every level is procedurally generated using a **Constraint Satisfaction Problem** solver.
- **Constraints**: Base Safety, Reachability (from spawns to Eagle), Fairness (spawn distance), and Density Balance.
- **Optimization**: Uses Backtracking with Forward Checking and MRV.

### 2. Module B: Pathfinding Search
Enemy tanks use different algorithms to demonstrate varied behaviors:
- **Basic Tanks**: BFS (Breadth-First Search) for shortest hop-paths.
- **Fast Tanks**: Greedy Best-First Search for aggressive rushing.
- **Armor Tanks**: A* Search with strategic cost-awareness (treats bricks as cost=3).

### 3. Module C: Adversarial Search (Boss AI)
The final level features a **Tank Commander** that uses:
- **Minimax Algorithm**: Simulates player moves up to depth 4.
- **Alpha-Beta Pruning**: Optimizes search speed by ~31x.
- **Dynamic Phases**: Boss becomes faster and smarter as its HP decreases.

---

## Implementation Details

- **Language**: Python 3.13+
- **Graphics**: Pygame (with custom sprite assets)
- **Architecture**: Modular design with separate engines for collision, AI, and game state.

## Submitted By

- **Ajmal Razaq** (23F-0524)
- **Rania Shoaib** (23F-0650)
- **Section**: 6A

---
*Created for the Artificial Intelligence Lab Semester Project - Spring 2026.*
