#!/usr/bin/env python3
"""Quick test to verify boss spawns correctly with 10 HP."""

import sys
sys.path.insert(0, 'src')

from tank import BossTank

# Test BossTank initialization
boss = BossTank(13, 7)
print(f"Boss created: {boss}")
print(f"Boss HP: {boss.hp}/{boss.max_hp}")
print(f"Boss color: {boss.color}")
print(f"Boss phase: {boss.phase}")
print(f"Boss type: {boss.tank_type}")

# Test damage
print("\nTesting damage:")
for i in range(11):
    destroyed = boss.take_damage(1)
    print(f"After bullet {i+1}: HP={boss.hp}, Destroyed={destroyed}, Phase={boss.phase}")
    if destroyed:
        break
