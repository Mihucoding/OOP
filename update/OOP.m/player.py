# player.py — Upgraded with hp, damage, fire_rate, alive from OOP-feature-player-enemy-basics
import pygame
from config import *
from spells import SpellManager

class Player:
    BASE_HP = 100
    BASE_SPEED = 200
    BASE_DAMAGE = 20
    BASE_FIRE_RATE = 0.5   # giây giữa 2 lần bắn tự động (chưa dùng, dành cho mở rộng)

    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.speed = Player.BASE_SPEED
        self.radius = 15

        # HP
        self.max_hp = Player.BASE_HP
        self.hp = float(Player.BASE_HP)
        self.alive = True

        # Damage stat (dùng khi đạn trúng enemy)
        self.damage = Player.BASE_DAMAGE

        # Fire rate (dự phòng cho auto-attack)
        self.fire_rate = Player.BASE_FIRE_RATE
        self.fire_timer = 0.0

        # Leveling
        self.level = 1
        self.exp = 0
        self.max_exp = 20    # Giảm xuống 20 để test lên cấp cho nhanh
        self.pending_level_ups = 0   # <--- THÊM BIẾN NÀY

        self.spell_manager = None   # Sẽ gán sau để tránh lỗi import chéo

        # Weapon system
        self.weapon = None        # FireWeapon / IceWeapon / LightningWeapon
        self.weapon_type = None   # 'fire' | 'ice' | 'lightning'

    def update(self, dt, mouse_pressed, world_mouse_x, world_mouse_y):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]: self.y -= self.speed * dt
        if keys[pygame.K_s]: self.y += self.speed * dt
        if keys[pygame.K_a]: self.x -= self.speed * dt
        if keys[pygame.K_d]: self.x += self.speed * dt

        # Giảm fire_timer nếu > 0
        self.fire_timer = max(0.0, self.fire_timer - dt)

    def can_fire(self) -> bool:
        return self.fire_timer <= 0

    def reset_fire_timer(self) -> None:
        self.fire_timer = self.fire_rate

    def take_damage(self, amount: float) -> None:
        """Trừ HP, clamp về 0, set alive=False nếu hp<=0."""
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

    def gain_exp(self, amount):
        self.exp += amount
        if self.exp >= self.max_exp:
            self.level_up()

    def level_up(self):
        self.level += 1
        self.exp -= self.max_exp
        self.max_exp = int(self.max_exp * 1.5)
        self.pending_level_ups += 1   # <--- ĐÁNH DẤU CÓ LÊN CẤP
        # Thưởng: HP tăng theo cấp
        bonus_hp = 10
        self.max_hp += bonus_hp
        self.hp = min(self.hp + bonus_hp, self.max_hp)  # Hồi một phần HP khi lên cấp

    def get_hp_ratio(self) -> float:
        return self.hp / self.max_hp

    def get_xp_ratio(self) -> float:
        return self.exp / self.max_exp

    def draw(self, screen, cx, cy):
        sx = int(self.x - cx)
        sy = int(self.y - cy)
        pygame.draw.circle(screen, BLUE, (sx, sy), self.radius)
        # Viền trắng
        pygame.draw.circle(screen, WHITE, (sx, sy), self.radius, 2)