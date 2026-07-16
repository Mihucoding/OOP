import math
import random

from logic.rune.rune_component import ModifierRune

class FuriousOutburstModifier(ModifierRune):
    """
    Rune Bộc Phát Giận Dữ — nổ thêm cầu lửa nhỏ theo quãng đường đạn đã bay.

    Cơ chế "Triggered on distance":
    - Đạn có quỹ đạo di chuyển thật (Fire/Wind) → nổ 1 quả NGAY lúc bắn,
      rồi nổ thêm mỗi TRIGGER_DISTANCE px đã bay (qua on_update, cần context
      để tự thêm đạn cầu lửa vào context['bullets']).
    - Lightning/Ice không có "quãng đường bay" (beam tức thời / spike sạc-thả)
      nên game_loop gọi thẳng `trigger_once()` — chỉ nổ 1 quả mỗi lần cast,
      không lặp lại dù giữ chuột lâu.

    Mỗi quả cầu lửa phụ = 1 Bullet nhỏ mang FireRune riêng (tái dùng burn có sẵn).
    """
    IS_TRIGGER       = True
    TRIGGER_ON       = "distance"
    OWNS_SUBTREE     = True     # nhánh con áp lên từng cầu lửa, không lên đạn cha
    TRIGGER_DISTANCE = 120.0   # px giữa 2 lần nổ (đạn có quỹ đạo)
    DAMAGE_PERCENT   = 0.20    # % damage gốc của đạn/chiêu
    BURN_STACK       = 1
    POINT_COST       = 2       # hiệu ứng AoE liên tục — tốn điểm như Split/Bounce

    # ── Đạn có quỹ đạo (Fire / Wind) ─────────────────────────────────────────

    def on_fire(self, bullet, context: dict) -> list:
        bullet._outburst_traveled = 0.0
        # Trả fireball + đạn phụ do NHÁNH CON sinh ra (VD lưỡi kiếm Flash of
        # Swords quay quanh chính cầu lửa). Nhánh con (buff/cast-graph) được áp
        # lên cầu lửa qua _attach_subtree_and_fire, không đụng đạn chính.
        fireball = self.trigger_once(bullet.x, bullet.y, bullet.damage, context)
        if fireball is None:
            return []
        return [fireball] + self._attach_subtree_and_fire(fireball, context)

    def on_update(self, bullet, dt: float, context: dict = None) -> None:
        if context is None:
            return
        speed = math.hypot(bullet.vx, bullet.vy)
        traveled = getattr(bullet, '_outburst_traveled', 0.0) + speed * dt
        threshold = self.TRIGGER_DISTANCE
        while traveled >= threshold:
            traveled -= threshold
            fireball = self.trigger_once(bullet.x, bullet.y, bullet.damage, context)
            if fireball is not None:
                context['bullets'].append(fireball)
                # Mỗi cầu lửa đẻ dọc đường cũng mang nhánh con của nó
                context['bullets'].extend(
                    self._attach_subtree_and_fire(fireball, context))
        bullet._outburst_traveled = traveled

    # ── Đạn tức thời (Lightning / Ice) — game_loop gọi thẳng hàm này ─────────

    def trigger_once(self, x: float, y: float, base_damage: float, context: dict,
                     dir_x: float = None, dir_y: float = None,
                     duration_mult: float = 1.0, source=None, **_extra):
        """Tạo 1 quả cầu lửa tại (x, y) và TRẢ VỀ (không tự append). Người gọi
        (RuneTree khi ở trong cây, hoặc game_loop khi gọi thẳng cho Lightning/Ice)
        chịu trách nhiệm thêm vào danh sách đạn.
        dir_x/dir_y: không dùng (Outburst luôn nổ ngẫu nhiên hướng) — nhận vào
        để tương thích chữ ký chung với các rune Trigger khác (VD RollingStone)."""
        from logic.entities.bullet import Bullet
        from logic.rune.rune_tree import RuneTree
        from logic.rune.elements.fire_rune import FireRune

        angle = random.uniform(0.0, math.tau)
        tx = x + math.cos(angle) * 100.0
        ty = y + math.sin(angle) * 100.0

        fire = FireRune()
        fire.element_stack = self.BURN_STACK
        tree = RuneTree()
        tree.add_element(fire)

        fireball = Bullet(x, y, tx, ty, base_damage * self.DAMAGE_PERCENT * self.stack, tree)
        fireball.visual_type = 'fire_bolt'
        return fireball

    def get_display_name(self) -> str: return "Furious Outburst"

    def get_description(self) -> str:
        # Khớp y chang thẻ gốc (nội dung + format bullet ◆, mỗi stat 1 dòng).
        pct = int(self.DAMAGE_PERCENT * 100 * self.stack)
        return ("Casts fireballs in random directions.\n"
                f"◆ Damage: {pct}%\n"
                f"◆ Apply {self.BURN_STACK} Burn")

    def get_color(self) -> tuple: return (255, 140, 40)
