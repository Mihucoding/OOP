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
        # 1. Cập nhật status_effects (giống Enemy)
        # 2. Tính slow_factor
        # 3. _update_charge(dt, player_x, player_y, slow_factor)
        # 4. _update_aoe(dt)
        # 5. _update_summon(dt)
        pass

    def _update_charge(self, dt, px, py, slow):
        # Nếu đang charge: lao về charge_target, đếm ngược charge_timer
        #   Khi hết timer hoặc đến nơi → is_charging = False, reset cooldown
        # Nếu không charge: đếm ngược cooldown, di chuyển bình thường về player
        #   Khi cooldown hết → bắt đầu charge (lưu vị trí player lúc này)
        pass

    def _update_aoe(self, dt):
        # Nếu aoe_active: đếm aoe_timer, khi hết → tắt, reset cooldown
        # Nếu không: đếm cooldown, khi hết → bật aoe_active
        pass

    def _update_summon(self, dt):
        # Đếm cooldown, khi hết → pending_summon = True, reset cooldown
        pass

    def check_aoe_hit(self, player_x: float, player_y: float) -> float:
        # Nếu aoe_active và player trong AOE_RADIUS → trả về AOE_DAMAGE_PER_SEC
        # Ngược lại trả về 0.0
        pass

    def check_charge_hit(self, player_x: float, player_y: float,
                         player_radius: float) -> float:
        # Nếu đang charge và khoảng cách <= radius+player_radius
        # Trả về damage (ví dụ 30), ngược lại 0
        pass
