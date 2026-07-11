from logic.rune.rune_component import ModifierRune

class HasteRune(ModifierRune):
    """
    Rune Tốc Độ — passive giảm cooldown chiêu chứa nó.
    Mỗi stack: giảm thêm 20% fire rate (tối thiểu 0.1s).
    Không ảnh hưởng đạn (on_update / on_fire / on_hit đều rỗng).
    """

    REDUCTION_PER_STACK = 0.20   # giảm 20% mỗi stack
    MIN_FIRE_RATE       = 0.10   # giới hạn tối thiểu (giây)
    BASE_FIRE_RATE      = 0.50   # fire rate mặc định của chiêu
    POINT_COST          = 1      # passive nhẹ — rẻ

    def on_hit(self, bullet, enemy, context: dict) -> None:
        pass

    def on_update(self, bullet, dt: float, context: dict = None) -> None:
        pass

    def on_fire(self, bullet, context: dict) -> list:
        return []

    def calc_fire_rate(self) -> float:
        """Trả về fire rate sau khi áp dụng stack giảm."""
        reduction = 1.0 - self.REDUCTION_PER_STACK * self.stack
        return max(self.MIN_FIRE_RATE,
                   self.BASE_FIRE_RATE * reduction)

    def get_display_name(self) -> str: return "Haste Rune"
    def get_description(self) -> str:
        pct = int(self.REDUCTION_PER_STACK * 100 * self.stack)
        return f"Reduces spell cooldown by {pct}% (Cost: {self.POINT_COST})"
    def get_color(self) -> tuple: return (100, 220, 255)
