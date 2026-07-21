import math


class SpellBuild:
    """Một chiêu riêng: có slot rune, RuneTree, và cooldown độc lập."""

    BASE_FIRE_RATE      = 0.5    # giây giữa 2 lần bắn mặc định (Ice/Lightning/Wind)
    FIRE_BASE_FIRE_RATE = 0.22   # Fire: đánh nhanh — bù lại tầm ngắn (xem FIRE_BULLET_LIFETIME)

    def __init__(self, name: str, slot_defs=None):
        from logic.rune.rune_slots import RuneSlots

        self.name       = name
        self.rune_slots = RuneSlots(slot_defs)
        self.rune_tree  = self.rune_slots.build_rune_tree()
        self.fire_timer = 0.0        # giây còn lại trước khi bắn được
        self.fire_rate  = self.BASE_FIRE_RATE  # có thể bị ảnh hưởng bởi HasteRune

    def tick(self, dt: float) -> None:
        """Giảm cooldown mỗi frame."""
        self.fire_timer = max(0.0, self.fire_timer - dt)

    def can_fire(self) -> bool:
        return self.fire_timer <= 0.0

    def reset_fire_timer(self) -> None:
        self.fire_timer = self.fire_rate

    def rebuild_rune_tree(self) -> None:
        self.rune_tree = self.rune_slots.build_rune_tree()
        self._recalculate_fire_rate()

    def _recalculate_fire_rate(self) -> None:
        from logic.rune.modifiers.haste_rune import HasteRune
        from logic.rune.elements.fire_rune import FireRune
        core = self.rune_slots.get(0).rune
        self.fire_rate = self.FIRE_BASE_FIRE_RATE if isinstance(core, FireRune) else self.BASE_FIRE_RATE
        for s in self.rune_slots.slots:
            if isinstance(s.rune, HasteRune) and self.rune_slots.is_active(s.id):
                self.fire_rate = s.rune.calc_fire_rate()
                break   # chỉ 1 HasteRune cho 1 chiêu

    def get_all_runes(self) -> list:
        return self.rune_tree.get_all_runes()


