import random

from logic.rune.elements.fire_rune      import FireRune
from logic.rune.elements.ice_rune       import IceRune
from logic.rune.elements.lightning_rune import LightningRune
from logic.rune.elements.wind_rune      import WindRune
from logic.rune.modifiers.spiral_modifier import SpiralModifier
from logic.rune.modifiers.bounce_modifier import BounceModifier
from logic.rune.modifiers.split_modifier  import SplitModifier
from logic.rune.modifiers.haste_rune      import HasteRune
from logic.leveling.stat_upgrade          import generate_stat_upgrade

# Pool Rune: 4 Elements + 3 Modifiers + 1 Passive
ALL_RUNES = [
    FireRune, IceRune, LightningRune, WindRune,
    SpiralModifier, BounceModifier, SplitModifier,
    HasteRune,
]

CHOICES_COUNT = 3


class LevelManager:
    """
    Quản lý việc chọn phần thưởng khi lên cấp.
    Mỗi lần lên cấp: 3 card = mix ngẫu nhiên Rune + StatUpgrade.
    Tỉ lệ Rune/Stat thay đổi theo wave (wave cao → thêm Stat).
    """

    def __init__(self):
        self.pending_level_up  = False
        self.current_choices: list = []   # list gồm Rune instance hoặc StatUpgrade

    def trigger_level_up(self, wave: int = 0, player=None) -> None:
        self.pending_level_up = True
        self.current_choices  = self._generate_choices(wave, player)

    def _generate_choices(self, wave: int, player=None) -> list:
        """
        Sinh 3 lựa chọn với tỉ lệ Stat tăng dần theo wave.
        Wave 0-4:  1 Stat / 2 Rune
        Wave 5-9:  2 Stat / 1 Rune
        Wave 10+:  2 Stat / 1 Rune (ổn định)
        """
        stat_count = min(2, 1 + wave // 5)
        rune_count = CHOICES_COUNT - stat_count

        choices = []
        # Sinh Stat cards — lucky của player ảnh hưởng rarity
        lucky = getattr(player, 'lucky', 0.0) if player is not None else 0.0
        for _ in range(stat_count):
            choices.append(generate_stat_upgrade(lucky))
        # Sinh Rune cards
        rune_classes = random.choices(ALL_RUNES, k=rune_count)
        for cls in rune_classes:
            choices.append(cls())

        random.shuffle(choices)
        return choices

    def apply_choice(self, index: int, player) -> None:
        """
        Áp dụng lựa chọn:
          - StatUpgrade → gọi upgrade.apply(player)
          - Rune        → thêm vào player.rune_inventory
        """
        if index < 0 or index >= len(self.current_choices):
            return
        choice = self.current_choices[index]

        from logic.leveling.stat_upgrade import StatUpgrade
        if isinstance(choice, StatUpgrade):
            choice.apply(player)
        else:
            player.add_to_inventory(choice)

        self.pending_level_up = False

    def is_choice_stat(self, index: int) -> bool:
        """Trả về True nếu choice[index] là StatUpgrade."""
        from logic.leveling.stat_upgrade import StatUpgrade
        if 0 <= index < len(self.current_choices):
            return isinstance(self.current_choices[index], StatUpgrade)
        return False
