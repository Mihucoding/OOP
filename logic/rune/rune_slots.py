"""
RuneSlots — hệ thống slot cố định cho 1 chiêu.

Layout cây:

              [0: Hệ chính]      ← optional ElementRune
              /              \
        [1: L1]              [2: R1]    ← chỉ ModifierRune
            |                    |
        [3: L2]              [4: R2]    ← chỉ ModifierRune

Slot 0 là hệ chính (optional): chỉ nhận ElementRune.
Slot 1/2 đặt được ngay, không cần Slot 0.
Slot 3 cần Slot 1; Slot 4 cần Slot 2.
Nhánh 1-4 chỉ nhận ModifierRune.
"""
from logic.rune.rune_component import ElementRune, ModifierRune
from logic.rune.rune_tree import RuneTree

# (id, parent_id, slot_type, abs_x, abs_y)
# Vị trí (x,y) chỉ là placeholder — builder tự đặt lại theo layout từng hệ.
#
# Mặc định: 4 modifier / 2 nhánh
#             [0]
#            /    \
#          [1]    [2]
#           |      |
#          [3]    [4]
SLOT_DEFS = [
    (0,  None, 'element',   760,  150),  # Hệ chính — ElementRune (khóa)
    (1,  0,    'modifier',  560,  310),  # L1
    (2,  0,    'modifier',  960,  310),  # R1
    (3,  1,    'modifier',  560,  500),  # L2 (con L1)
    (4,  2,    'modifier',  960,  500),  # R2 (con R1)
]

# Fire: 5 modifier / 3 nhánh (trái leaf · giữa 2 · phải 2)
#              [0]
#           /   |   \
#         [1]  [2]  [3]
#               |    |
#              [4]  [5]
# Vị trí (x,y) chỉ placeholder — builder đặt lại theo layout xéo từng hệ.
# Fire: core@0; 1@1→0; 2@2→0; 3@4→0; 4@9→3(điểm4); 5@7→2(điểm7)  → 5 modifier
SLOT_DEFS_FIRE = [
    (0, None, 'element',  760, 150),
    (1, 0,    'modifier', 600, 330),
    (2, 0,    'modifier', 920, 330),
    (3, 0,    'modifier', 760, 330),
    (4, 3,    'modifier', 760, 510),
    (5, 2,    'modifier', 920, 510),   # con của slot 2, tại điểm lưới 7
]
# Ice: core@0; 1@4→0; 2@9→1; 3@11→2; 4@7→1; 5@12→4
SLOT_DEFS_ICE = [
    (0, None, 'element',  760, 150),
    (1, 0,    'modifier', 760, 300),
    (2, 1,    'modifier', 760, 400),
    (3, 2,    'modifier', 600, 500),
    (4, 1,    'modifier', 900, 400),
    (5, 4,    'modifier', 900, 500),
]
# Wind: core@0; 1@4→0; 2@9→1; 3@6→1; 4@14→2; 5@12→2
SLOT_DEFS_WIND = [
    (0, None, 'element',  760, 150),
    (1, 0,    'modifier', 760, 300),
    (2, 1,    'modifier', 760, 400),
    (3, 1,    'modifier', 600, 400),
    (4, 2,    'modifier', 700, 520),
    (5, 2,    'modifier', 860, 520),
]
# Lightning: core@0; 1@1→0; 2@6→1; 3@2→0; 4@4→3; 5@7→3
SLOT_DEFS_LIGHTNING = [
    (0, None, 'element',  760, 150),
    (1, 0,    'modifier', 600, 340),
    (2, 1,    'modifier', 540, 480),
    (3, 0,    'modifier', 920, 340),
    (4, 3,    'modifier', 860, 480),
    (5, 3,    'modifier', 980, 480),
]


def slot_defs_for_rune(rune):
    """Chọn cấu trúc slot theo hệ — mỗi hệ có cây riêng (5 modifier / 3 tầng)."""
    from logic.rune.elements.fire_rune import FireRune
    from logic.rune.elements.ice_rune import IceRune
    from logic.rune.elements.wind_rune import WindRune
    from logic.rune.elements.lightning_rune import LightningRune
    if isinstance(rune, FireRune):
        return SLOT_DEFS_FIRE
    if isinstance(rune, IceRune):
        return SLOT_DEFS_ICE
    if isinstance(rune, WindRune):
        return SLOT_DEFS_WIND
    if isinstance(rune, LightningRune):
        return SLOT_DEFS_LIGHTNING
    return SLOT_DEFS


