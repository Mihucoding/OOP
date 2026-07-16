import random

from logic.rune.modifiers.hit_and_run_modifier import HitAndRunModifier
from logic.rune.modifiers.twist_of_fate_modifier import TwistOfFateModifier
from logic.rune.modifiers.haste_rune      import HasteRune
from logic.rune.modifiers.lightened_heart_modifier import LightenedHeartModifier
from logic.rune.modifiers.piercing_eyes_modifier    import PiercingEyesModifier
from logic.rune.modifiers.furious_outburst_modifier import FuriousOutburstModifier
from logic.rune.modifiers.heavy_hitter_modifier     import HeavyHitterModifier
from logic.rune.modifiers.rolling_stone_modifier    import RollingStoneModifier
from logic.rune.modifiers.self_centered_modifier    import SelfCenteredModifier
from logic.rune.modifiers.destructive_path_modifier import DestructivePathModifier
from logic.rune.modifiers.frenetic_energy_modifier  import FreneticEnergyModifier
from logic.rune.modifiers.perfect_storm_modifier    import PerfectStormModifier
from logic.rune.modifiers.stars_aligned_modifier    import StarsAlignedModifier
from logic.rune.modifiers.flash_of_swords_trigger    import FlashOfSwordsTrigger
from logic.leveling.stat_upgrade          import generate_stat_upgrade

# Pool lên cấp: CHỈ Modifier — Element hệ chính đã chọn 1 lần lúc đầu ván
# (Skill Select) và khóa cứng, không xuất hiện lại ở đây nữa.
ALL_RUNES = [
    HitAndRunModifier, TwistOfFateModifier, HasteRune,
    LightenedHeartModifier, PiercingEyesModifier, FuriousOutburstModifier,
    HeavyHitterModifier, RollingStoneModifier, SelfCenteredModifier,
    DestructivePathModifier,
    FreneticEnergyModifier, PerfectStormModifier, StarsAlignedModifier,
    FlashOfSwordsTrigger,
]

# Số bản tối đa của 1 loại Modifier mà player có thể sở hữu (kho + đã lắp).
# Đủ 2 bản 1 loại thì loại đó ngừng xuất hiện trong lựa chọn lên cấp.
MAX_COPIES_PER_RUNE = 2

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

    def _count_owned(self, player, rune_cls) -> int:
        """Số bản `rune_cls` player đang có (kho chưa lắp + đã lắp ở mọi chiêu)."""
        if player is None:
            return 0
        count = sum(1 for r in player.rune_inventory if isinstance(r, rune_cls))
        for spell in player.spells:
            for slot in spell.rune_slots.slots:
                if slot.slot_type == 'modifier' and isinstance(slot.rune, rune_cls):
                    count += 1
        return count

    def _generate_choices(self, wave: int, player=None) -> list:
        """
        Sinh 3 lựa chọn với tỉ lệ Stat tăng dần theo wave.
        Wave 0-4:  1 Stat / 2 Rune
        Wave 5-9:  2 Stat / 1 Rune
        Wave 10+:  2 Stat / 1 Rune (ổn định)
        Rune: chỉ Modifier, loại nào đã đủ MAX_COPIES_PER_RUNE bản thì không
        sinh ra nữa (thay bằng StatUpgrade để vẫn đủ CHOICES_COUNT lựa chọn).
        """
        stat_count = min(2, 1 + wave // 5)
        rune_count = CHOICES_COUNT - stat_count

        lucky = getattr(player, 'lucky', 0.0) if player is not None else 0.0

        available = [cls for cls in ALL_RUNES
                     if self._count_owned(player, cls) < MAX_COPIES_PER_RUNE]
        if not available:
            # Player đã max mọi loại modifier — dồn hết thành thẻ Stat
            stat_count, rune_count = CHOICES_COUNT, 0

        choices = []
        for _ in range(stat_count):
            choices.append(generate_stat_upgrade(lucky))
        for cls in random.choices(available, k=rune_count):
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
