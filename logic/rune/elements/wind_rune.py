from logic.rune.rune_component import ElementRune
from logic.entities.status_effect import StatusEffect


class WindRune(ElementRune):
    """
    Rune Gió — gây slow khi trúng đạn.
    Stack: chọn 2 lần → slow lâu hơn.
    """
    # Bounce: boomerang đã xuyên + tự quay về → "nảy sang địch gần nhất" vô nghĩa.
    # SelfCentered giờ THAM GIA cast graph nên KHÔNG còn ép boomerang quay:
    #   boomerang (CAN_ORBIT=False) chỉ nhận +count/+duration; còn khi Self-
    #   Centered làm con của 1 Trigger (VD Flash of Swords) thì chỉ tia kiếm
    #   quay quanh boomerang — hợp lệ. Vì vậy bỏ cấm SelfCentered ở đây.
    FORBIDDEN_MODIFIERS = ("BounceModifier",)

    SLOW_FACTOR   = 0.5     # quái còn 50% tốc độ
    SLOW_DURATION = 2.0     # giây

    def on_hit(self, bullet, enemy, context: dict) -> None:
        slow = StatusEffect(
            effect_type='slow',
            damage_per_sec=0.0,
            duration=self.SLOW_DURATION * bullet.element_stack,
            slow_factor=self.SLOW_FACTOR,
        )
        enemy.add_status(slow)

    def get_display_name(self) -> str:
        return "Wind Rune"

    def get_description(self) -> str:
        return f"{int((1-self.SLOW_FACTOR)*100)}% slow {self.SLOW_DURATION}s (pierce + boomerang)"

    def get_color(self) -> tuple:
        return (180, 230, 255)
