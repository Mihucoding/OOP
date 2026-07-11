import math

from logic.rune.rune_component import ModifierRune

ORBIT_SPEED = 220.0   # độ/giây quay quanh tâm (dùng chung cho Self-Centered + Flash blade)

def orbit_steer(bullet, dt: float) -> None:
    """Lái 1 viên đạn đang orbit: quay quanh tâm (bullet.player_x/player_y —
    game_loop đồng bộ mỗi frame; có thể là player hoặc NGUỒN spawn như
    boomerang) với bán kính bullet._orbit_radius. Tốc độ góc mặc định
    ORBIT_SPEED, nhưng có thể override riêng từng viên qua
    bullet._orbit_speed_deg (VD Flash of Swords quay chậm hơn Self-Centered).
    Đặt vx/vy để sau bullet.update (x += vx*dt) viên đạn nằm đúng trên vòng
    tròn. Thời lượng do Bullet.LIFETIME/elapsed lo, không cần đếm riêng ở đây."""
    if not getattr(bullet, '_orbit', False):
        return
    speed_deg = getattr(bullet, '_orbit_speed_deg', ORBIT_SPEED)
    bullet._orbit_angle += math.radians(speed_deg * dt)
    cx = getattr(bullet, 'player_x', bullet.x)
    cy = getattr(bullet, 'player_y', bullet.y)
    tx = cx + math.cos(bullet._orbit_angle) * bullet._orbit_radius
    ty = cy + math.sin(bullet._orbit_angle) * bullet._orbit_radius
    if dt > 0:
        bullet.vx = (tx - bullet.x) / dt
        bullet.vy = (ty - bullet.y) / dt

class SelfCenteredModifier(ModifierRune):
    """
    Rune "Tự Tâm" (Rare Modifier) — THAM GIA CAST GRAPH: gắn vào Trigger gần
    nhất phía trên, else Spell gốc (đúng luật Mystralia, giống Frenetic/Stars
    Aligned). Cái nó gắn vào sẽ:
      - Add Orbit movement : các bản của cast đó quay quanh tâm thay vì bay thẳng.
      - Spawn Count +2     : rải thêm 2 bản đều quanh vòng orbit.
      - Duration +150%     : nhân thời lượng bản spawn lên 2.5x.

    Nhờ tham gia cast graph, Self-Centered giờ TÔN TRỌNG cấu trúc cha-con:
      • Gắn thẳng Spell → các đạn CHÍNH quay quanh PLAYER (như cũ).
      • Gắn dưới 1 Trigger (VD Flash of Swords) → chỉ các bản của TRIGGER đó
        (tia kiếm) quay & nhân lên, KHÔNG đụng tới đạn chính. Với hệ gió, tia
        kiếm quay quanh chính boomerang đã spawn ra chúng (xem Flash of Swords).

    Đạn có quỹ đạo riêng (WindBoomerang: CAN_ORBIT=False) chỉ nhận +count/
    +duration chứ không bị ép quay (tránh đá nhau với quỹ đạo ra/về).
    """
    ORBIT_RADIUS             = 90.0   # pixel — bán kính quỹ đạo
    BASE_DURATION            = 2.5    # giây tồn tại gốc (trước khi +150%)
    DURATION_BONUS_PER_STACK = 1.50   # +150% thời lượng mỗi stack
    EXTRA_SPAWN_PER_STACK    = 2      # Spawn Count +2 mỗi stack
    POINT_COST = 2

    def contribute_cast(self, cast_params) -> None:
        """Gọi bởi RuneTree._walk_cast_graph — chỉnh cast mình gắn vào."""
        dur_mult = 1.0 + self.DURATION_BONUS_PER_STACK * self.stack
        cast_params.orbit          = True
        cast_params.orbit_radius   = self.ORBIT_RADIUS
        cast_params.orbit_duration = self.BASE_DURATION * dur_mult
        cast_params.duration_mult *= dur_mult
        cast_params.add_batch(self.EXTRA_SPAWN_PER_STACK * self.stack, 'ring', self.ORBIT_RADIUS)

    # Không tạo đạn qua on_fire nữa (toàn bộ đi qua contribute_cast). Nhưng vẫn
    # LÁI các đạn đã được bật orbit (chúng dùng chung cây rune này với Spell).
    def on_fire(self, bullet, context: dict) -> list:
        return []

    def on_update(self, bullet, dt: float, context: dict = None) -> None:
        orbit_steer(bullet, dt)

    def get_display_name(self) -> str: return "Self-Centered"

    def get_description(self) -> str:
        # Khớp y chang thẻ gốc (nội dung + format bullet ◆, mỗi stat 1 dòng).
        extra = self.EXTRA_SPAWN_PER_STACK * self.stack
        pct   = int(self.DURATION_BONUS_PER_STACK * 100 * self.stack)
        return ("◆ Add Orbit movement\n"
                f"◆ Spawn Count +{extra}\n"
                f"◆ Duration +{pct}%")

    def get_color(self) -> tuple: return (150, 190, 235)
