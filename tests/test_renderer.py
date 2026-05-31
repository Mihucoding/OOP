import unittest
import pygame
from ui.renderer import Renderer
from logic.entities.enemy import Enemy
from logic.entities.fast_enemy import FastEnemy
from logic.entities.ranged_enemy import RangedEnemy
from logic.entities.boss import Boss

class MockPlayer:
    def __init__(self):
        self.x = 0
        self.y = 0

class TestRenderer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        # Initialize a dummy display to allow image loading and surface creation
        pygame.display.set_mode((800, 600))
        
    def setUp(self):
        screen = pygame.Surface((800, 600))
        self.renderer = Renderer(screen)
        
    def test_load_animations(self):
        # Ensure animations are loaded without crashing
        self.assertIn('run', self.renderer.mushroom_animations)
        self.assertIn('attack1', self.renderer.fast_animations)
        self.assertIn('attack', self.renderer.tank_animations)
        self.assertIn('attack', self.renderer.boss_animations)
        
    def test_draw_enemy_states(self):
        # Create enemies in various states to ensure frame indexing math works
        cam_x, cam_y = 0, 0
        
        # 1. Normal Enemy (Mushroom)
        enemy = Enemy(100, 100)
        enemy.state = 'run'
        self.renderer.draw_enemy(enemy, cam_x, cam_y)
        
        enemy.state = 'attack'
        enemy.attack_timer = 0.4
        self.renderer.draw_enemy(enemy, cam_x, cam_y)
        
        enemy.state = 'die'
        enemy.die_timer = 0.5
        self.renderer.draw_enemy(enemy, cam_x, cam_y)
        
        # 2. Fast Enemy (Bat)
        fast = FastEnemy(200, 200)
        fast.state = 'attack1'
        fast.attack_timer = 0.3
        self.renderer.draw_enemy(fast, cam_x, cam_y)
        
        fast.state = 'windup'
        fast.attack_timer = 0.2
        self.renderer.draw_enemy(fast, cam_x, cam_y)
        
        fast.state = 'lunge'
        fast.attack_timer = 0.1
        self.renderer.draw_enemy(fast, cam_x, cam_y)
        
        # 3. Boss (Golem)
        boss = Boss(300, 300)
        boss.is_charging = True
        self.renderer.draw_boss(boss, cam_x, cam_y)
        
        boss.is_charging = False
        boss.aoe_active = True
        boss.aoe_timer = 1.0
        self.renderer.draw_boss(boss, cam_x, cam_y)

if __name__ == '__main__':
    unittest.main()
