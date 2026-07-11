from logic.rune.rune_component import ModifierRune

class StarsAlignedModifier(ModifierRune):
    """
    Rune "Sao Thẳng Hàng" — cùng luật neo với FreneticEnergyModifier (gắn vào
    Trigger gần nhất phía trên, else Spell gốc), nhưng dàn các bản sao THẲNG
    HÀNG (vuông góc hướng bay, cùng hướng) thay vì toả ngẫu nhiên trong cone,
    và còn tăng tốc + thu nhỏ kích thước:
      - Casts spawns in a line
      - Spawn Count +2
      - Damage x0.7
      - Speed x1.3
      - Size x0.5

    Hoạt động trên cả 4 hệ (xem FreneticEnergyModifier — cùng cơ chế cast graph).

    Đóng góp qua add_batch() (không ghi đè batch của rune khác) — nếu cùng
    gắn vào 1 cast với Frenetic Energy, 2 rune vẫn giữ ĐÚNG đội hình riêng
    (line dàn hàng của Stars Aligned không lẫn với cone toả ngẫu nhiên của
    Frenetic).
    """
    SPAWN_COUNT_DELTA = 2
    DAMAGE_MULT       = 0.7
    SPEED_MULT        = 1.3
    SIZE_MULT         = 0.5
    LINE_SPACING      = 34.0
    POINT_COST        = 2   # Rare Modifier — mạnh hơn Frenetic (Common)

    def contribute_cast(self, cast_params) -> None:
        """Gọi bởi RuneTree._walk_cast_graph — chỉnh tham số của cái mình gắn vào."""
        cast_params.damage_mult *= self.DAMAGE_MULT ** self.stack
        cast_params.speed_mult  *= self.SPEED_MULT ** self.stack
        cast_params.size_mult   *= self.SIZE_MULT ** self.stack
        cast_params.add_batch(self.SPAWN_COUNT_DELTA * self.stack, 'line', self.LINE_SPACING)

    # Không tham gia hệ on_fire/on_update cũ — toàn bộ hiệu ứng đi qua contribute_cast.
    def on_fire(self, bullet, context: dict) -> list:
        return []

    def on_update(self, bullet, dt: float, context: dict = None) -> None:
        pass

    def get_display_name(self) -> str: return "Stars Aligned"

    def get_description(self) -> str:
        # Khớp y chang thẻ gốc (nội dung + format bullet ◆, mỗi stat 1 dòng).
        n   = self.SPAWN_COUNT_DELTA * self.stack
        dmg = self.DAMAGE_MULT ** self.stack
        return ("Casts spawns in a line\n"
                f"◆ Spawn Count +{n}\n"
                f"◆ Damage x{dmg:.1f}\n"
                f"◆ Speed x{self.SPEED_MULT}\n"
                f"◆ Size x{self.SIZE_MULT}")

    def get_color(self) -> tuple: return (230, 200, 90)
