import math
import random

from logic.rune.rune_component import ModifierRune

class RollingStoneModifier(ModifierRune):
    """
    Rune Trigger "Triggered on spawn" — nổ đúng 1 lần mỗi lần cast (không lặp
    lại theo quãng đường như FuriousOutburstModifier), tung ra 1 tảng đá lăn
    xuyên qua nhiều địch trong DURATION giây.

    - Fire/Wind (có Bullet/WindBoomerang thật): gọi lúc bắn (on_fire).
    - Lightning/Ice (đòn tức thời): game_loop tự dò rune này qua
      `_find_triggerable_modifiers()` rồi gọi thẳng `trigger_once()`.
    """
    IS_TRIGGER     = True
    TRIGGER_ON     = "spawn"
    DAMAGE_PERCENT = 0.25   # % damage gốc của chiêu
    DURATION       = 5.0    # giây đá lăn tồn tại
    ROLL_RADIUS    = 22.0   # bán kính va chạm — to hơn đạn thường
    ROLL_SPEED     = 220.0  # pixel/giây — lăn chậm nhưng dai
    POINT_COST     = 1      # Trigger "Common" trong thẻ tham khảo — rẻ hơn Outburst

    # ── Đạn có quỹ đạo (Fire) ────────────────────────────────────────────────

    def on_fire(self, bullet, context: dict) -> list:
        # KHÔNG tự append vào context — trả boulder ra qua return để RuneTree
        # tiếp tục áp rune con (VD HeavyHitter) lên đúng viên đá này, bất kể
        # RollingStone đứng cha hay con trong cây.
        boulder = self.trigger_once(bullet.x, bullet.y, bullet.damage, context,
                                    dir_x=bullet.vx, dir_y=bullet.vy)
        return [boulder] if boulder is not None else []

    def on_update(self, bullet, dt: float, context: dict = None) -> None:
        pass   # chỉ nổ lúc spawn — không lặp theo quãng đường

    # ── Trigger dùng chung cho mọi hệ (kể cả Wind/Lightning/Ice) ─────────────

    def trigger_once(self, x: float, y: float, base_damage: float, context: dict,
                     dir_x: float = None, dir_y: float = None,
                     duration_mult: float = 1.0, source=None, **_extra):
        """Tạo 1 tảng đá lăn tại (x, y) và TRẢ VỀ (không tự append). Người gọi
        chịu trách nhiệm thêm vào danh sách đạn. dir_x/dir_y: hướng lăn (None
        → ngẫu nhiên)."""
        from logic.entities.bullet import Bullet

        if dir_x is None or dir_y is None or math.hypot(dir_x, dir_y) < 1e-6:
            angle = random.uniform(0.0, math.tau)
            ux, uy = math.cos(angle), math.sin(angle)
        else:
            d = math.hypot(dir_x, dir_y)
            ux, uy = dir_x / d, dir_y / d

        boulder = Bullet(x, y, x + ux * 100.0, y + uy * 100.0,
                         base_damage * self.DAMAGE_PERCENT * self.stack, None)
        boulder.vx, boulder.vy   = ux * self.ROLL_SPEED, uy * self.ROLL_SPEED
        boulder.radius           = self.ROLL_RADIUS
        boulder.LIFETIME         = self.DURATION
        boulder.pierce_remaining = 999   # lăn xuyên qua gần như vô hạn địch trong 5s
        boulder.visual_type      = 'rolling_boulder'
        return boulder

    def get_display_name(self) -> str: return "Rolling Stone"

    def get_description(self) -> str:
        pct = int(self.DAMAGE_PERCENT * 100 * self.stack)
        return (f"On cast, rolls a boulder for {int(self.DURATION)}s: "
                f"{pct}% dmg, pierces (Cost: {self.POINT_COST})")

    def get_color(self) -> tuple: return (150, 120, 90)
