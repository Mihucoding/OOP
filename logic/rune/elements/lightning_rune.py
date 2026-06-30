from logic.rune.rune_component import ElementRune


class LightningRune(ElementRune):
    BONUS_DAMAGE = 15.0

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
