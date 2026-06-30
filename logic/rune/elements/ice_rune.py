import math

from logic.rune.rune_component import ElementRune
from logic.entities.status_effect import StatusEffect


class IceRune(ElementRune):
    """Ice element. Basic bullets chill; active slot casts a hold-charge spike."""

    SLOW_FACTOR = 0.6
    SLOW_DURATION = 3.0

    CHARGE_MAX_TIME = 1.25
    MIN_LENGTH = 130.0
    MAX_LENGTH = 360.0
    HITBOX_WIDTH = 78.0
    START_OFFSET = 44.0
    MIN_DAMAGE_MULT = 0.9
    MAX_DAMAGE_MULT = 2.35

    def on_hit(self, bullet, enemy, context: dict) -> None:
        chill = StatusEffect(
            effect_type="chill",
            damage_per_sec=0.0,
            duration=self.SLOW_DURATION,
            slow_factor=self.SLOW_FACTOR ** bullet.element_stack,
        )
        enemy.add_status(chill)

    def charge_ratio(self, held_time: float) -> float:
        return max(0.0, min(1.0, held_time / self.CHARGE_MAX_TIME))

    def build_charge_attack(
        self,
        caster_x: float,
        caster_y: float,
        target_x: float,
        target_y: float,
        held_time: float,
        max_length: float | None = None,
    ) -> dict:
        charge_ratio = self.charge_ratio(held_time)
        dx = target_x - caster_x
        dy = target_y - caster_y
        dist = math.hypot(dx, dy)
        if dist <= 0:
            dx, dy = 1.0, 0.0
        else:
            dx, dy = dx / dist, dy / dist

        length = self.MIN_LENGTH + (self.MAX_LENGTH - self.MIN_LENGTH) * charge_ratio
        if max_length is not None:
            length = min(length, max(32.0, max_length))
        length_ratio = max(
            0.0,
            min(1.0, (length - self.MIN_LENGTH) / max(1.0, self.MAX_LENGTH - self.MIN_LENGTH)),
        )
        width = self.HITBOX_WIDTH
        start_x = caster_x + dx * self.START_OFFSET
        start_y = caster_y + dy * self.START_OFFSET
        end_x = start_x + dx * length
        end_y = start_y + dy * length
        perp_x, perp_y = -dy, dx
        half_w = width / 2

        return {
            "ratio": length_ratio,
            "charge_ratio": charge_ratio,
            "length": length,
            "width": width,
            "dir_x": dx,
            "dir_y": dy,
            "start_x": start_x,
            "start_y": start_y,
            "end_x": end_x,
            "end_y": end_y,
            "corners": [
                (start_x + perp_x * half_w, start_y + perp_y * half_w),
                (end_x + perp_x * half_w, end_y + perp_y * half_w),
                (end_x - perp_x * half_w, end_y - perp_y * half_w),
                (start_x - perp_x * half_w, start_y - perp_y * half_w),
            ],
            "damage_mult": self.MIN_DAMAGE_MULT
            + (self.MAX_DAMAGE_MULT - self.MIN_DAMAGE_MULT) * length_ratio,
        }

    def apply_charge_hit(self, enemy, damage: float, charge_ratio: float, stack: int = 1) -> None:
        enemy.take_damage(damage)
        chill = StatusEffect(
            effect_type="chill",
            damage_per_sec=0.0,
            duration=self.SLOW_DURATION * (1.0 + 0.35 * charge_ratio),
            slow_factor=self.SLOW_FACTOR ** stack,
        )
        enemy.add_status(chill)

    def get_display_name(self) -> str:
        return "Ice Rune"

    def get_description(self) -> str:
        return "Hold to grow an ice spike hitbox. Longer charge increases range and damage."

    def get_color(self) -> tuple:
        return (100, 200, 255)
