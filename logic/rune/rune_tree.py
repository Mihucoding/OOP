"""
RuneTree — Cây Rune kết hợp Elements + Modifiers cho 1 chiêu.

Chiêu luôn có Base Spell (đạn thường), nên RuneTree không cần Element để bắn.
Elements thêm hiệu ứng khi trúng; Modifiers thay đổi hành vi đạn.
"""
from logic.rune.rune_component import RuneComponent, ElementRune, ModifierRune


class RuneTree:
    """
    Container chứa toàn bộ Rune của 1 viên đạn.
    - elements : list[ElementRune] — nhiều nguyên tố cùng hoạt động
    - modifiers: list[ModifierRune] — quỹ đạo / split / bounce
    - MAX_DEPTH = 3
    """

    MAX_DEPTH = 3

    def __init__(self):
        self.elements:  list[ElementRune]  = []
        self.modifiers: list[ModifierRune] = []

    # ── Backward-compat property ───────────────────────────────────────────────

    @property
    def element(self) -> ElementRune | None:
        """Element đầu tiên trong cây, giữ lại để tương thích code cũ."""
        return self.elements[0] if self.elements else None

    # ── Thiết lập Elements ────────────────────────────────────────────────────

    def set_element(self, elem: ElementRune) -> None:
        """Thay thế toàn bộ danh sách Element bằng 1 Element."""
        self.elements = [elem]

    def add_element(self, elem: ElementRune) -> None:
        """Thêm Element phụ vào danh sách."""
        self.elements.append(elem)

    def remove_element(self, elem: ElementRune) -> None:
        if elem in self.elements:
            self.elements.remove(elem)

    # ── Thiết lập Modifiers ───────────────────────────────────────────────────

    def add_modifier(self, modifier: ModifierRune,
                     parent: ModifierRune = None,
                     depth: int = 1) -> bool:
        if depth > self.MAX_DEPTH:
            return False
        if parent is None:
            self.modifiers.append(modifier)
        else:
            parent.add_child(modifier)
        return True

    # ── Áp dụng cây ──────────────────────────────────────────────────────────

    def on_fire(self, bullet, context: dict) -> list:
        """Gọi khi đạn bắn. Trả về list đạn phụ (SplitModifier tạo thêm)."""
        new_bullets: list = []
        for mod in self.modifiers:
            self._traverse_fire(mod, bullet, context, new_bullets, depth=1)
        return new_bullets

    def on_update(self, bullet, dt: float) -> None:
        """Gọi mỗi frame để cập nhật quỹ đạo đạn."""
        for mod in self.modifiers:
            self._traverse_update(mod, bullet, dt, depth=1)

    def on_hit(self, bullet, enemy, context: dict) -> None:
        """
        Gọi khi đạn trúng quái.
        Áp dụng TẤT CẢ Elements (mỗi cái dùng element_stack của riêng nó),
        sau đó áp dụng Modifiers.
        """
        original_stack = bullet.element_stack
        for elem in self.elements:
            # Tạm đặt element_stack theo từng element (hỗ trợ stacking riêng)
            bullet.element_stack = getattr(elem, 'element_stack', 1)
            elem.on_hit(bullet, enemy, context)
        bullet.element_stack = original_stack  # phục hồi

        for mod in self.modifiers:
            self._traverse_hit(mod, bullet, enemy, context, depth=1)

    # ── Duyệt cây đệ quy ─────────────────────────────────────────────────────

    def _traverse_fire(self, node, bullet, context, result, depth):
        if depth > self.MAX_DEPTH:
            return
        new = node.on_fire(bullet, context)
        if new:
            result.extend(new)
        for child in node.get_children():
            self._traverse_fire(child, bullet, context, result, depth + 1)

    def _traverse_update(self, node, bullet, dt, depth):
        if depth > self.MAX_DEPTH:
            return
        node.on_update(bullet, dt)
        for child in node.get_children():
            self._traverse_update(child, bullet, dt, depth + 1)

    def _traverse_hit(self, node, bullet, enemy, context, depth):
        if depth > self.MAX_DEPTH:
            return
        node.on_hit(bullet, enemy, context)
        for child in node.get_children():
            self._traverse_hit(child, bullet, enemy, context, depth + 1)

    # ── Tiện ích ─────────────────────────────────────────────────────────────

    def get_all_runes(self) -> list:
        """Trả về toàn bộ Rune trong cây (dùng cho HUD / Builder)."""
        runes = list(self.elements)
        for mod in self.modifiers:
            self._collect(mod, runes)
        return runes

    def _collect(self, node: RuneComponent, out: list):
        out.append(node)
        for child in node.get_children():
            self._collect(child, out)

    def is_ready(self) -> bool:
        """Base Spell luôn bắn được, kể cả khi chưa gắn rune."""
        return True

    def describe(self) -> str:
        """Mô tả ngắn gọn (dùng cho debug và Builder hint)."""
        elem_str = " | ".join(
            f"[{e.get_display_name()}]" for e in self.elements)
        mod_str  = " ".join(
            f"->{m.get_display_name()}" for m in self.modifiers)
        parts = [p for p in (elem_str, mod_str) if p]
        return " ".join(parts) if parts else "Basic shot"