class RuneSlot:
    """Một slot trong cây Rune Builder."""

    def __init__(self, slot_id: int, parent_id, slot_type: str, x: int, y: int):
        self.id        = slot_id
        self.parent_id = parent_id
        self.slot_type = slot_type   # 'element' | 'modifier'
        self.x         = x
        self.y         = y
        self.rune      = None
        self.locked    = False       # lõi hệ chính: khóa cứng, không đổi trong builder

    def is_empty(self) -> bool: return self.rune is None

    def can_accept(self, rune) -> bool:
        if self.slot_type == 'element':
            return isinstance(rune, ElementRune)
        if self.slot_type == 'modifier':
            return isinstance(rune, ModifierRune)
        return False


class RuneSlots:
    """Quản lý Slot 0 (hệ chính) + 4 slot modifier của một chiêu."""

    NODE_RADIUS = 38
    MAX_POINTS  = 5   # ngân sách điểm cho modifier của 1 chiêu (mỗi ModifierRune.POINT_COST)

    def __init__(self, slot_defs=None):
        defs = slot_defs if slot_defs is not None else SLOT_DEFS
        self.slots: list[RuneSlot] = [
            RuneSlot(sid, pid, stype, x, y)
            for sid, pid, stype, x, y in defs
        ]

    def get(self, slot_id: int) -> RuneSlot:
        return self.slots[slot_id]

    # ── Kiểm tra ──────────────────────────────────────────────────────────────

    def set_core(self, rune) -> None:
        """Gán element vào lõi (slot 0) và khóa cứng — dùng khi chọn hệ đầu ván."""
        slot0 = self.get(0)
        slot0.rune   = rune
        slot0.locked = True

    def can_place(self, slot_id: int, rune) -> bool:
        slot = self.get(slot_id)
        if slot.locked:
            return False
        if not slot.is_empty():
            return False
        # KHÔNG cần node cha có rune: node rời sẽ TỰ NỐI lên tổ tiên gần nhất
        # có rune (cuối cùng là root/element) khi build cây.
        # Type check thông thường
        if slot.can_accept(rune):
            # Modifier vào nhánh: element ở Slot 0 có quyền từ chối (VD Bounce với
            # beam/spike/boomerang — tránh crash & vô nghĩa).
            if slot.slot_type == 'modifier' and isinstance(rune, ModifierRune):
                slot0_rune = self.get(0).rune
                if slot0_rune is not None and not slot0_rune.accepts_modifier(rune):
                    return False
                # Ngân sách điểm: đủ 5 (MAX_POINTS) thì không lắp thêm được nữa
                cost = getattr(rune, 'POINT_COST', 1)
                if self.used_points() + cost > self.MAX_POINTS:
                    return False
            return True
        # Modifier slot + cùng element với Slot 0 → cho phép stack
        if slot.slot_type == 'modifier' and isinstance(rune, ElementRune):
            slot0_rune = self.get(0).rune
            if slot0_rune is not None and type(rune) == type(slot0_rune):
                return True
        return False

    def is_active(self, slot_id: int) -> bool:
        """Mọi slot có rune đều active — node rời tự nối lên tổ tiên gần nhất
        có rune nên không còn trạng thái 'khoá vì cha trống'."""
        return not self.get(slot_id).is_empty()

    def effective_parent(self, slot_id: int):
        """id tổ tiên gần nhất CÓ rune (bỏ qua node rỗng), tính cả Slot 0.
        None nếu tới gốc mà không gặp node nào có rune."""
        anc = self.get(slot_id).parent_id
        while anc is not None:
            if not self.get(anc).is_empty():
                return anc
            anc = self.get(anc).parent_id
        return None

    def used_points(self, exclude_slot_id: int | None = None) -> int:
        """Tổng điểm các ModifierRune đang lắp (mỗi chiêu tối đa MAX_POINTS)."""
        total = 0
        for s in self.slots:
            if s.slot_type != 'modifier' or s.rune is None:
                continue
            if exclude_slot_id is not None and s.id == exclude_slot_id:
                continue
            if isinstance(s.rune, ModifierRune):
                total += getattr(s.rune, 'POINT_COST', 1)
        return total

    # ── Thao tác ──────────────────────────────────────────────────────────────

    def place(self, slot_id: int, rune) -> bool:
        if not self.can_place(slot_id, rune):
            return False
        self.get(slot_id).rune = rune
        return True

    def remove(self, slot_id: int):
        slot = self.get(slot_id)
        if slot.locked:
            return None
        old_rune  = slot.rune
        slot.rune = None
        return old_rune

    def swap(self, slot_id: int, incoming_rune):
        slot = self.get(slot_id)
        if slot.locked:
            return None
        # Kiểm tra type bằng cùng logic can_place (không cần slot trống)
        accepts = slot.can_accept(incoming_rune)
        # Modifier vào nhánh: element ở Slot 0 có quyền từ chối (VD Bounce)
        if accepts and slot.slot_type == 'modifier' and isinstance(incoming_rune, ModifierRune):
            slot0_rune = self.get(0).rune
            if slot0_rune is not None and not slot0_rune.accepts_modifier(incoming_rune):
                accepts = False
            else:
                # Ngân sách điểm: trừ điểm của rune SẮP BỊ THAY (loại khỏi tổng) trước khi so
                cost = getattr(incoming_rune, 'POINT_COST', 1)
                if self.used_points(exclude_slot_id=slot_id) + cost > self.MAX_POINTS:
                    accepts = False
        if not accepts and slot.slot_type == 'modifier' and isinstance(incoming_rune, ElementRune):
            slot0_rune = self.get(0).rune
            accepts = slot0_rune is not None and type(incoming_rune) == type(slot0_rune)
        if not accepts:
            return None
        old       = slot.rune
        slot.rune = incoming_rune
        return old

    # ── Build RuneTree ─────────────────────────────────────────────────────────

    def build_rune_tree(self) -> RuneTree:
        """
        Tạo RuneTree từ các slot hiện tại.
        Slot 0 (element): thêm ElementRune nếu có.
        Slot 1-4 (modifier): giữ quan hệ cha-con khi parent cũng là Modifier.
        """
        # Reset _children của tất cả modifier để tránh duplicate khi rebuild
        for s in self.slots:
            if s.rune is not None and isinstance(s.rune, ModifierRune):
                s.rune._children = []

        tree = RuneTree()

        # ── Slot 0: Element hệ chính (optional) ──────────────────────────────
        slot0 = self.get(0)
        if slot0.rune is not None:
            # Đếm rune cùng hệ trong modifier slot để cộng vào element_stack
            same_elem_boost = sum(
                1 for s in self.slots
                if s.slot_type == 'modifier'
                and self.is_active(s.id)
                and isinstance(s.rune, ElementRune)
                and type(s.rune) == type(slot0.rune)
            )
            slot0.rune.element_stack = 1 + same_elem_boost
            tree.add_element(slot0.rune)

        # ── Slot 1-4: Modifier, tự nối lên tổ tiên gần nhất có rune ───────────
        placed: dict[int, any] = {}         # slot_id → modifier rune đã thêm
        placed_depth: dict[int, int] = {}   # slot_id → depth trong cây

        for s in self.slots:
            if s.slot_type != 'modifier':
                continue
            if not isinstance(s.rune, ModifierRune) or not self.is_active(s.id):
                continue

            # Nối vào modifier tổ tiên gần nhất; nếu tổ tiên là element (Slot 0)
            # hoặc không có → thành modifier gốc (nối thẳng tới đạn).
            ep = self.effective_parent(s.id)
            if ep is not None and ep in placed:
                parent_rune = placed[ep]
                depth       = placed_depth[ep] + 1
                tree.add_modifier(s.rune, parent=parent_rune, depth=depth)
            else:
                depth = 1
                tree.add_modifier(s.rune, parent=None, depth=depth)

            placed[s.id]       = s.rune
            placed_depth[s.id] = depth

        return tree
