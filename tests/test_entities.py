import unittest
import math
from logic.entities.enemy import Enemy
from logic.entities.boss import Boss
from logic.entities.ranged_enemy import RangedEnemy
from logic.entities.status_effect import StatusEffect

class TestEntities(unittest.TestCase):
    def test_status_effect(self):
        enemy = Enemy(0, 0)
        effect = StatusEffect('poison', damage_per_sec=10.0, duration=2.0)
        effect.update(enemy, 0.5)
        self.assertEqual(effect.remaining, 1.5)
        self.assertEqual(enemy.hp, 45.0) # 50 - (10 * 0.5)

    def test_enemy_movement_with_slow(self):
        enemy = Enemy(0, 0)
        enemy.speed = 100
        # Add slow effect (50% speed)
        effect = StatusEffect('slow', damage_per_sec=0, duration=2.0, slow_factor=0.5)
        enemy.add_status(effect)
        
        # Player at (100, 0)
        enemy.update(1.0, 100, 0)
        # Expected position: x = 0 + 1 * (100 * 0.5) * 1.0 = 50
        self.assertEqual(enemy.x, 50.0)

    def test_enemy_status_refresh(self):
        enemy = Enemy(0, 0)
        eff1 = StatusEffect('burn', 5, 2.0)
        eff2 = StatusEffect('burn', 5, 5.0)
        enemy.add_status(eff1)
        enemy.add_status(eff2)
        self.assertEqual(len(enemy.status_effects), 1)
        self.assertEqual(enemy.status_effects[0].remaining, 5.0)

    def test_ranged_enemy_behavior(self):
        # STOP_DISTANCE = 350
        re = RangedEnemy(0, 0)
        re.speed = 100
        
        # Ở xa: 500px -> Phải di chuyển
        re.update(1.0, 500, 0)
        self.assertEqual(re.x, 100.0)
        
        # Ở gần: 300px -> Phải đứng lại
        re.update(1.0, 300, 0) # re.x vẫn là 100 vì dist = 200 < 350
        self.assertEqual(re.x, 100.0)

    def test_boss_charge_logic(self):
        boss = Boss(0, 0)
        boss.charge_cooldown_timer = 0
        # Frame 1: Trigger charge
        boss.update(0.1, 1000, 0)
        self.assertTrue(boss.is_charging)
        self.assertEqual(boss.charge_target_x, 1000)
        
        # Frame 2: Moving towards target (Charge speed = 350)
        # dist = 1000, move_x = 1, x += 1 * 350 * 0.1 = 35
        boss.update(0.1, 1000, 0)
        self.assertAlmostEqual(boss.x, 35.0) # Frame 1 chốt target, Frame 2 mới bắt đầu lao

    def test_enemy_multipliers(self):
        enemy = Enemy(0, 0, hp_mult=1.5, speed_mult=1.2)
        self.assertEqual(enemy.max_hp, Enemy.BASE_HP * 1.5)
        self.assertEqual(enemy.speed, Enemy.BASE_SPEED * 1.2)
        self.assertEqual(enemy.damage, 20.0 * 1.5)

    def test_fast_enemy(self):
        from logic.entities.fast_enemy import FastEnemy
        enemy = FastEnemy(0, 0, hp_mult=2.0, speed_mult=1.0)
        self.assertEqual(enemy.max_hp, FastEnemy.BASE_HP * 2.0)
        self.assertEqual(enemy.speed, FastEnemy.BASE_SPEED * 1.0)

    def test_tank_enemy(self):
        from logic.entities.tank_enemy import TankEnemy
        enemy = TankEnemy(0, 0, hp_mult=1.0, speed_mult=0.5)
        self.assertEqual(enemy.max_hp, TankEnemy.BASE_HP * 1.0)
        self.assertEqual(enemy.speed, TankEnemy.BASE_SPEED * 0.5)

if __name__ == '__main__':
    unittest.main()
