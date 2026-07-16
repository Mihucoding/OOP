import math
from logic.entities.status_effect import StatusEffect


class Enemy:
    RADIUS    = 20
    BASE_HP   = 200
    BASE_SPEED = 80
    XP_VALUE  = 10

    def __init__(self, x: float, y: float, hp_mult=1.0, speed_mult=1.0):
        self.x       = float(x)
        self.y       = float(y)
        self.radius  = self.__class__.RADIUS
        self.max_hp  = self.__class__.BASE_HP * hp_mult
        self.hp      = float(self.max_hp)
        self.speed   = self.__class__.BASE_SPEED * speed_mult
        self.damage  = 20.0 * hp_mult
        self.xp_value = self.__class__.XP_VALUE
        self.alive   = True
        self.status_effects: list[StatusEffect] = []
        self.cast_lock_timer = 0.0

        # Attack State Machine
        self.state = 'run'  # 'run', 'attack', 'cooldown'
        self.attack_timer = 0.0
        self.cooldown_timer = 0.0
        self.facing_dir = 1
        self.ATTACK_RANGE = 55.0
        self.ATTACK_DURATION = 0.8
        self.ATTACK_HIT_TIME = 0.4
        self.COOLDOWN_DURATION = 1.0
        self.has_hit = False
        self.attack_hitbox = None # (x, y, radius)
        
        self.hurt_timer = 0.0
        self.die_timer = 0.0
        self.xp_dropped = False

    def update(self, dt: float, player_x: float, player_y: float) -> None:
        """
        Cập nhật logic của quái vật mỗi frame.
        - Xử lý các hiệu ứng trạng thái (StatusEffects) đang bị nhiễm: trừ máu từ từ nếu bị thiêu đốt (Burn), làm chậm (Slow/Chill), hoặc làm choáng (Stun).
        - Nếu không bị choáng, tìm đường (AI) di chuyển về phía người chơi.
        - Cập nhật thời gian chờ đòn đánh (nếu có).

        👉 BƯỚC TIẾP THEO (Bước 10): Quái vật di chuyển xong, hệ thống sẽ quay về `_update` của GameLoop để bắn đạn nếu bạn click chuột trái. Mở lại file [ui/game_loop.py](file:///c:/Users/acer/Downloads/OOP-mihu_branch/ui/game_loop.py) hàm `_spawn_bullet`.
        """
        self.hurt_timer = max(0.0, self.hurt_timer - dt)
        if self.state == 'die':
            self.die_timer += dt
            # Mushroom-Die có 15 frames, chạy ~1.2s
            if self.die_timer >= 1.2:
                self.alive = False
            return

        # 1. Cập nhật status_effects và tính slow_factor tổng hợp
        slow_factor    = 1.0
        active_effects = []
        for eff in self.status_effects:
            eff.update(self, dt)
            if not eff.is_expired():
                active_effects.append(eff)
                # Mọi effect có slow_factor < 1.0 đều làm chậm (slow, chill, stun)
                if eff.slow_factor < 1.0:
                    slow_factor = min(slow_factor, eff.slow_factor)
        self.status_effects = active_effects
        if self.cast_lock_timer > 0:
            self.cast_lock_timer = max(0.0, self.cast_lock_timer - dt)
            return

        # 2. State Machine
        self.attack_hitbox = None # Xoá hitbox frame cũ
        
        if self.state == 'run':
            move_x   = player_x - self.x
            move_y   = player_y - self.y
            move_len = math.hypot(move_x, move_y)
            
            if move_len > 0:
                self.facing_dir = 1 if move_x > 0 else -1
                
            if move_len <= self.ATTACK_RANGE:
                self.state = 'attack'
                self.attack_timer = 0.0
                self.has_hit = False
            elif move_len > 0:
                self.x += (move_x / move_len) * self.speed * slow_factor * dt
                self.y += (move_y / move_len) * self.speed * slow_factor * dt
                
        elif self.state == 'attack':
            self.attack_timer += dt
            if self.attack_timer >= self.ATTACK_HIT_TIME and not self.has_hit:
                self.has_hit = True
                # Tạo hitbox vũ khí phía trước
                hx = self.x + self.facing_dir * 25.0
                hy = self.y
                self.attack_hitbox = (hx, hy, 30.0) # radius 30
                
            if self.attack_timer >= self.ATTACK_DURATION:
                self.state = 'cooldown'
                self.cooldown_timer = self.COOLDOWN_DURATION
                
        elif self.state == 'cooldown':
            self.cooldown_timer -= dt
            if self.cooldown_timer <= 0:
                self.state = 'run'

    def take_damage(self, amount: float, flinch: bool = True) -> None:
        """
        Hàm xử lý khi quái nhận sát thương cơ bản từ viên đạn.
        Trừ máu, hiện số sát thương nảy lên (Floating Text) và giật lùi quái một chút (flinch).

        👉 BƯỚC TIẾP THEO (Bước 17): Sát thương cơ bản đã xong, giờ là lúc kích hoạt sát thương và hiệu ứng từ ngọc. Hãy quay lại file [logic/rune/rune_tree.py](file:///c:/Users/acer/Downloads/OOP-mihu_branch/logic/rune/rune_tree.py) đọc hàm `on_hit`.
        """
        if self.hp <= 0: return # Đang chết rồi
        self.hp -= amount
        if flinch:
            self.hurt_timer = 0.3
        if self.hp <= 0:
            self.hp = 0
            self.state = 'die'
            self.die_timer = 0.0
            self.attack_hitbox = None
            self.cast_lock_timer = 0.0

    def add_status(self, effect: StatusEffect) -> None:
        # Nếu đã có effect cùng loại → refresh remaining + cộng dồn stacks (burn/chill)
        # theo ĐÚNG lượng effect mới mang theo (burn: +1/lần; chill: +CHILL_PER_HIT/lần).
        for eff in self.status_effects:
            if eff.type == effect.type:
                eff.remaining = max(eff.remaining, effect.remaining)
                if eff.type in ('burn', 'chill'):
                    eff.stacks = min(eff.stacks + effect.stacks, eff.max_stacks)
                return
        self.status_effects.append(effect)

    def drop_xp(self, lucky: float = 0.0) -> list:
        from logic.entities.xp_orb import scatter_xp
        # Lucky cao → thêm orb: 0→3, ≥20→4, ≥50→5
        count = 3 + (1 if lucky >= 20 else 0) + (1 if lucky >= 50 else 0)
        return scatter_xp(self.x, self.y, self.xp_value, count=count)

    def get_hp_ratio(self) -> float:
        return self.hp / self.max_hp
