from logic.rune.rune_component import ModifierRune

class PiercingEyesModifier(ModifierRune):
    """
    Rune Mắt Xuyên Thấu — đạn xuyên qua thêm N địch trước khi biến mất
    (mỗi địch chỉ ăn damage 1 lần nhờ Bullet._hit_ids, kể cả khi đạn dính
    hitbox nhiều frame liền).
    Stack: mỗi bản cộng dồn thêm PIERCE_PER_STACK lượt xuyên.
    """
    PIERCE_PER_STACK = 1
    POINT_COST = 2   # xuyên thêm địch là hiệu ứng mạnh — tốn điểm như Split/Bounce
    ON_FIRE_PRIORITY = 10   # buff thuần → áp TRƯỚC spawner/trigger (xem ModifierRune)

    def on_fire(self, bullet, context: dict) -> list:
        bullet.pierce_remaining = (
            getattr(bullet, 'pierce_remaining', 0) + self.PIERCE_PER_STACK * self.stack
        )
        return []

    def on_update(self, bullet, dt: float, context: dict = None) -> None:
        pass

    def get_display_name(self) -> str: return "Piercing Eyes"

    def get_description(self) -> str:
        n = self.PIERCE_PER_STACK * self.stack
        target = "enemy" if n == 1 else "enemies"
        return f"Bullets pierce through {n} extra {target} (Cost: {self.POINT_COST})"

    def get_color(self) -> tuple: return (100, 220, 200)
