import math
from logic.entities.enemy import Enemy


class Boss(Enemy):
    """
    Boss kế thừa Enemy, có 3 skill riêng:
    1. Charge  : lao thẳng vào player tốc độ cao 1 giây
    2. AoE Slam: vùng damage tròn xung quanh boss trong AOE_DURATION giây
    3. Summon  : set cờ pending_summon=True → WaveManager spawn quái
    """
    RADIUS = 45
    BASE_HP = 1000
    BASE_SPEED = 50
    XP_VALUE = 500

    # Skill configs
    CHARGE_COOLDOWN = 8.0
    CHARGE_DURATION = 1.2
    CHARGE_SPEED = 350

    AOE_COOLDOWN = 12.0
    AOE_RADIUS = 120
    AOE_DAMAGE_PER_SEC = 40.0
    AOE_DURATION = 1.5

    SUMMON_COOLDOWN = 15.0
    SUMMON_COUNT = 4

    CHARGE_DAMAGE = 30.0

    def __init__(self, x: float, y: float):
        super().__init__(x, y)
        self.radius = Boss.RADIUS
        self.max_hp = Boss.BASE_HP
        self.hp = float(Boss.BASE_HP)
        self.speed = Boss.BASE_SPEED
        self.xp_value = Boss.XP_VALUE

        # Charge state
        self.charge_cooldown_timer = 5.0   # đợi 5s trước lần đầu
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
        self.pending_summon = False   # WaveManager đọc cờ này

    def update(self, dt: float, player_x: float, player_y: float) -> None:
        # 1. Cập nhật status_effects (xử lý slow, chill, stun như nhau qua slow_factor)
        slow_factor    = 1.0
        active_effects = []
        for eff in self.status_effects:
            eff.update(self, dt)
            if not eff.is_expired():
                active_effects.append(eff)
                if eff.slow_factor < 1.0:
                    slow_factor = min(slow_factor, eff.slow_factor)
        self.status_effects = active_effects

        # 2. Gọi các skill của Boss
        self._update_charge(dt, player_x, player_y, slow_factor)
        self._update_aoe(dt)
        self._update_summon(dt)

    def _update_charge(self, dt, px, py, slow):
        # Nếu đang charge: lao về charge_target, đếm ngược charge_timer
        #   Khi hết timer hoặc đến nơi → is_charging = False, reset cooldown
        # Nếu không charge: đếm ngược cooldown, di chuyển bình thường về player
        #   Khi cooldown hết → bắt đầu charge (lưu vị trí player lúc này)
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
                    move_x /= move_len
                    move_y /= move_len
                self.x += move_x * Boss.CHARGE_SPEED * dt
                self.y += move_y * Boss.CHARGE_SPEED * dt
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
                    move_x /= move_len
                    move_y /= move_len
                self.x += move_x * self.speed * slow * dt
                self.y += move_y * self.speed * slow * dt

    def _update_aoe(self, dt):
        # Nếu aoe_active: đếm aoe_timer, khi hết → tắt, reset cooldown
        # Nếu không: đếm cooldown, khi hết → bật aoe_active
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
        # Đếm cooldown, khi hết → pending_summon = True, reset cooldown
        self.summon_cooldown_timer -= dt
        if self.summon_cooldown_timer <= 0:
            self.pending_summon = True
            self.summon_cooldown_timer = Boss.SUMMON_COOLDOWN

    def check_aoe_hit(self, player_x: float, player_y: float) -> float:
        # Nếu aoe_active và player trong AOE_RADIUS → trả về AOE_DAMAGE_PER_SEC
        # Ngược lại trả về 0.0
        if self.aoe_active:
            dist = math.hypot(player_x - self.x, player_y - self.y)
            if dist <= Boss.AOE_RADIUS:
                return Boss.AOE_DAMAGE_PER_SEC
        return 0.0

    def check_charge_hit(self, player_x: float, player_y: float,
                         player_radius: float) -> float:
        # Nếu đang charge và khoảng cách <= radius+player_radius
        # Trả về damage (ví dụ 30), ngược lại 0
        if self.is_charging:
            dist = math.hypot(player_x - self.x, player_y - self.y)
            if dist <= Boss.RADIUS + player_radius:
                return Boss.CHARGE_DAMAGE
        return 0.0
