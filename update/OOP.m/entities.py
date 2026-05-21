# entities.py — Upgraded with Enemy hierarchy from OOP-feature-player-enemy-basics
import pygame
import math
from config import *
from status_effect import StatusEffect


# ===========================================================================
#  ENEMY BASE — kế thừa từ OOP-feature, tích hợp pygame draw
# ===========================================================================
class Enemy:
    RADIUS = 20
    BASE_HP = 50
    BASE_SPEED = 100
    XP_VALUE = 10

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.radius = Enemy.RADIUS
        self.max_hp = Enemy.BASE_HP
        self.hp = float(Enemy.BASE_HP)
        self.speed = Enemy.BASE_SPEED
        self.xp_value = Enemy.XP_VALUE
        self.alive = True
        self.status_effects: list = []

    def update(self, dt, player_x, player_y):
        # 1. Cập nhật status_effects và tính slow_factor
        slow_factor = 1.0
        active_effects = []
        for eff in self.status_effects:
            eff.update(self, dt)
            if not eff.is_expired():
                active_effects.append(eff)
                if eff.slow_factor < 1.0:
                    slow_factor = min(slow_factor, eff.slow_factor)
        self.status_effects = active_effects

        # 2. Logic di chuyển đuổi theo player
        move_x = player_x - self.x
        move_y = player_y - self.y
        move_len = math.hypot(move_x, move_y)
        if move_len > 0:
            self.x += (move_x / move_len) * self.speed * slow_factor * dt
            self.y += (move_y / move_len) * self.speed * slow_factor * dt

    def take_damage(self, amount: float) -> None:
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

    def add_status(self, effect: StatusEffect) -> None:
        """Nếu đã có effect cùng loại → refresh remaining và tăng stack (nếu là burn hoặc chill)."""
        for eff in self.status_effects:
            if eff.type == effect.type:
                eff.remaining = max(eff.remaining, effect.remaining)
                if eff.type in ['burn', 'chill']:
                    eff.stacks = min(eff.stacks + 1, eff.max_stacks)
                return
        self.status_effects.append(effect)

    def get_hp_ratio(self) -> float:
        return self.hp / self.max_hp

    def draw(self, screen, cx, cy):
        sx = int(self.x - cx)
        sy = int(self.y - cy)
        # Thân
        pygame.draw.circle(screen, RED, (sx, sy), self.radius)
        # HP bar
        bar_w = self.radius * 2
        bar_h = 4
        bx = sx - self.radius
        by = sy - self.radius - 8
        pygame.draw.rect(screen, (60, 0, 0), (bx, by, bar_w, bar_h))
        pygame.draw.rect(screen, (220, 40, 40),
                         (bx, by, int(bar_w * self.get_hp_ratio()), bar_h))
        
        # Glow & Stacks khi có status effect
        if self.status_effects:
            eff_color = {'burn': ORANGE, 'poison': GREEN, 'slow': CYAN, 'chill': (150, 200, 255), 'stun': YELLOW}
            primary = self.status_effects[0]
            color = eff_color.get(primary.type, WHITE)
            pygame.draw.circle(screen, color, (sx, sy), self.radius + 3, 2)
            
            # Hiển thị số stack nếu là burn
            for eff in self.status_effects:
                if eff.type == 'burn':
                    try:
                        font_stack = pygame.font.SysFont(None, 20)
                        stack_txt = f"x{eff.stacks}"
                        col = (255, 255, 0) if eff.stacks >= 5 else ORANGE
                        txt = font_stack.render(stack_txt, True, col)
                        screen.blit(txt, (sx + self.radius + 2, sy - 10))
                    except: pass


