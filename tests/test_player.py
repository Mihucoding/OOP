import unittest
import math
from logic.entities.player import Player

class TestPlayer(unittest.TestCase):
    def test_initialization(self):
        p = Player(10, 20)
        self.assertEqual(p.x, 10)
        self.assertEqual(p.y, 20)
        self.assertEqual(p.hp, 100)
        self.assertEqual(p.fire_timer, 0.0)

    def test_update_movement(self):
        p = Player(0, 0)
        p.speed = 100
        # Di chuyển chéo (1, 1)
        p.update(1.0, 1, 1)
        # Vector độ dài 1.0 -> x, y += 100 * (1/sqrt(2)) ~ 70.71
        expected = 100 / math.sqrt(2)
        self.assertAlmostEqual(p.x, expected)
        self.assertAlmostEqual(p.y, expected)

    def test_update_fire_timer(self):
        p = Player(0, 0)
        p.fire_timer = 1.0
        p.update(0.5, 0, 0)
        self.assertAlmostEqual(p.fire_timer, 0.5)
        p.update(1.0, 0, 0)
        # Clamp timer to 0
        self.assertEqual(p.fire_timer, 0.0)

    def test_take_damage(self):
        p = Player(0, 0)
        p.take_damage(30)
        self.assertEqual(p.hp, 70)
        self.assertTrue(p.alive)
        p.take_damage(80)
        self.assertEqual(p.hp, 0)
        self.assertFalse(p.alive)

    def test_add_xp_multiple_levels(self):
        p = Player()
        leveled_up = p.add_xp(100) # 30 + 42 + 28 remaining -> level 3
        self.assertTrue(leveled_up)
        self.assertEqual(p.level, 3)
        self.assertEqual(p.xp, 28)

if __name__ == '__main__':
    unittest.main()
