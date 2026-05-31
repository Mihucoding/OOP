from logic.entities.enemy import Enemy
import math

class FastEnemy(Enemy):
    """
    Quái Nhanh: máu ít, di chuyển cực nhanh.
    Có cơ chế gồng (windup) và lướt tới cắn (lunge).
    """
    RADIUS = 15
    BASE_HP = 30
    BASE_SPEED = 150
    XP_VALUE = 15
    COLOR = (255, 255, 0) # YELLOW

    def __init__(self, x, y, hp_mult=1.0, speed_mult=1.0):
        super().__init__(x, y, hp_mult, speed_mult)
        self.ATTACK1_RANGE = 45.0
        self.ATTACK2_RANGE = 120.0
        self.WINDUP_DURATION = 0.5
        self.LUNGE_DURATION = 0.3
        self.LUNGE_SPEED_MULT = 3.0
        self.ATTACK1_DURATION = 0.6
        self.ATTACK1_HIT_TIME = 0.3
        
        self.attack2_cooldown_timer = 0.0
        
        self.lunge_target_x = 0.0
        self.lunge_target_y = 0.0

    def update(self, dt: float, player_x: float, player_y: float) -> None:
        self.hurt_timer = max(0.0, getattr(self, 'hurt_timer', 0.0) - dt)
        if getattr(self, 'state', '') == 'die':
            self.die_timer += dt
            if self.die_timer >= 1.2:
                self.alive = False
            return
            
        slow_factor = 1.0
        active_effects = []
        for eff in self.status_effects:
            eff.update(self, dt)
            if not eff.is_expired():
                active_effects.append(eff)
                if eff.slow_factor < 1.0:
                    slow_factor = min(slow_factor, eff.slow_factor)
        self.status_effects = active_effects
        
        if self.cast_lock_timer > 0:
            self.cast_lock_timer = max(0.0, self.cast_lock_timer - dt)
            return

        self.attack_hitbox = None
        self.attack2_cooldown_timer -= dt
        
        if self.state == 'run':
            move_x = player_x - self.x
            move_y = player_y - self.y
            move_len = math.hypot(move_x, move_y)
            if move_len > 0:
                self.facing_dir = 1 if move_x > 0 else -1

            if move_len <= self.ATTACK1_RANGE:
                self.state = 'attack1'
                self.attack_timer = 0.0
                self.has_hit = False
            elif move_len <= self.ATTACK2_RANGE and self.attack2_cooldown_timer <= 0:
                self.state = 'windup'
                self.attack_timer = 0.0
                self.lunge_target_x = player_x
                self.lunge_target_y = player_y
            elif move_len > 0:
                self.x += (move_x / move_len) * self.speed * slow_factor * dt
                self.y += (move_y / move_len) * self.speed * slow_factor * dt
                
        elif self.state == 'attack1':
            self.attack_timer += dt
            if self.attack_timer >= self.ATTACK1_HIT_TIME and not self.has_hit:
                self.has_hit = True
                hx = self.x + self.facing_dir * 25.0
                hy = self.y
                self.attack_hitbox = (hx, hy, 30.0)
            if self.attack_timer >= self.ATTACK1_DURATION:
                self.state = 'cooldown'
                self.cooldown_timer = 0.8
                
        elif self.state == 'windup':
            self.attack_timer += dt
            if self.attack_timer >= self.WINDUP_DURATION:
                self.state = 'lunge'
                self.attack_timer = 0.0
                self.has_hit = False
                
        elif self.state == 'lunge':
            self.attack_timer += dt
            move_x = self.lunge_target_x - self.x
            move_y = self.lunge_target_y - self.y
            move_len = math.hypot(move_x, move_y)
            
            if move_len > 0:
                self.x += (move_x / move_len) * self.speed * self.LUNGE_SPEED_MULT * slow_factor * dt
                self.y += (move_y / move_len) * self.speed * self.LUNGE_SPEED_MULT * slow_factor * dt
                
            if not self.has_hit:
                self.has_hit = True
                hx = self.x + self.facing_dir * 15.0
                hy = self.y
                self.attack_hitbox = (hx, hy, 25.0)

            if self.attack_timer >= self.LUNGE_DURATION:
                self.state = 'cooldown'
                self.cooldown_timer = 1.2
                self.attack2_cooldown_timer = 3.0 # Đợi 3s trước khi charge tiếp
                
        elif self.state == 'cooldown':
            self.cooldown_timer -= dt
            if self.cooldown_timer <= 0:
                self.state = 'run'