# ===========================================================================
#  RANGED ENEMY — giữ khoảng cách, bắn đạn
# ===========================================================================
class RangedEnemy(Enemy):
    """Quái tầm xa — giữ khoảng cách và bắn đạn về phía player."""
    RADIUS = 16
    BASE_HP = 35
    BASE_SPEED = 70
    XP_VALUE = 15
    STOP_DISTANCE = 300
    FIRE_RATE = 2.0   # giây giữa 2 lần bắn

    def __init__(self, x, y):
        super().__init__(x, y)
        self.radius = RangedEnemy.RADIUS
        self.max_hp = RangedEnemy.BASE_HP
        self.hp = float(RangedEnemy.BASE_HP)
        self.speed = RangedEnemy.BASE_SPEED
        self.xp_value = RangedEnemy.XP_VALUE
        self.fire_timer = self.FIRE_RATE

    def update(self, dt, player_x, player_y):
        # 1. Cập nhật status effects
        slow_factor = 1.0
        active_effects = []
        for eff in self.status_effects:
            eff.update(self, dt)
            if not eff.is_expired():
                active_effects.append(eff)
                if eff.slow_factor < 1.0:
                    slow_factor = min(slow_factor, eff.slow_factor)
        self.status_effects = active_effects

        # 2. Chỉ di chuyển nếu ở xa hơn STOP_DISTANCE
        dist = math.hypot(player_x - self.x, player_y - self.y)
        if dist > self.STOP_DISTANCE:
            move_x = player_x - self.x
            move_y = player_y - self.y
            self.x += (move_x / dist) * self.speed * slow_factor * dt
            self.y += (move_y / dist) * self.speed * slow_factor * dt

        # 3. Đếm fire timer
        if self.fire_timer > 0:
            self.fire_timer -= dt

    def can_fire(self) -> bool:
        return self.fire_timer <= 0

    def reset_fire_timer(self) -> None:
        self.fire_timer = self.FIRE_RATE

    def draw(self, screen, cx, cy):
        sx = int(self.x - cx)
        sy = int(self.y - cy)
        pygame.draw.circle(screen, CYAN, (sx, sy), self.radius)
        pygame.draw.circle(screen, WHITE, (sx, sy), self.radius, 2)
        # HP bar
        bar_w = self.radius * 2
        bar_h = 4
        bx = sx - self.radius
        by = sy - self.radius - 8
        pygame.draw.rect(screen, (0, 60, 60), (bx, by, bar_w, bar_h))
        pygame.draw.rect(screen, CYAN,
                         (bx, by, int(bar_w * self.get_hp_ratio()), bar_h))
        
        # Glow & Stacks
        if self.status_effects:
            eff_color = {'burn': ORANGE, 'poison': GREEN, 'slow': (150, 150, 255)}
            primary = self.status_effects[0]
            color = eff_color.get(primary.type, WHITE)
            pygame.draw.circle(screen, color, (sx, sy), self.radius + 3, 2)
            
            for eff in self.status_effects:
                if eff.type == 'burn':
                    try:
                        font_stack = pygame.font.SysFont(None, 18)
                        stack_txt = f"x{eff.stacks}"
                        col = (255, 255, 0) if eff.stacks >= 5 else ORANGE
                        txt = font_stack.render(stack_txt, True, col)
                        screen.blit(txt, (sx + self.radius + 2, sy - 10))
                    except: pass


