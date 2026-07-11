import math
import random

from logic.rune.rune_component import ModifierRune
from logic.rune.modifiers.self_centered_modifier import orbit_steer

class _OrbitingBladeMovement(ModifierRune):
    """Behavior nội bộ (không vào ALL_RUNES) — gắn vào cây rune riêng của mỗi
    tia kiếm để lái nó quay quanh nguồn mỗi frame."""
    def on_fire(self, bullet, context: dict) -> list:
        return []

    def on_update(self, bullet, dt: float, context: dict = None) -> None:
        orbit_steer(bullet, dt)

    def on_hit(self, bullet, enemy, context: dict) -> None:
        pass

class FlashOfSwordsTrigger(ModifierRune):
    """
    Rune Trigger "Flash of Swords" (Rare Trigger, "Triggered on spawn") —
    THAM GIA CAST GRAPH: neo vào Trigger gần nhất phía trên, else Spell gốc.
    Mỗi khi cái nó neo vào spawn, nó phóng ra 1 tia kiếm QUAY QUANH NGUỒN của
    nó:
      - Damage 20%     : % damage gốc của Spell/Trigger phía trên.
      - Critical 5%    : có 5% chí mạng (x2 damage).
      - Length 4       : tia kiếm dài (bán kính va chạm to).
      - Orbit movement : tia quay quanh nguồn đã spawn ra nó.

    Vì có `trigger_once()` + `IS_CAST_GRAPH_TRIGGER`, nó chạy đúng trên cả 4 hệ:
      • Fire/Wind: nguồn là chính viên đạn/boomerang → tia kiếm quay THEO nó.
      • Ice/Lightning (đòn tức thời): không có đạn nguồn → tia quay quanh điểm cast.

    Nếu có Self-Centered neo vào NÓ (Flash làm cha, Self-Centered làm con): số
    tia +2 (rải quanh vòng) và thời lượng +150% — ra chùm kiếm cong quay quanh
    nguồn, đúng như đảo thứ tự 2 rune.
    """
    IS_CAST_GRAPH_TRIGGER = True
    IS_TRIGGER     = True
    TRIGGER_ON     = "spawn"
    # Lưỡi kiếm quay quanh nguồn → mọi Spawn Count (dù modifier con dùng đội hình
    # 'line'/'cone') phải RẢI ĐỀU quanh vòng, nếu không kiếm ra lệch góc không
    # đều (xem RuneTree._orbit_even_batches).
    ORBIT_EVEN_SPACING = True

    DAMAGE_PERCENT = 0.20
    CRIT_CHANCE    = 0.05
    CRIT_MULT      = 2.0
    LENGTH         = 4       # chỉ số "Length" hiển thị trên thẻ (độ dài tia kiếm)
    ORBIT_RADIUS   = 42.0    # = ĐỘ DÀI lưỡi kiếm: gốc ở viên đạn, mũi vươn ra 42px
    ORBIT_SPEED_DEG = 300.0  # độ/giây — quay nhanh, vun vút quanh nguồn
    BASE_DURATION  = 2.0     # giây tia kiếm tồn tại (trước duration_mult)
    BLADE_RADIUS   = 14.0    # Length 4 → tia kiếm dài, hitbox to
    POINT_COST     = 2       # Rare Trigger

    # Toàn bộ hiệu ứng đi qua trigger_once (cast graph) — on_fire/on_update rỗng.
    def on_fire(self, bullet, context: dict) -> list:
        return []

    def on_update(self, bullet, dt: float, context: dict = None) -> None:
        pass

    def trigger_once(self, x: float, y: float, base_damage: float, context: dict,
                     dir_x: float = None, dir_y: float = None,
                     angle_jitter_deg: float = 0.0,
                     speed_mult: float = 1.0, size_mult: float = 1.0,
                     duration_mult: float = 1.0, source=None):
        """Tạo 1 tia kiếm QUAY QUANH NGUỒN tại (x, y) và TRẢ VỀ (người gọi thêm
        vào danh sách đạn). source: đối tượng để quay quanh (boomerang/đạn) —
        None thì quay quanh chính điểm cast (Ice/Lightning)."""
        from logic.entities.bullet import Bullet
        from logic.rune.rune_tree import RuneTree

        cx = source.x if source is not None else x
        cy = source.y if source is not None else y
        dist = math.hypot(x - cx, y - cy)
        if dist > 1.0:
            # Đã được rải sẵn ra vòng (VD ring batch của Self-Centered).
            orbit_radius = dist
            orbit_angle  = math.atan2(y - cy, x - cx)
        else:
            # Bản gốc trùng nguồn → tự đẩy ra vòng bán kính mặc định.
            orbit_radius = self.ORBIT_RADIUS
            base = math.atan2(dir_y, dir_x) if (dir_x or dir_y) else 0.0
            orbit_angle = base + math.radians(angle_jitter_deg)
            x = cx + math.cos(orbit_angle) * orbit_radius
            y = cy + math.sin(orbit_angle) * orbit_radius

        damage = base_damage * self.stack
        is_crit = random.random() < self.CRIT_CHANCE
        if is_crit:
            damage *= self.CRIT_MULT

        tree = RuneTree()
        tree.add_modifier(_OrbitingBladeMovement())
        blade = Bullet(x, y, x + 1.0, y, damage, tree)
        blade.visual_type      = 'sword_beam'
        blade.is_crit          = is_crit
        blade.radius           = self.BLADE_RADIUS * size_mult
        blade.LIFETIME         = self.BASE_DURATION * duration_mult
        blade.pierce_remaining = 9999          # tia quay xuyên qua địch
        blade._orbit           = True
        blade._orbit_radius    = orbit_radius
        blade._orbit_angle     = orbit_angle
        blade._orbit_speed_deg = self.ORBIT_SPEED_DEG   # quay vừa phải, không quá nhanh
        blade._orbit_target    = source        # theo nguồn (boomerang) mỗi frame
        blade.player_x         = cx
        blade.player_y         = cy
        return blade

    def get_display_name(self) -> str: return "Flash of Swords"

    def get_description(self) -> str:
        # Khớp y chang thẻ gốc (nội dung + format bullet ◆, mỗi stat 1 dòng).
        pct  = int(self.DAMAGE_PERCENT * 100 * self.stack)
        crit = int(self.CRIT_CHANCE * 100)
        return ("Casts a beam orbiting its source.\n"
                f"◆ Damage: {pct}%\n"
                f"◆ Critical chance: {crit}%\n"
                f"◆ Length: {self.LENGTH}\n"
                "◆ Orbit movement")

    def get_color(self) -> tuple: return (200, 220, 255)
