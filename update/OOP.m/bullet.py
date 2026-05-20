import pygame
import math
from config import *

class Bullet:
    def __init__(self, x, y, target_x, target_y):
        self.x = x
        self.y = y
        self.speed = 400 # Pixel mỗi giây
        self.radius = 5
        
        # Tính toán góc bay bằng Toán Vector
        dx = target_x - x
        dy = target_y - y
        distance = math.hypot(dx, dy)
        
        if distance == 0:
            self.dir_x, self.dir_y = 0, -1
        else:
            self.dir_x = dx / distance
            self.dir_y = dy / distance

    def update(self, dt):
        # Đạn di chuyển theo hướng đã tính
        self.x += self.dir_x * self.speed * dt
        self.y += self.dir_y * self.speed * dt

    def draw(self, screen):
        pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), self.radius)