# ===========================================================================
#  BOSS — kế thừa Enemy, có 3 skill: Charge / AoE Slam / Summon
# ===========================================================================
class Boss(Enemy):
    """
    Boss kế thừa Enemy, có 3 skill riêng:
    1. Charge  : lao thẳng vào player tốc độ cao
    2. AoE Slam: vùng damage tròn xung quanh boss
    3. Summon  : set cờ pending_summon=True → main loop spawn thêm quái
    """
    RADIUS = 45
    BASE_HP = 800
    BASE_SPEED = 50
    XP_VALUE = 300

    CHARGE_COOLDOWN = 8.0
    CHARGE_DURATION = 1.2
    CHARGE_SPEED = 350
    CHARGE_DAMAGE = 30.0

    AOE_COOLDOWN = 10.0
    AOE_RADIUS = 130
    AOE_DAMAGE_PER_SEC = 40.0
    AOE_DURATION = 1.5

    SUMMON_COOLDOWN = 15.0
    SUMMON_COUNT = 3

    def __init__(self, x, y):
        super().__init__(x, y)
        self.radius = Boss.RADIUS
        self.max_hp = Boss.BASE_HP
        self.hp = float(Boss.BASE_HP)
        self.speed = Boss.BASE_SPEED
        self.xp_value = Boss.XP_VALUE

        # Charge state
        self.charge_cooldown_timer = 5.0
        self.charge_timer = 0.0
        self.is_charging = False
        self.charge_target_x = 0.0
        self.charge_target_y = 0.0

        # AoE state
        self.aoe_cooldown_timer = 8.0
        self.aoe_active = False
        self.aoe_timer = 0.0

        # Summon state
        self.summon_cooldown_timer = 10.0
        self.pending_summon = False

    def update(self, dt, player_x, player_y):
        # 1. Cập nhật status_effects
        slow_factor = 1.0
        active_effects = []
        for eff in self.status_effects:
            eff.update(self, dt)
            if not eff.is_expired():
                active_effects.append(eff)
                if eff.slow_factor < 1.0:
                    slow_factor = min(slow_factor, eff.slow_factor)
        self.status_effects = active_effects

        # 2. Gọi 3 skill
        self._update_charge(dt, player_x, player_y, slow_factor)
        self._update_aoe(dt)
        self._update_summon(dt)

    def _update_charge(self, dt, px, py, slow):
        if self.is_charging:
            self.charge_timer -= dt
            if self.charge_timer <= 0:
                self.is_charging = False
                self.charge_cooldown_timer = Boss.CHARGE_COOLDOWN
            else:
                move_x = self.charge_target_x - self.x
                move_y = self.charge_target_y - self.y
                move_len = math.hypot(move_x, move_y)
                if move_len > 0:
                    self.x += (move_x / move_len) * Boss.CHARGE_SPEED * dt
                    self.y += (move_y / move_len) * Boss.CHARGE_SPEED * dt
        else:
            self.charge_cooldown_timer -= dt
            if self.charge_cooldown_timer <= 0:
                self.is_charging = True
                self.charge_timer = Boss.CHARGE_DURATION
                self.charge_target_x = px
                self.charge_target_y = py
            else:
                move_x = px - self.x
                move_y = py - self.y
                move_len = math.hypot(move_x, move_y)
                if move_len > 0:
                    self.x += (move_x / move_len) * self.speed * slow * dt
                    self.y += (move_y / move_len) * self.speed * slow * dt

    def _update_aoe(self, dt):
        if self.aoe_active:
            self.aoe_timer -= dt
            if self.aoe_timer <= 0:
                self.aoe_active = False
                self.aoe_cooldown_timer = Boss.AOE_COOLDOWN
        else:
            self.aoe_cooldown_timer -= dt
            if self.aoe_cooldown_timer <= 0:
                self.aoe_active = True
                self.aoe_timer = Boss.AOE_DURATION

    def _update_summon(self, dt):
        self.summon_cooldown_timer -= dt
        if self.summon_cooldown_timer <= 0:
            self.pending_summon = True
            self.summon_cooldown_timer = Boss.SUMMON_COOLDOWN

    def check_aoe_hit(self, player_x: float, player_y: float) -> float:
        """Trả về AOE_DAMAGE_PER_SEC nếu player trong vùng AoE, ngược lại 0."""
        if self.aoe_active:
            dist = math.hypot(player_x - self.x, player_y - self.y)
            if dist <= Boss.AOE_RADIUS:
                return Boss.AOE_DAMAGE_PER_SEC
        return 0.0

    def check_charge_hit(self, player_x: float, player_y: float,
                         player_radius: float) -> float:
        """Trả về CHARGE_DAMAGE nếu đang charge và chạm player."""
        if self.is_charging:
            dist = math.hypot(player_x - self.x, player_y - self.y)
            if dist <= Boss.RADIUS + player_radius:
                return Boss.CHARGE_DAMAGE
        return 0.0

    def draw(self, screen, cx, cy):
        sx = int(self.x - cx)
        sy = int(self.y - cy)

        # AoE vòng tròn cảnh báo
        if self.aoe_active:
            aoe_surf = pygame.Surface((Boss.AOE_RADIUS * 2, Boss.AOE_RADIUS * 2), pygame.SRCALPHA)
            pygame.draw.circle(aoe_surf, (255, 50, 50, 60),
                               (Boss.AOE_RADIUS, Boss.AOE_RADIUS), Boss.AOE_RADIUS)
            screen.blit(aoe_surf, (sx - Boss.AOE_RADIUS, sy - Boss.AOE_RADIUS))
            pygame.draw.circle(screen, (255, 80, 80), (sx, sy), Boss.AOE_RADIUS, 2)

        # Thân boss
        color = (220, 0, 220) if not self.is_charging else (255, 100, 0)
        pygame.draw.circle(screen, color, (sx, sy), self.radius)
        pygame.draw.circle(screen, WHITE, (sx, sy), self.radius, 3)

        # Nhãn BOSS
        try:
            font_small = pygame.font.SysFont(None, 22)
            label = font_small.render("BOSS", True, WHITE)
            screen.blit(label, (sx - label.get_width() // 2, sy - 8))
        except Exception:
            pass

        # HP bar boss (to hơn)
        bar_w = self.radius * 3
        bar_h = 7
        bx = sx - bar_w // 2
        by = sy - self.radius - 16
        pygame.draw.rect(screen, (80, 0, 80), (bx, by, bar_w, bar_h))
        pygame.draw.rect(screen, (220, 0, 220),
                         (bx, by, int(bar_w * self.get_hp_ratio()), bar_h))

        # Indicator "CHARGING"
        if self.is_charging:
            try:
                font_small = pygame.font.SysFont(None, 20)
                txt = font_small.render("CHARGE!", True, ORANGE)
                screen.blit(txt, (sx - txt.get_width() // 2, sy - self.radius - 30))
            except Exception:
                pass
        
        # Stacks Burn cho Boss
        for eff in self.status_effects:
            if eff.type == 'burn':
                try:
                    font_stack = pygame.font.SysFont(None, 24)
                    stack_txt = f"x{eff.stacks}"
                    col = (255, 255, 0) if eff.stacks >= 5 else ORANGE
                    txt = font_stack.render(stack_txt, True, col)
                    screen.blit(txt, (sx + self.radius + 5, sy - 20))
                except: pass


# ===========================================================================
#  EXP GEM (giữ nguyên để tương thích với main.py)
# ===========================================================================
class ExpGem:
    def __init__(self, x, y, amount=10):
        self.x = x
        self.y = y
        self.radius = 5
        self.amount = amount

    def draw(self, screen, cx, cy):
        pygame.draw.circle(screen, GREEN,
                           (int(self.x - cx), int(self.y - cy)), self.radius)


# ===========================================================================
#  ENEMY BULLET — đạn của RangedEnemy
# ===========================================================================
class EnemyBullet:
    SPEED = 220
    RADIUS = 5
    DAMAGE = 12.0
    LIFETIME = 4.0

    def __init__(self, x, y, target_x, target_y):
        self.x = float(x)
        self.y = float(y)
        self.radius = EnemyBullet.RADIUS
        self.damage = EnemyBullet.DAMAGE
        self.alive = True
        self.elapsed = 0.0

        dx = target_x - x
        dy = target_y - y
        dist = math.hypot(dx, dy)
        if dist == 0:
            self.vx, self.vy = 0.0, -1.0
        else:
            self.vx = (dx / dist) * EnemyBullet.SPEED
            self.vy = (dy / dist) * EnemyBullet.SPEED

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.elapsed += dt
        if self.elapsed >= EnemyBullet.LIFETIME:
            self.alive = False

    def draw(self, screen, cx, cy):
        pygame.draw.circle(screen, ORANGE,
                           (int(self.x - cx), int(self.y - cy)), self.radius)