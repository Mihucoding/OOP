"""
RuneTree — Cây Rune kết hợp Element + Modifiers.

Ví dụ song song (parallel):
    tree.element = IceRune()
    tree.add_modifier(SpiralModifier())   # root level
    tree.add_modifier(BounceModifier())   # root level
    → đạn xoắn ốc + đóng băng + nảy

Ví dụ nối tiếp (serial):
    spiral = SpiralModifier()
    bounce = BounceModifier()
    tree.add_modifier(spiral)
    tree.add_modifier(bounce, parent=spiral)   # bounce là con của spiral
    → spiral áp dụng trước, bounce là "con" của spiral
"""
from logic.rune.rune_component import RuneComponent, ElementRune, ModifierRune


class RuneTree:
    """
    Container chứa toàn bộ Rune của 1 viên đạn.
    - element: đúng 1 ElementRune (bắt buộc để bắn)
    - modifiers: danh sách ModifierRune ở cấp gốc (song song nhau)
    - MAX_DEPTH = 3: cây tối đa 3 cấp sâu
    """

    MAX_DEPTH = 3

    def __init__(self, element: ElementRune = None):
        self.element: ElementRune | None = element
        self.modifiers: list[ModifierRune] = []

    def set_element(self, element: ElementRune) -> None:
        self.element = element

    def add_modifier(self, modifier: ModifierRune,
                     parent: ModifierRune = None,
                     depth: int = 1) -> bool:
        """
        Thêm modifier vào cây.
        - parent=None  → thêm vào gốc (song song)
        - parent=X     → thêm làm con của X (nối tiếp)
        Trả về False nếu vượt MAX_DEPTH.
        """
        if depth > self.MAX_DEPTH:
            return False
        if parent is None:
            self.modifiers.append(modifier)
        else:
            parent.add_child(modifier)
        return True

    # ── Áp dụng cây ──────────────────────────────────────────────

    def on_fire(self, bullet, context: dict) -> list:
        """Gọi khi đạn bắn. Trả về list đạn phụ (Split tạo thêm)."""
        new_bullets: list = []
        for mod in self.modifiers:
            self._traverse_fire(mod, bullet, context, new_bullets, depth=1)
        return new_bullets

    def on_update(self, bullet, dt: float) -> None:
        """Gọi mỗi frame để cập nhật quỹ đạo đạn."""
        for mod in self.modifiers:
            self._traverse_update(mod, bullet, dt, depth=1)

    def on_hit(self, bullet, enemy, context: dict) -> None:
        """Gọi khi đạn trúng quái — áp dụng hiệu ứng Element trước, rồi Modifier."""
        if self.element:
            self.element.on_hit(bullet, enemy, context)
        for mod in self.modifiers:
            self._traverse_hit(mod, bullet, enemy, context, depth=1)

    # ── Duyệt cây đệ quy ─────────────────────────────────────────

    def _traverse_fire(self, node: RuneComponent, bullet, context, result, depth):
        if depth > self.MAX_DEPTH:
            return
        new = node.on_fire(bullet, context)
        if new:
            result.extend(new)
        for child in node.get_children():
            self._traverse_fire(child, bullet, context, result, depth + 1)

    def _traverse_update(self, node: RuneComponent, bullet, dt, depth):
        if depth > self.MAX_DEPTH:
            return
        node.on_update(bullet, dt)
        for child in node.get_children():
            self._traverse_update(child, bullet, dt, depth + 1)

    def _traverse_hit(self, node: RuneComponent, bullet, enemy, context, depth):
        if depth > self.MAX_DEPTH:
            return
        node.on_hit(bullet, enemy, context)
        for child in node.get_children():
            self._traverse_hit(child, bullet, enemy, context, depth + 1)

    # ── Tiện ích ─────────────────────────────────────────────────

    def get_all_runes(self) -> list:
        """Trả về toàn bộ Rune trong cây (dùng cho UI hiển thị)."""
        runes = []
        if self.element:
            runes.append(self.element)
        for mod in self.modifiers:
            self._collect(mod, runes)
        return runes

    def _collect(self, node: RuneComponent, out: list):
        out.append(node)
        for child in node.get_children():
            self._collect(child, out)

    def is_ready(self) -> bool:
        """Cây hợp lệ khi có ít nhất 1 Element."""
        return self.element is not None

    def describe(self) -> str:
        """Mô tả ngắn gọn (dùng cho debug)."""
        parts = []
        if self.element:
            parts.append(f"[{self.element.get_display_name()}]")
        for mod in self.modifiers:
            parts.append(f"→{mod.get_display_name()}")
        return " ".join(parts) if parts else "Chưa có Rune"
