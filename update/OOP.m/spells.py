import pygame
import math
from config import *

class Projectile:
    def __init__(self, x, y, target_x, target_y, color, speed, lifetime):
        self.x, self.y = x, y
        self.speed, self.lifetime = speed, lifetime
        self.radius = 6
        self.color = color
        self.is_alive = True # Cờ xác định đạn còn sống không
        
        dx, dy = target_x - x, target_y - y
        dist = math.hypot(dx, dy)
        self.dir_x, self.dir_y = (0, -1) if dist == 0 else (dx / dist, dy / dist)
            
        self.active_nodes = [] # Các node Rune đang áp dụng
        
    def update(self, dt, spell_manager):
        self.lifetime -= dt
        # Gọi event on_update mỗi frame
        for node in self.active_nodes:
            node.on_update(self, dt, spell_manager)
        self.x += self.dir_x * self.speed * dt
        self.y += self.dir_y * self.speed * dt

    def draw(self, screen, cx, cy):
        pygame.draw.circle(screen, self.color, (int(self.x - cx), int(self.y - cy)), self.radius)

class SpellManager:
    def __init__(self, player):
        self.player = player
        self.projectiles = []
        self.core_tree = None # Lưu Rune Lõi ở đây
        self.enemies_ref = [] # Trỏ tới list quái để Rune nảy tìm mục tiêu

    def create_projectile(self, x, y, tx, ty, color, speed, lifetime):
        return Projectile(x, y, tx, ty, color, speed, lifetime)

    def on_click(self, world_mouse_x, world_mouse_y):
        if self.core_tree:
            # Xác định màu và thông số từ Lõi
            color = ORANGE if self.core_tree.element == "Lửa" else PURPLE
            # Sinh đạn cha
            p = self.create_projectile(self.player.x, self.player.y, world_mouse_x, world_mouse_y, color, 500, 1.5)
            p.active_nodes = [self.core_tree]
            self.projectiles.append(p)
            
            # Kích hoạt hook on_spawn ngay khi bắn
            self.core_tree.on_spawn(p, self)

    def update(self, dt, mouse_pressed, world_mouse_x, world_mouse_y, enemies):
        self.enemies_ref = enemies # Cập nhật danh sách quái mới nhất
        for p in self.projectiles:
            p.update(dt, self)
        # Lọc đạn chết hoặc hết thời gian
        self.projectiles = [p for p in self.projectiles if p.lifetime > 0 and p.is_alive]
        
    def draw(self, screen, cx, cy):
        for p in self.projectiles:
            p.draw(screen, cx, cy)