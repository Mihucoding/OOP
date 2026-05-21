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
SLOT_DEFS = [
    (0,  None, 'element',   760,  150),  # Hệ chính — optional ElementRune
    (1,  0,    'modifier',  560,  310),  # L1
    (2,  0,    'modifier',  960,  310),  # R1
    (3,  1,    'modifier',  560,  500),  # L2
    (4,  2,    'modifier',  960,  500),  # R2
]


class RuneSlot:
    """Một slot trong cây Rune Builder."""

    def __init__(self, slot_id: int, parent_id, slot_type: str, x: int, y: int):
        self.id        = slot_id
        self.parent_id = parent_id
        self.slot_type = slot_type   # 'element' | 'modifier'
        self.x         = x
        self.y         = y
        self.rune      = None

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

    def __init__(self):
        self.slots: list[RuneSlot] = [
            RuneSlot(sid, pid, stype, x, y)
            for sid, pid, stype, x, y in SLOT_DEFS
        ]

    def get(self, slot_id: int) -> RuneSlot:
        return self.slots[slot_id]

    # ── Kiểm tra ──────────────────────────────────────────────────────────────

    def can_place(self, slot_id: int, rune) -> bool:
        slot = self.get(slot_id)
        if not slot.is_empty():
            return False
        # Parent check: Slot 3/4 cần Slot 1/2 có rune
        if slot.parent_id is not None and slot.parent_id != 0:
            if self.get(slot.parent_id).is_empty():
                return False
        # Type check thông thường
        if slot.can_accept(rune):
            return True
        # Modifier slot + cùng element với Slot 0 → cho phép stack
        if slot.slot_type == 'modifier' and isinstance(rune, ElementRune):
            slot0_rune = self.get(0).rune
            if slot0_rune is not None and type(rune) == type(slot0_rune):
                return True
        return False

    def is_active(self, slot_id: int) -> bool:
        """Slot active nếu có rune hợp lệ; Slot 1/2 không cần Slot 0."""
        slot = self.get(slot_id)
        if slot.is_empty():
            return False
        # Slot 0 (element) active nếu có rune
        if slot.slot_type == 'element':
            return True
        # Slot 1/2 (parent=0): active nếu có rune, Slot 0 không bắt buộc
        if slot.parent_id == 0:
            return True
        # Slot 3/4: cần parent (1/2) active
        parent = self.get(slot.parent_id)
        return self.is_active(slot.parent_id)

    # ── Thao tác ──────────────────────────────────────────────────────────────

    def place(self, slot_id: int, rune) -> bool:
        if not self.can_place(slot_id, rune):
            return False
        self.get(slot_id).rune = rune
        return True

    def remove(self, slot_id: int):
        slot      = self.get(slot_id)
        old_rune  = slot.rune
        slot.rune = None
        return old_rune

    def swap(self, slot_id: int, incoming_rune):
        slot = self.get(slot_id)
        # Kiểm tra type bằng cùng logic can_place (không cần slot trống)
        accepts = slot.can_accept(incoming_rune)
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

        # ── Slot 1-4: Modifier, giữ parent-child ─────────────────────────────
        placed: dict[int, any] = {}   # slot_id → rune đã thêm vào tree

        for s in self.slots:
            if s.slot_type != 'modifier':
                continue
            if not isinstance(s.rune, ModifierRune) or not self.is_active(s.id):
                continue

            depth = self._get_depth(s.id)
            parent_rune = placed.get(s.parent_id)

            if isinstance(parent_rune, ModifierRune):
                tree.add_modifier(s.rune, parent=parent_rune, depth=depth)
            else:
                tree.add_modifier(s.rune, parent=None, depth=depth)

            placed[s.id] = s.rune

        return tree

    def _get_depth(self, slot_id: int) -> int:
        depth = 0
        slot  = self.get(slot_id)
        while slot.parent_id is not None:
            depth += 1
            slot   = self.get(slot.parent_id)
        return depth
