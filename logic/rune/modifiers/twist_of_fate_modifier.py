import math
from logic.rune.rune_component import ModifierRune

class TwistOfFateModifier(ModifierRune):
    """
    Rune "Vặn Xoắn Định Mệnh" (Common Modifier) — thay thế SpiralModifier cũ:
      - Add Spiral movement : quay vận tốc đạn mỗi frame.
      - Duration +1s        : đạn tồn tại lâu hơn (cộng thẳng vào LIFETIME).
      - Size x1.5 over lifetime: đạn LỚN DẦN theo thời gian sống, từ 1x lúc
        bắn ra tới x1.5 lúc gần hết đời (không phải phóng to ngay lập tức).

    Fire/Wind (đạn bay thật, có on_update mỗi frame): chạy đúng 3 hiệu ứng trên.
    Ice/Lightning (không có đạn bay, on_fire/on_update không được gọi tới):
    game_loop._has_spiral_modifier() dùng sự hiện diện của rune này làm công
    tắc chuyển gai/tia thẳng sang đòn xoáy vòng/vòng cung — kế thừa đúng vai
    trò cũ của SpiralModifier cho 2 hệ đó.
    Gắn dưới Flash of Swords (Trigger tham gia cast graph, không phải đạn bay
    thẳng): contribute_cast() cộng dồn vào CastParams.spiral_stack, Trigger đó
    tự đọc để bẻ cong lưỡi kiếm + cộng Duration/Size lên tia kiếm nó sinh ra
    (xem FlashOfSwordsTrigger.trigger_once/_OrbitingBladeMovement).
    """
    ROTATE_SPEED   = 180.0   # độ/giây — tốc độ xoay vận tốc (Fire/Wind)
    DURATION_BONUS = 1.0     # +1s mỗi stack
    SIZE_MULT      = 1.5     # x1.5 kích thước lúc gần hết đời, mỗi stack
    POINT_COST     = 1       # Common Modifier — rẻ

    # WindBoomerang không có field LIFETIME (dùng MAX_LIFE + phase out/pause/
    # return thay vì elapsed/LIFETIME đơn giản như Bullet) — cần đọc/ghi đúng
    # tên field theo từng loại đạn.
    @staticmethod
    def _duration_attr(bullet) -> str:
        return 'LIFETIME' if hasattr(bullet, 'LIFETIME') else 'MAX_LIFE'

    def contribute_cast(self, cast_params) -> None:
        # Gắn dưới 1 Trigger tham gia cast graph (VD Flash of Swords): tia
        # kiếm không có "vận tốc" để tự xoay như đạn thường, nên Trigger tự
        # đọc spiral_stack để quyết cách thể hiện "spiral" của riêng nó
        # (VD lưỡi kiếm bẻ cong hơn — xem FlashOfSwordsTrigger.trigger_once).
        cast_params.spiral_stack += self.stack

    def on_fire(self, bullet, context: dict) -> list:
        attr = self._duration_attr(bullet)
        setattr(bullet, attr, getattr(bullet, attr) + self.DURATION_BONUS * self.stack)
        return []

    def on_update(self, bullet, dt: float, context: dict = None) -> None:
        # Xoay vector vận tốc mỗi frame.
        angle_rad = math.radians(self.ROTATE_SPEED * self.stack * dt)
        cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
        vx_new = bullet.vx * cos_a - bullet.vy * sin_a
        vy_new = bullet.vx * sin_a + bullet.vy * cos_a
        bullet.vx, bullet.vy = vx_new, vy_new

        # Lớn dần theo thời gian sống — chốt bán kính GỐC ở lần update đầu
        # tiên (sau khi mọi rune khác đã áp size_mult xong trong on_fire/cast
        # graph), rồi nội suy tới SIZE_MULT lúc bullet.elapsed chạm duration.
        if not hasattr(bullet, '_twist_base_radius'):
            bullet._twist_base_radius = bullet.radius
        duration = getattr(bullet, self._duration_attr(bullet))
        ratio  = min(1.0, bullet.elapsed / max(0.001, duration))
        growth = 1.0 + (self.SIZE_MULT - 1.0) * self.stack * ratio
        bullet.radius = bullet._twist_base_radius * growth

    def get_display_name(self) -> str: return "Twist of Fate"

    def get_description(self) -> str:
        # Khớp y chang thẻ gốc (nội dung + format bullet ◆, mỗi stat 1 dòng).
        dur  = self.DURATION_BONUS * self.stack
        mult = 1.0 + (self.SIZE_MULT - 1.0) * self.stack
        return ("◆ Add Spiral movement\n"
                f"◆ Duration +{dur:.0f}s\n"
                f"◆ Increase Size by x{mult:.1f} over lifetime")

    def get_color(self) -> tuple: return (200, 150, 255)
