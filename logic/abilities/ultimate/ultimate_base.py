"""
UltimateAbility — base class cho tất cả ultimate.

activate() xử lý damage/effect trực tiếp,
trả về dict mô tả visual effect cho renderer.
"""
import math
from abc import ABC, abstractmethod


class UltimateAbility(ABC):
    COOLDOWN = 8.0    # giây, override trong subclass
    RADIUS   = 200.0  # bán kính AoE

    @property
    def name(self) -> str:
        return "Ultimate"

    @property
    def color(self) -> tuple:
        return (255, 255, 255)

    def activate(self, player, enemies: list, boss, context: dict) -> dict:
        """
        Kích hoạt ultimate. Trả về visual_info dict:
        {
          'cx': float, 'cy': float,   # tâm hiệu ứng
          'radius': float,
          'color': tuple,
          'duration': float,          # giây hiển thị flash
        }
        """
        targets = self._get_targets(player, enemies, boss)
        self._apply(player, targets, context)
        return {
            'cx':       player.x,
            'cy':       player.y,
            'radius':   self.RADIUS,
            'color':    self.color,
            'duration': 0.5,
            'name':     self.name,
        }

    @abstractmethod
    def _apply(self, player, targets: list, context: dict) -> None:
        """Áp dụng hiệu ứng lên danh sách targets."""

    def _get_targets(self, player, enemies: list, boss) -> list:
        """Lọc enemy trong bán kính."""
        targets = []
        for e in enemies:
            if not e.alive:
                continue
            if math.hypot(e.x - player.x, e.y - player.y) <= self.RADIUS:
                targets.append(e)
        if boss and boss.alive:
            if math.hypot(boss.x - player.x, boss.y - player.y) <= self.RADIUS:
                targets.append(boss)
        return targets


def get_ultimate_for_spell(spell) -> UltimateAbility:
    """Trả về ultimate phù hợp với element ở Slot 0 của spell."""
    from logic.rune.elements.fire_rune      import FireRune
    from logic.rune.elements.ice_rune       import IceRune
    from logic.rune.elements.lightning_rune import LightningRune
    from logic.rune.elements.wind_rune      import WindRune
    from logic.abilities.ultimate.ultimates import (
        FireNova, IceBlizzard, LightningStorm, WindCyclone, ShadowNova)

    slot0_rune = spell.rune_slots.get(0).rune
    if isinstance(slot0_rune, FireRune):      return FireNova()
    if isinstance(slot0_rune, IceRune):       return IceBlizzard()
    if isinstance(slot0_rune, LightningRune): return LightningStorm()
    if isinstance(slot0_rune, WindRune):      return WindCyclone()
    return ShadowNova()
