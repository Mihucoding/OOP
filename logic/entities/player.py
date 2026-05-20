import math


class SpellBuild:
    """Một chiêu riêng: có slot rune, RuneTree, và cooldown độc lập."""

    BASE_FIRE_RATE = 0.5   # giây giữa 2 lần bắn mặc định

    def __init__(self, name: str):
        from logic.rune.rune_slots import RuneSlots

        self.name       = name
        self.rune_slots = RuneSlots()
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
        self.fire_rate = self.BASE_FIRE_RATE
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

    def __init__(self, x=0.0, y=0.0):
        self.x          = float(x)
        self.y          = float(y)
        self.radius     = Player.RADIUS
        self.max_hp     = Player.BASE_HP
        self.hp         = float(Player.BASE_HP)
        self.speed      = Player.BASE_SPEED
        self.fire_rate  = Player.BASE_FIRE_RATE
        self.damage     = Player.BASE_DAMAGE
        self.alive      = True

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

        # Rune Builder system: 3 chiêu riêng, mỗi chiêu có cây rune riêng.
        self.rune_inventory: list = []   # Rune chưa đặt vào cây
        self.spells = [
            SpellBuild("Chiêu 1"),
            SpellBuild("Chiêu 2"),
            SpellBuild("Chiêu 3"),
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
        move_len = math.hypot(move_x, move_y)
        if move_len > 0:
            move_x /= move_len
            move_y /= move_len
        self.x += move_x * self.speed * dt
        self.y += move_y * self.speed * dt
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
        reduced = amount * (1.0 - self.armor / 100.0)
        self.hp -= reduced
        if self.hp <= 0:
            self.hp    = 0
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
