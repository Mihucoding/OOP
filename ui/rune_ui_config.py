"""
rune_ui_config — Cấu hình tập trung cho Rune Builder & Skill Select.

MUỐN CHỈNH GIAO DIỆN? Sửa các hằng số ở đây, KHÔNG cần đụng code vẽ:
  • Board to/nhỏ, đặt ở đâu   → BOARD_CENTER, BOARD_RADIUS
  • Node gần/xa, nối ngắn/dài → NODE_REACH_SCALE
  • Đường nối dày/mảnh        → LINK_WIDTH_ACTIVE / LINK_WIDTH_INACTIVE
  • Số chiêu                  → SPELL_COUNT
  • Thêm hệ mới               → thêm 1 entry vào ELEMENT_THEMES + ELEMENT_ORDER

Module này thuộc tầng UI (được phép import pygame). logic/ KHÔNG import file này.
"""
import math
import os
import pygame

# ── Board (bàn cờ lục giác) ────────────────────────────────────────────────────
BOARD_CENTER = (760, 452)     # tâm board — dời xuống chừa chỗ cho thanh kho phía trên
BOARD_RADIUS = 262            # bán kính board — số lớn = board BỰ hơn

# ── Node & đường nối ────────────────────────────────────────────────────────────
NODE_REACH_SCALE    = 0.72    # < 1.0: kéo node lại gần tâm → đường nối NGẮN hơn
LINK_WIDTH_ACTIVE   = 9       # độ DÀY đường nối khi active
LINK_WIDTH_INACTIVE = 4
ARROW_SIZE          = 13      # cỡ mũi tên

# ── Số chiêu chọn lúc đầu ván ───────────────────────────────────────────────────
SPELL_COUNT = 2

# ── 17 giao điểm lưới lục giác (dx, dy theo bán kính board) ─────────────────────
# Đánh số y hệt hình vẽ tay: 0 đỉnh trên · 16 đỉnh dưới · cạnh trái 3-8-13 · phải 5-10-15
# Đặt node theo SỐ ĐIỂM — chỉ cần khai báo point number cho từng slot của mỗi hệ.
GRID_POINTS = {
    0:  (0.000, -1.000),
    1:  (-0.433, -0.750), 2:  (0.433, -0.750),
    3:  (-0.866, -0.500), 4:  (0.000, -0.500), 5:  (0.866, -0.500),
    6:  (-0.433, -0.250), 7:  (0.433, -0.250),
    8:  (-0.866,  0.000), 9:  (0.000,  0.000), 10: (0.866,  0.000),
    11: (-0.433,  0.250), 12: (0.433,  0.250),
    13: (-0.866,  0.500), 14: (0.000,  0.500), 15: (0.866,  0.500),
    16: (0.000,  1.000),
}

# ── Keyword sub-card (giải nghĩa từ khoá xuất hiện trong mô tả rune) ────────────
# Thẻ phụ hiện dưới panel rune, giải thích các "từ khoá" game (như thẻ gốc).
# Thêm keyword mới = thêm 1 entry (khoá phải khớp chữ trong get_description).
KEYWORD_INFO = {
    "Critical": "Deals critical damage (Base multiplier: x2).",
    "Vortex": "Pulls targets toward the Spell's or Trigger's center.",
}


def keywords_in_text(text: str) -> list:
    """Trả list (tên keyword, định nghĩa) cho các keyword có mặt trong text
    (không phân biệt hoa/thường), giữ thứ tự khai báo trong KEYWORD_INFO."""
    low = text.lower()
    return [(name, info) for name, info in KEYWORD_INFO.items()
            if name.lower() in low]


# ── Element registry (thêm hệ mới = thêm 1 entry ở đây) ─────────────────────────
ELEMENT_ORDER = ["fire", "ice", "lightning", "wind"]

