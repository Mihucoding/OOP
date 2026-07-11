from logic.rune.rune_component import ModifierRune

class HeavyHitterModifier(ModifierRune):
    """
    Rune Đòn Nặng — đổi tốc độ lấy sát thương.
    Stack: mỗi bản cộng dồn cả 2 hiệu ứng (nhân dồn qua từng lần on_fire).
    """
    DAMAGE_BONUS_PER_STACK = 0.50   # +50% damage mỗi stack
    SPEED_PENALTY_PER_STACK = 0.25  # -25% tốc độ mỗi stack
    MIN_SPEED_MULT = 0.25            # sàn tốc độ — tránh đạn gần như đứng yên
    POINT_COST = 2                   # buff damage mạnh — tốn điểm như Split/Bounce
    ON_FIRE_PRIORITY = 10            # buff thuần → áp TRƯỚC spawner/trigger (xem ModifierRune)

    def on_fire(self, bullet, context: dict) -> list:
        bullet.damage *= 1.0 + self.DAMAGE_BONUS_PER_STACK * self.stack
        speed_mult = max(self.MIN_SPEED_MULT,
                        1.0 - self.SPEED_PENALTY_PER_STACK * self.stack)
        bullet.vx *= speed_mult
        bullet.vy *= speed_mult
        return []

    def on_update(self, bullet, dt: float, context: dict = None) -> None:
        pass

    def get_display_name(self) -> str: return "Heavy Hitter"

    def get_description(self) -> str:
        pct_dmg   = int(self.DAMAGE_BONUS_PER_STACK * 100 * self.stack)
        pct_speed = int(self.SPEED_PENALTY_PER_STACK * 100 * self.stack)
        return f"Damage +{pct_dmg}%, Speed -{pct_speed}% (Cost: {self.POINT_COST})"

    def get_color(self) -> tuple: return (235, 90, 70)
