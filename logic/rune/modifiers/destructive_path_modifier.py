import math

from logic.rune.rune_component import ModifierRune

class DestructivePathModifier(ModifierRune):
    """
    Rune "Con Đường Hủy Diệt" — để lại vệt lửa dọc đường đạn bay, mỗi vệt tồn
    tại TRAIL_DURATION giây và áp 1 Burn cho địch đứng vào.

    - Đạn có quỹ đạo (Fire/Wind): để vệt NGAY lúc bắn + để thêm mỗi
      TRAIL_INTERVAL px đã bay (qua on_update, giống cơ chế của
      FuriousOutburstModifier nhưng để lại vệt ĐỨNG YÊN thay vì bắn cầu lửa).
    - Lightning/Ice (đòn tức thời): cũng có `trigger_once()` nên tự động được
      game_loop._find_triggerable_modifiers() gọi 1 lần mỗi cast (dùng chung
      cơ chế Trigger tổng quát, dù đây là Modifier chứ không phải Trigger).
    """
    TRAIL_INTERVAL = 45.0    # px giữa 2 vệt lửa liên tiếp
    TRAIL_DURATION = 1.0     # giây mỗi vệt tồn tại
    TRAIL_RADIUS   = 30.0    # bán kính vùng gây Burn
    BURN_STACK     = 1
    POINT_COST     = 1       # Common Modifier — rẻ

    # ── Đạn có quỹ đạo (Fire / Wind) ─────────────────────────────────────────

    def on_fire(self, bullet, context: dict) -> list:
        bullet._trail_traveled = 0.0
        self.trigger_once(bullet.x, bullet.y, bullet.damage, context)
        return []

    def on_update(self, bullet, dt: float, context: dict = None) -> None:
        if context is None:
            return
        speed = math.hypot(bullet.vx, bullet.vy)
        traveled = getattr(bullet, '_trail_traveled', 0.0) + speed * dt
        while traveled >= self.TRAIL_INTERVAL:
            traveled -= self.TRAIL_INTERVAL
            self.trigger_once(bullet.x, bullet.y, bullet.damage, context)
        bullet._trail_traveled = traveled

    # ── Trigger dùng chung (kể cả Lightning/Ice/Wind qua game_loop) ──────────

    def trigger_once(self, x: float, y: float, base_damage: float, context: dict,
                     dir_x: float = None, dir_y: float = None) -> None:
        """Để lại 1 vệt lửa tại (x, y). dir_x/dir_y không dùng — vệt đứng yên."""
        from logic.entities.attack_effect import AoEBurst
        from logic.rune.rune_tree import RuneTree
        from logic.rune.elements.fire_rune import FireRune

        fire = FireRune()
        fire.element_stack = self.BURN_STACK
        tree = RuneTree()
        tree.add_element(fire)

        # Vệt lửa không gây damage trực tiếp (chỉ áp Burn) — khớp mô tả
        # "Leaves a trail of fire ... and applies 1 Burn" (không có %damage).
        patch = AoEBurst(x, y, 0.0, self.TRAIL_RADIUS,
                         visual_type='fire_bolt_hit', rune_tree=tree)

        # Ép tổng vòng đời (grow+active+fade) = đúng TRAIL_DURATION giây.
        default_total = AoEBurst.GROW_DUR + AoEBurst.ACTIVE_DUR + AoEBurst.FADE_DUR
        scale = self.TRAIL_DURATION / default_total
        patch.GROW_DUR   *= scale
        patch.ACTIVE_DUR *= scale
        patch.FADE_DUR   *= scale
        patch.TOTAL_LIFE  = patch.GROW_DUR + patch.ACTIVE_DUR + patch.FADE_DUR

        active_effects = context.get('active_effects')
        if active_effects is not None:
            active_effects.append(patch)

    def get_display_name(self) -> str: return "Destructive Path"

    def get_description(self) -> str:
        return (f"Leaves a trail of fire that lasts {self.TRAIL_DURATION:.0f}s "
                f"and applies {self.BURN_STACK} Burn (Cost: {self.POINT_COST})")

    def get_color(self) -> tuple: return (255, 120, 50)
