from logic.rune.rune_component import ModifierRune

class LightenedHeartModifier(ModifierRune):
    """
    Rune Trái Tim Nhẹ — đạn bay nhanh hơn, đổi lại nhỏ hơn (hitbox + hình ảnh).
    Stack: mỗi bản cộng dồn cả 2 hiệu ứng (nhân dồn qua từng lần on_fire).
    """
    SPEED_BONUS_PER_STACK    = 0.40   # +40% tốc độ mỗi stack
    SIZE_REDUCTION_PER_STACK = 0.20   # -20% kích cỡ mỗi stack
    MIN_SIZE_MULT = 0.2               # sàn kích cỡ — tránh hitbox về 0/âm
    POINT_COST = 1                    # buff tốc độ + đổi lại nhược điểm — rẻ
    ON_FIRE_PRIORITY = 10             # buff thuần → áp TRƯỚC spawner/trigger (xem ModifierRune)

    def on_fire(self, bullet, context: dict) -> list:
        speed_mult = 1.0 + self.SPEED_BONUS_PER_STACK * self.stack
        size_mult  = max(self.MIN_SIZE_MULT,
                        1.0 - self.SIZE_REDUCTION_PER_STACK * self.stack)
        bullet.vx     *= speed_mult
        bullet.vy     *= speed_mult
        bullet.radius *= size_mult
        return []

    def on_update(self, bullet, dt: float, context: dict = None) -> None:
        pass

    def get_display_name(self) -> str: return "Lightened Heart"

    def get_description(self) -> str:
        pct_speed = int(self.SPEED_BONUS_PER_STACK * 100 * self.stack)
        pct_size  = int(self.SIZE_REDUCTION_PER_STACK * 100 * self.stack)
        return f"Speed +{pct_speed}%, Size -{pct_size}% (Cost: {self.POINT_COST})"

    def get_color(self) -> tuple: return (120, 220, 150)