class Player:
    RADIUS         = 15
    BASE_HP        = 100
    BASE_SPEED     = 200
    BASE_FIRE_RATE = 0.5
    BASE_DAMAGE    = 20
    LIGHTNING_OVERLOAD_SPEED_MULT = 1.35
    MOVE_ACCEL     = 1900.0
    MOVE_FRICTION  = 2600.0
    STOP_EPSILON   = 3.0

    def __init__(self, x=0.0, y=0.0):
        self.x          = float(x)
        self.y          = float(y)
        self.vel_x      = 0.0
        self.vel_y      = 0.0
        self.move_speed_ratio = 0.0
        self.radius     = Player.RADIUS
        self.max_hp     = Player.BASE_HP
        self.hp         = float(Player.BASE_HP)
        self.speed      = Player.BASE_SPEED
        self.fire_rate  = Player.BASE_FIRE_RATE
        self.damage     = Player.BASE_DAMAGE
        self.alive      = True
        self.is_moving  = False
        self.facing_dir = 1
        self.dash_timer = 0.0
        self.dash_duration = 0.0
        self.dash_vel_x = 0.0
        self.dash_vel_y = 0.0
        self.hurt_timer = 0.0
        self.attack_timer = 0.0
        self.cast_lock_timer = 0.0
        self.cast_anim = None   # None | 'fire' — renderer chọn animation vung tay khi cast
        self.lightning_overload = 0.0
        self.lightning_overloaded = False
        self.noclip_mode = False
        self.lives = 3

        # Chỉ số stats (nâng qua StatUpgrade)
        self.armor    = 0.0    # % giảm damage nhận (tối đa 75%)
        self.hp_regen = 0.0    # HP hồi mỗi giây
        self.xp_range = 0.0    # px cộng thêm vào XPOrb.MAGNET_RADIUS
        self.lucky    = 0.0    # điểm may mắn (0-100): crit + rarity + XP drops

        # Ultimate
        self.ultimate_cooldown = 8.0   # giây
        self.ultimate_timer    = 0.0   # giây còn lại (> 0 → đang hồi)

        # Movement ability (mặc định: Dash)
        from logic.abilities.movement.dash_ability import DashAbility
        self.movement_ability = DashAbility()

        # Rune Builder system: 2 chiêu riêng, mỗi chiêu có cây rune riêng.
        self.rune_inventory: list = []   # Chỉ chứa modifier rune (element đã gán lúc chọn đầu game)
        self.spells = [
            SpellBuild("Spell 1"),
            SpellBuild("Spell 2"),
        ]
        self.active_spell_index = 0

        # Leveling
        self.level      = 1
        self.xp         = 0
        self.xp_to_next = 30

        # Thông báo "có rune mới" để HUD hiển thị
        self.has_new_rune = False

    # ── Movement & fire ───────────────────────────────────────────────────────

    def update(self, dt: float, move_x: float, move_y: float) -> None:
        """
        Cập nhật trạng thái của người chơi mỗi frame.
        - Xử lý gia tốc, ma sát để tính toán vận tốc (vel_x, vel_y) mượt mà dựa vào move_x, move_y nhận được.
        - Cập nhật tọa độ (x, y) mới.
        - Giảm dần thời gian chờ của các kỹ năng (cooldown chiêu, lướt, bất tử tạm thời).
        
        👉 BƯỚC TIẾP THEO (Bước 9): Sau khi cập nhật người chơi, vòng lặp _update của GameLoop sẽ gọi cập nhật Quái Vật. Hãy mở [logic/entities/enemy.py](file:///c:/Users/acer/Downloads/OOP-mihu_branch/logic/entities/enemy.py) hàm `update` để xem AI quái hoạt động thế nào.
        """
        move_len = math.hypot(move_x, move_y)
        cast_locked = self.cast_lock_timer > 0
        if move_x < 0:
            self.facing_dir = -1
        elif move_x > 0:
            self.facing_dir = 1

        move_speed = self.speed
        if getattr(self, "noclip_mode", False):
            move_speed *= 3.5
        elif self.lightning_overloaded:
            move_speed *= self.LIGHTNING_OVERLOAD_SPEED_MULT

        dash_active = self.dash_timer > 0
        if dash_active:
            dash_ratio = self.dash_timer / max(self.dash_duration, 0.001)
            dash_scale = 0.35 + 0.65 * dash_ratio
            self.vel_x = self.dash_vel_x * dash_scale
            self.vel_y = self.dash_vel_y * dash_scale
        elif cast_locked:
            self.vel_x = 0.0
            self.vel_y = 0.0
        elif move_len > 0:
            move_x /= move_len
            move_y /= move_len
            self.vel_x = self._approach(self.vel_x, move_x * move_speed, self.MOVE_ACCEL * dt)
            self.vel_y = self._approach(self.vel_y, move_y * move_speed, self.MOVE_ACCEL * dt)
        else:
            self.vel_x = self._approach(self.vel_x, 0.0, self.MOVE_FRICTION * dt)
            self.vel_y = self._approach(self.vel_y, 0.0, self.MOVE_FRICTION * dt)

        if abs(self.vel_x) < self.STOP_EPSILON:
            self.vel_x = 0.0
        if abs(self.vel_y) < self.STOP_EPSILON:
            self.vel_y = 0.0

        self.x += self.vel_x * dt
        self.y += self.vel_y * dt
        current_speed = math.hypot(self.vel_x, self.vel_y)
        self.move_speed_ratio = min(1.0, current_speed / max(move_speed, 1.0))
        self.is_moving = current_speed > self.STOP_EPSILON and not cast_locked
        self.dash_timer = max(0.0, self.dash_timer - dt)
        if self.dash_timer <= 0:
            self.dash_vel_x = 0.0
            self.dash_vel_y = 0.0
        self.hurt_timer = max(0.0, self.hurt_timer - dt)
        self.attack_timer = max(0.0, self.attack_timer - dt)
        self.cast_lock_timer = max(0.0, self.cast_lock_timer - dt)
        # Tick cooldown tất cả chiêu mỗi frame
        for spell in self.spells:
            spell.tick(dt)
        # Tick movement ability
        self.movement_ability.tick(dt)
        # Tick ultimate cooldown
        if self.ultimate_timer > 0:
            self.ultimate_timer = max(0.0, self.ultimate_timer - dt)
        # HP regen
        if self.hp_regen > 0 and self.alive:
            self.hp = min(self.max_hp, self.hp + self.hp_regen * dt)

    @staticmethod
    def _approach(current: float, target: float, amount: float) -> float:
        if current < target:
            return min(current + amount, target)
        if current > target:
            return max(current - amount, target)
        return current

    # Backward compat: fire_timer trỏ vào chiêu đang active
    @property
    def fire_timer(self) -> float:
        return self.get_active_spell().fire_timer

    @fire_timer.setter
    def fire_timer(self, value: float) -> None:
        self.get_active_spell().fire_timer = value

    def get_crit_chance(self) -> float:
        """Cơ hội chí mạng (0.0 – 1.0) dựa theo lucky."""
        return min(0.40, self.lucky * 0.004)

    def can_ultimate(self) -> bool:
        return self.ultimate_timer <= 0.0

    def reset_ultimate(self) -> None:
        self.ultimate_timer = self.ultimate_cooldown

    def can_fire(self) -> bool:
        return self.get_active_spell().can_fire()

    def reset_fire_timer(self) -> None:
        self.get_active_spell().reset_fire_timer()

    # ── HP ────────────────────────────────────────────────────────────────────

    def take_damage(self, amount: float) -> None:
        if getattr(self, "noclip_mode", False) or getattr(self, "god_mode", False):
            return
        reduced = amount * (1.0 - self.armor / 100.0)
        self.hp -= reduced
        if reduced > 0 and self.alive:
            self.hurt_timer = 0.35
        if self.hp <= 0:
            self.hp = 0
            if self.lives > 0:
                self.hp = self.max_hp
                self.lives -= 1 
            else:
                self.alive = False

    # ── XP ────────────────────────────────────────────────────────────────────

    def add_xp(self, amount: int) -> bool:
        self.xp     += amount
        leveled_up   = False
        while self.xp >= self.xp_to_next:
            self.level      += 1
            self.xp         -= self.xp_to_next
            self.xp_to_next  = int(self.xp_to_next * 1.4)
            leveled_up       = True
        return leveled_up

    # ── Rune Builder ──────────────────────────────────────────────────────────

    def add_to_inventory(self, rune) -> None:
        """Thêm rune vào inventory (chưa đặt vào cây)."""
        self.rune_inventory.append(rune)
        self.has_new_rune = True

    def setup_spells(self, element_runes: list) -> None:
        """Khởi tạo các chiêu theo danh sách ElementRune đã chọn đầu ván.

        Mỗi chiêu nhận 1 element vào lõi (slot 0) khóa cứng, dùng layout cây
        riêng của hệ đó. Người chơi chỉ gắn modifier vào nhánh.
        """
        from logic.rune.rune_slots import slot_defs_for_rune
        self.spells = []
        for i, rune in enumerate(element_runes):
            sb = SpellBuild(f"Spell {i + 1}", slot_defs=slot_defs_for_rune(rune))
            sb.rune_slots.set_core(rune)
            sb.rebuild_rune_tree()
            self.spells.append(sb)
        self.active_spell_index = 0

    def get_active_spell(self) -> SpellBuild:
        return self.spells[self.active_spell_index]

    def set_active_spell(self, index: int) -> bool:
        if index < 0 or index >= len(self.spells):
            return False
        self.active_spell_index = index
        return True

    @property
    def rune_slots(self):
        """Backward compat: slot của chiêu đang active."""
        return self.get_active_spell().rune_slots

    @property
    def rune_tree(self):
        """Backward compat: RuneTree của chiêu đang active."""
        return self.get_active_spell().rune_tree

    def rebuild_rune_tree(self) -> None:
        """Backward compat: rebuild chiêu đang active."""
        self.get_active_spell().rebuild_rune_tree()

    def rebuild_all_spells(self) -> None:
        for spell in self.spells:
            spell.rebuild_rune_tree()

    # ── Ratio ─────────────────────────────────────────────────────────────────

    def get_hp_ratio(self) -> float: return self.hp / self.max_hp
    def get_xp_ratio(self) -> float: return self.xp / self.xp_to_next
