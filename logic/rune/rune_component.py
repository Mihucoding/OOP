"""
Composite Pattern — Lớp cơ sở cho hệ thống Rune.

Cấu trúc:
    RuneComponent (ABC)          ← interface chung
    ├── ElementRune(RuneComponent) ← leaf: chỉ xử lý on_hit
    └── ModifierRune(RuneComponent) ← composite: xử lý on_update/on_fire, có children
"""
from abc import ABC, abstractmethod


class RuneComponent(ABC):
    """
    Lớp trừu tượng gốc của Composite Pattern.
    Mọi Rune đều kế thừa từ class này.
    """

    @abstractmethod
    def on_hit(self, bullet, enemy, context: dict) -> None:
        """
        Gọi khi đạn trúng quái.
        context = {'enemies': list[Enemy], 'bullets': list[Bullet]}
        """
        pass

    @abstractmethod
    def on_update(self, bullet, dt: float) -> None:
        """Gọi mỗi frame — dùng để thay đổi vận tốc/quỹ đạo đạn."""
        pass

    @abstractmethod
    def on_fire(self, bullet, context: dict) -> list:
        """
        Gọi ngay khi đạn được bắn ra.
        Trả về list đạn mới nếu có (ví dụ SplitModifier tạo thêm 2 viên).
        """
        pass

    def get_children(self) -> list:
        """Trả về danh sách Rune con. Override trong ModifierRune."""
        return []

    def get_name(self) -> str:
        return self.__class__.__name__

    def get_display_name(self) -> str:
        """Tên hiển thị trên UI khi chọn Rune lúc lên cấp."""
        return self.__class__.__name__

    def get_description(self) -> str:
        """Mô tả ngắn hiển thị trên UI."""
        return ""

    def get_color(self) -> tuple:
        """Màu đại diện trên UI (R, G, B)."""
        return (200, 200, 200)


class ElementRune(RuneComponent):
    """
    Rune Nguyên Tố (leaf node).
    Định hình hiệu ứng khi đạn trúng quái.
    Không thay đổi quỹ đạo, không tạo thêm đạn, không có con.
    """

    def on_update(self, bullet, dt: float) -> None:
        pass  # Element không ảnh hưởng chuyển động

    def on_fire(self, bullet, context: dict) -> list:
        return []  # Element không tạo thêm đạn

    def get_children(self) -> list:
        return []  # Leaf node — không có con


class ModifierRune(RuneComponent):
    """
    Rune Quỹ Đạo (composite node).
    Định hình chuyển động vật lý của đạn.
    Có thể chứa các Rune con (children) để tạo hiệu ứng lồng nhau.
    """

    def __init__(self):
        self._children: list[RuneComponent] = []

    def on_hit(self, bullet, enemy, context: dict) -> None:
        pass  # Modifier không có hiệu ứng trúng quái (mặc định)

    def add_child(self, rune: RuneComponent) -> None:
        """Thêm Rune con vào Modifier này (cấu trúc nối tiếp)."""
        self._children.append(rune)

    def get_children(self) -> list:
        return self._children
