from logic.entities.enemy import Enemy


class DummyEnemy(Enemy):
    """
    Bia tập (training dummy) cho creative mode: đứng yên, máu vô hạn (không
    chết), dùng để đo sát thương/DPS. Cộng dồn mọi damage nhận được (kể cả DoT
    burn/chill) và tự tính DPS trên cửa sổ trượt DPS_WINDOW giây.
    """
    RADIUS   = 24
    XP_VALUE = 0
    COLOR    = (210, 210, 220)
    DPS_WINDOW = 1.0   # giây — cửa sổ trượt để tính DPS

    def __init__(self, x: float, y: float):
        super().__init__(x, y)
        # "Vô hạn máu" đạt được bằng cách take_damage KHÔNG trừ máu (xem dưới),
        # nên max_hp giữ ở mức 1 quái mạnh thật sự để các hiệu ứng theo % máu
        # (VD burn 5-stack = 5% max HP/s) cho ra con số DPS đúng tầm, không nổ
        # thành hàng tỉ như khi để max_hp khổng lồ.
        self.max_hp = 1000.0
        self.hp     = self.max_hp
        self.damage = 0.0             # không gây hại nếu player đụng vào
        self.state  = 'idle'
        self.total_damage = 0.0       # tổng damage đã nhận
        self._dps_window: list[list] = []   # [[thời gian còn lại, lượng dmg], ...]
        self.dps = 0.0

    def update(self, dt: float, player_x: float, player_y: float) -> None:
        # Đứng yên: chỉ tick hurt (animation trúng đòn), status effect (DoT vẫn
        # gây damage → cộng vào DPS), và cập nhật cửa sổ DPS. Không di chuyển.
        self.hurt_timer = max(0.0, self.hurt_timer - dt)

        active = []
        for eff in self.status_effects:
            eff.update(self, dt)   # burn/chill gọi take_damage(flinch=False)
            if not eff.is_expired():
                active.append(eff)
        self.status_effects = active

        # Trượt cửa sổ DPS
        for entry in self._dps_window:
            entry[0] -= dt
        self._dps_window = [e for e in self._dps_window if e[0] > 0.0]
        self.dps = sum(e[1] for e in self._dps_window) / self.DPS_WINDOW

    def take_damage(self, amount: float, flinch: bool = True) -> None:
        if amount <= 0:
            return
        self.total_damage += amount
        self._dps_window.append([self.DPS_WINDOW, amount])
        if flinch:
            self.hurt_timer = 0.3
        # Không trừ máu / không chết — hp giữ nguyên "vô hạn"

    def drop_xp(self, lucky: float = 0.0) -> list:
        return []
