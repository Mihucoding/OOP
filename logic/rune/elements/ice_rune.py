from logic.rune.rune_component import ElementRune
from logic.entities.status_effect import StatusEffect


class IceRune(ElementRune):
    """
    Rune Băng — làm chậm quái khi trúng đạn.
    Stack: chọn 2 lần → slow_factor giảm thêm (0.6 → 0.36).
    """
    SLOW_FACTOR = 0.6       # quái còn 60% tốc độ
    SLOW_DURATION = 3.0

    def on_hit(self, bullet, enemy, context: dict) -> None:
        # 'chill' hỗ trợ stacks: mỗi lần trúng thêm 1 stack, tối đa 5 stacks = đóng băng
        chill = StatusEffect(
            effect_type='chill',
            damage_per_sec=0.0,
            duration=self.SLOW_DURATION,
            slow_factor=self.SLOW_FACTOR ** bullet.element_stack,
        )
        enemy.add_status(chill)

    def get_display_name(self) -> str: return "Rune Băng"
    def get_description(self) -> str:
        return f"Làm chậm quái {int((1-self.SLOW_FACTOR)*100)}% trong {self.SLOW_DURATION}s"
    def get_color(self) -> tuple: return (100, 200, 255)
