from logic.rune.rune_component import ElementRune
from logic.entities.status_effect import StatusEffect


class LightningRune(ElementRune):
    """
    Rune Sét — stunlên quái khi trúng đạn, đứng yên hoàn toàn.
    Stack: chọn 2 lần → thời gian stun tăng gấp đôi + damage thêm nhân đôi.
    """
    STUN_DURATION = 0.8   # giây
    BONUS_DAMAGE  = 15.0  # damage thêm ngay lập tức

    def on_hit(self, bullet, enemy, context: dict) -> None:
        # Stun: slow_factor = 0.0 → quái đứng yên hoàn toàn
        stun = StatusEffect(
            effect_type='stun',
            damage_per_sec=0.0,
            duration=self.STUN_DURATION * bullet.element_stack,
            slow_factor=0.0,
        )
        enemy.add_status(stun)
        # Damage thêm ngay lập tức (sét đánh)
        enemy.take_damage(self.BONUS_DAMAGE * bullet.element_stack)

    def get_display_name(self) -> str:
        return "Rune Sét"

    def get_description(self) -> str:
        return f"Stun {self.STUN_DURATION}s + {self.BONUS_DAMAGE} damage ngay"

    def get_color(self) -> tuple:
        return (200, 180, 255)
