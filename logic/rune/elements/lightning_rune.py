from logic.rune.rune_component import ElementRune


class LightningRune(ElementRune):
    BONUS_DAMAGE = 15.0
    # Beam tức thời — không có viên đạn bay nên không thể nảy.
    # Bounce: beam tức thời không phải đạn bay nên không thể nảy.
    # SelfCentered giờ là cast-graph modifier: gắn thẳng beam thì vô hại (beam
    # không có đạn để quay), nhưng gắn dưới 1 Trigger (VD Flash of Swords) thì
    # tia kiếm do trigger sinh ra vẫn quay được → cho phép.
    # TwistOfFate: KHÔNG xoay vận tốc/lớn dần ở đây (beam tức thời) — thay vào
    # đó là công tắc chuyển tia thẳng sang vòng cung tĩnh (_execute_lightning_spiral_ring).
    FORBIDDEN_MODIFIERS = ("BounceModifier",)

    def on_hit(self, bullet, enemy, context: dict) -> None:
        context.get('effects', []).append({
            'kind': 'lightning_hit',
            'x': enemy.x,
            'y': enemy.y,
            'duration': 0.24,
        })
        enemy.take_damage(self.BONUS_DAMAGE * bullet.element_stack)

    def get_display_name(self) -> str:
        return "Lightning Rune"

    def get_description(self) -> str:
        return f"Instant chain lightning + {self.BONUS_DAMAGE} bonus damage"

    def get_color(self) -> tuple:
        return (200, 180, 255)
