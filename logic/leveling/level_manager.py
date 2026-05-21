import random

<<<<<<< HEAD
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
=======
# Import tất cả Rune để tạo pool lựa chọn
from logic.rune.elements.fire_rune import FireRune
from logic.rune.elements.ice_rune import IceRune
from logic.rune.elements.poison_rune import PoisonRune
from logic.rune.modifiers.spiral_modifier import SpiralModifier
from logic.rune.modifiers.bounce_modifier import BounceModifier
from logic.rune.modifiers.split_modifier import SplitModifier

ALL_RUNES = [FireRune, IceRune, PoisonRune,
             SpiralModifier, BounceModifier, SplitModifier]
>>>>>>> 3e15ae77a0ed8863193acdf98696434a388c7c55


class LevelManager:
    """
<<<<<<< HEAD
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
=======
    Quản lý việc chọn Rune khi lên cấp.
    - Tạo pool 3 Rune ngẫu nhiên để player chọn
    - Áp dụng Rune được chọn vào RuneTree của player
    """
    CHOICES_COUNT = 3   # số lựa chọn mỗi lần lên cấp

    def __init__(self):
        self.pending_level_up = False
        self.current_choices: list = []   # list RuneComponent instances

    def trigger_level_up(self) -> None:
        # Set pending_level_up = True
        # Tạo current_choices: chọn CHOICES_COUNT Rune ngẫu nhiên từ ALL_RUNES
        # Instantiate chúng (gọi constructor)
        pass

    def apply_choice(self, index: int, player) -> None:
        """
        Áp dụng Rune người chơi chọn vào player.rune_tree.
        index: 0, 1, hoặc 2
        """
        # rune = current_choices[index]
        # Nếu là ElementRune:
        #   Nếu player.rune_tree.element là cùng loại → element_stack += 1
        #   Ngược lại → player.rune_tree.set_element(rune)
        # Nếu là ModifierRune:
        #   Kiểm tra đã có modifier cùng loại chưa, nếu có → stack += 1
        #   Ngược lại → player.rune_tree.add_modifier(rune)
        # Set pending_level_up = False
        pass
>>>>>>> 3e15ae77a0ed8863193acdf98696434a388c7c55