ELEMENT_THEMES = {
    "fire": {
        "color": (255, 104, 28), "accent": (205, 40, 24), "muted": (128, 63, 32),
        "glyph": "F", "name": "FUR IGINI",
        "desc": "A short-ranged punch of fire.",
    },
    "ice": {
        "color": (90, 200, 255), "accent": (80, 120, 255), "muted": (44, 103, 145),
        "glyph": "I", "name": "GLACIA SPIRE",
        "desc": "A charged shard that grows into a piercing ice spike.",
    },
    "lightning": {
        "color": (58, 255, 218), "accent": (128, 90, 255), "muted": (35, 126, 118),
        "glyph": "Z", "name": "EXAE AURA",
        "desc": "A dangerous beam of lightning.",
    },
    "wind": {
        "color": (80, 245, 55), "accent": (34, 180, 36), "muted": (34, 110, 62),
        "glyph": "W", "name": "CELE AER",
        "desc": "A boomerang gust that returns when called back.",
    },
    "basic": {
        "color": (190, 220, 230), "accent": (70, 120, 132), "muted": (55, 92, 102),
        "glyph": "*", "name": "BASIC SHOT",
        "desc": "A reliable projectile shaped by the runes socketed into this spell.",
    },
}


def theme(key: str) -> dict:
    """Trả theme của element key (fallback về 'basic')."""
    return ELEMENT_THEMES.get(key, ELEMENT_THEMES["basic"])


def make_element_rune(key: str):
    """Tạo instance ElementRune tương ứng key. Dùng ở tầng UI để nạp vào lõi chiêu."""
    from logic.rune.elements.fire_rune import FireRune
    from logic.rune.elements.ice_rune import IceRune
    from logic.rune.elements.lightning_rune import LightningRune
    from logic.rune.elements.wind_rune import WindRune
    return {
        "fire": FireRune, "ice": IceRune,
        "lightning": LightningRune, "wind": WindRune,
    }[key]()


def rune_element_key(rune) -> str | None:
    """Map một ElementRune → key; Modifier/None trả None."""
    if rune is None:
        return None
    from logic.rune.elements.fire_rune import FireRune
    from logic.rune.elements.ice_rune import IceRune
    from logic.rune.elements.lightning_rune import LightningRune
    from logic.rune.elements.wind_rune import WindRune
    if isinstance(rune, WindRune):
        return "wind"
    if isinstance(rune, LightningRune):
        return "lightning"
    if isinstance(rune, FireRune):
        return "fire"
    if isinstance(rune, IceRune):
        return "ice"
    return None


# ── Icon sprite (dùng chung builder + skill select) ─────────────────────────────
_ICON_CACHE: dict = {}
_ICON_LOADED = False


def _hex_points(cx: int, cy: int, radius: int) -> list:
    return [
        (int(cx + math.cos(math.radians(60 * i - 30)) * radius),
         int(cy + math.sin(math.radians(60 * i - 30)) * radius))
        for i in range(6)
    ]


def _hex_mask_icon(img: pygame.Surface) -> pygame.Surface:
    """Crop ảnh về vuông rồi mask theo lục giác → trong suốt ngoài crest (cắt nền JPG)."""
    w, h = img.get_size()
    s = min(w, h)
    square = pygame.Surface((s, s), pygame.SRCALPHA)
    square.blit(img, (0, 0), pygame.Rect((w - s) // 2, (h - s) // 2, s, s))
    mask = pygame.Surface((s, s), pygame.SRCALPHA)
    pygame.draw.polygon(mask, (255, 255, 255, 255), _hex_points(s // 2, s // 2, int(s * 0.49)))
    square.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return square


def _load_icons() -> None:
    global _ICON_LOADED
    _ICON_LOADED = True
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    folders = [
        os.path.join(root, "assets", "element"),
        os.path.join(root, "assets", "sprites", "runes"),
    ]
    for key in ("fire", "ice", "lightning", "wind", "basic"):
        surf = None
        for folder in folders:
            for ext in (".png", ".jpg", ".jpeg"):
                path = os.path.join(folder, key + ext)
                if os.path.exists(path):
                    try:
                        surf = pygame.image.load(path).convert_alpha()
                    except pygame.error:
                        surf = None
                    break
            if surf is not None:
                break
        if surf is not None:
            _ICON_CACHE[key] = _hex_mask_icon(surf)


def element_icon(key):
    """Sprite icon (đã mask lục giác) cho element key, hoặc None để fallback glyph."""
    if key is None:
        return None
    if not _ICON_LOADED:
        _load_icons()
    return _ICON_CACHE.get(key)
