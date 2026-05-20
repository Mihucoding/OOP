"""
StatUpgrade — hệ thống nâng chỉ số cơ bản cho player.

Mỗi StatUpgrade có:
  - stat_type : loại chỉ số
  - value     : giá trị tăng (được chọn theo rarity)
  - rarity    : COMMON / UNCOMMON / RARE / EPIC / LEGENDARY
"""
import random

# ── Rarity ──────────────────────────────────────────────────────────────────
COMMON     = 'common'
UNCOMMON   = 'uncommon'
RARE       = 'rare'
EPIC       = 'epic'
LEGENDARY  = 'legendary'

RARITY_WEIGHTS = [50, 28, 15, 6, 1]   # common → legendary
RARITY_LIST    = [COMMON, UNCOMMON, RARE, EPIC, LEGENDARY]

RARITY_LABEL = {
    COMMON:    'Phổ thông',
    UNCOMMON:  'Không phổ biến',
    RARE:      'Quý hiếm',
    EPIC:      'Sử thi',
    LEGENDARY: 'Huyền thoại',
}

# ── Màu rarity (RGB) ─────────────────────────────────────────────────────────
RARITY_COLOR = {
    COMMON:    (170, 170, 170),
    UNCOMMON:  (80,  200, 120),
    RARE:      (80,  140, 255),
    EPIC:      (180, 80,  255),
    LEGENDARY: (255, 200, 50),
}

# ── Định nghĩa từng stat ─────────────────────────────────────────────────────
# stat_type → {rarity: value, ...}
STAT_DEFS = {
    'max_hp': {
        'display': 'Máu tối đa',
        'icon':    '❤',
        'fmt':     '+{v} HP',
        'values': {
            COMMON:    15,
            UNCOMMON:  25,
            RARE:      35,
            EPIC:      50,
            LEGENDARY: 80,
        },
    },
    'speed': {
        'display': 'Tốc độ di chuyển',
        'icon':    '👟',
        'fmt':     '+{v} tốc độ',
        'values': {
            COMMON:    10,
            UNCOMMON:  15,
            RARE:      22,
            EPIC:      30,
            LEGENDARY: 50,
        },
    },
    'damage': {
        'display': 'Sát thương đạn',
        'icon':    '⚔',
        'fmt':     '+{v} sát thương',
        'values': {
            COMMON:    3,
            UNCOMMON:  5,
            RARE:      8,
            EPIC:      12,
            LEGENDARY: 20,
        },
    },
    'armor': {
        'display': 'Giáp (giảm damage)',
        'icon':    '🛡',
        'fmt':     '+{v}% giáp',
        'values': {
            COMMON:    3,
            UNCOMMON:  5,
            RARE:      8,
            EPIC:      12,
            LEGENDARY: 20,
        },
    },
    'hp_regen': {
        'display': 'Hồi máu thụ động',
        'icon':    '💚',
        'fmt':     '+{v} HP/s',
        'values': {
            COMMON:    1,
            UNCOMMON:  2,
            RARE:      3,
            EPIC:      5,
            LEGENDARY: 8,
        },
    },
    'xp_range': {
        'display': 'Bán kính hút XP',
        'icon':    '✨',
        'fmt':     '+{v}px hút XP',
        'values': {
            COMMON:    30,
            UNCOMMON:  50,
            RARE:      70,
            EPIC:      100,
            LEGENDARY: 150,
        },
    },
    'lucky': {
        'display': 'May mắn',
        'icon':    '🍀',
        'fmt':     '+{v} may mắn',
        'values': {
            COMMON:    5,
            UNCOMMON:  8,
            RARE:      12,
            EPIC:      18,
            LEGENDARY: 28,
        },
    },
    'cdr': {
        'display': 'Giảm hồi chiêu',
        'icon':    '⏱',
        'fmt':     '-{v}% hồi chiêu',
        'values': {
            COMMON:    5,
            UNCOMMON:  8,
            RARE:      12,
            EPIC:      16,
            LEGENDARY: 22,
        },
    },
}

ALL_STAT_TYPES = list(STAT_DEFS.keys())


class StatUpgrade:
    """Một lựa chọn nâng chỉ số. Có thể apply trực tiếp lên player."""

    def __init__(self, stat_type: str, rarity: str):
        self.stat_type = stat_type
        self.rarity    = rarity
        defn           = STAT_DEFS[stat_type]
        self.value     = defn['values'][rarity]
        self._display  = defn['display']
        self._fmt      = defn['fmt']
        self._icon     = defn['icon']

    # ── Giao diện ──────────────────────────────────────────────────────────────

    def get_display_name(self) -> str:
        return self._display

    def get_value_text(self) -> str:
        return self._fmt.format(v=self.value)

    def get_rarity_label(self) -> str:
        return RARITY_LABEL[self.rarity]

    def get_color(self) -> tuple:
        return RARITY_COLOR[self.rarity]

    def get_icon(self) -> str:
        return self._icon

    # ── Áp dụng lên player ────────────────────────────────────────────────────

    def apply(self, player) -> None:
        """Cộng trực tiếp vào chỉ số player."""
        if self.stat_type == 'max_hp':
            player.max_hp += self.value
            player.hp     += self.value * 0.5   # hồi 50% lượng HP tăng thêm
        elif self.stat_type == 'speed':
            player.speed  += self.value
        elif self.stat_type == 'damage':
            player.damage += self.value
        elif self.stat_type == 'armor':
            player.armor  = min(75.0, player.armor + self.value)  # tối đa 75%
        elif self.stat_type == 'hp_regen':
            player.hp_regen += self.value
        elif self.stat_type == 'xp_range':
            player.xp_range += self.value
        elif self.stat_type == 'lucky':
            player.lucky = min(100.0, player.lucky + self.value)
        elif self.stat_type == 'cdr':
            # Giảm cooldown tất cả chiêu + ultimate
            factor = 1.0 - self.value / 100.0
            for spell in player.spells:
                spell.fire_rate  = max(0.08, spell.fire_rate * factor)
            player.ultimate_cooldown = max(2.0,
                                           player.ultimate_cooldown * factor)


def _pick_rarity(lucky: float = 0.0) -> str:
    """Chọn rarity với trọng số; lucky cao → dịch weight về Rare/Epic."""
    weights = list(RARITY_WEIGHTS)
    # Mỗi điểm lucky dịch 0.3% từ common sang rare+
    boost = min(lucky * 0.3, 30.0)
    weights[0] = max(5,  weights[0] - boost)         # common giảm
    weights[2] = weights[2] + boost * 0.5            # rare tăng
    weights[3] = weights[3] + boost * 0.3            # epic tăng
    weights[4] = weights[4] + boost * 0.2            # legendary tăng
    return random.choices(RARITY_LIST, weights=weights, k=1)[0]


def generate_stat_upgrade(lucky: float = 0.0) -> StatUpgrade:
    """Tạo 1 StatUpgrade ngẫu nhiên với rarity có trọng số theo lucky."""
    stat_type = random.choice(ALL_STAT_TYPES)
    rarity    = _pick_rarity(lucky)
    return StatUpgrade(stat_type, rarity)
