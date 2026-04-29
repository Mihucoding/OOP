import random

# Import tất cả Rune để tạo pool lựa chọn
from logic.rune.elements.fire_rune import FireRune
from logic.rune.elements.ice_rune import IceRune
from logic.rune.elements.poison_rune import PoisonRune
from logic.rune.modifiers.spiral_modifier import SpiralModifier
from logic.rune.modifiers.bounce_modifier import BounceModifier
from logic.rune.modifiers.split_modifier import SplitModifier

ALL_RUNES = [FireRune, IceRune, PoisonRune,
             SpiralModifier, BounceModifier, SplitModifier]


class LevelManager:
    """
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
