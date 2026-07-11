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
    def on_update(self, bullet, dt: float, context: dict = None) -> None:
        """Gọi mỗi frame — dùng để thay đổi vận tốc/quỹ đạo đạn."""
        pass

    @abstractmethod
    def on_fire(self, bullet, context: dict) -> list:
        """
        Gọi ngay khi đạn được bắn ra.
        Trả về list đạn mới nếu có (ví dụ Stars Aligned tạo thêm bản dàn hàng).
        """
        pass

    def get_children(self) -> list:
        """Trả về danh sách Rune con. Override trong ModifierRune."""
        return []

    def get_display_name(self) -> str:
        """Tên hiển thị trên UI khi chọn Rune lúc lên cấp."""
        return self.__class__.__name__

    def get_description(self) -> str:
        """Mô tả ngắn hiển thị trên UI."""
        return ""

    def get_color(self) -> tuple:
        """Màu đại diện trên UI (R, G, B)."""
        return (200, 200, 200)

    def get_rune_kind(self) -> str:
        """Phân loại rune trong taxonomy Composite: 'element' | 'modifier' |
        'trigger'. Dùng cho nhãn UI (thẻ Rune) và tra cứu logic."""
        return 'modifier'


class ElementRune(RuneComponent):
    """
    Rune Nguyên Tố (leaf node).
    Định hình hiệu ứng khi đạn trúng quái.
    Không thay đổi quỹ đạo, không tạo thêm đạn, không có con.
    """

    # Tên class các Modifier KHÔNG hợp với dạng đạn của element này.
    # Mỗi element con tự khai báo (Open/Closed — không sửa RuneSlots).
    FORBIDDEN_MODIFIERS: tuple = ()

    def accepts_modifier(self, modifier) -> bool:
        """Element có nhận Modifier này vào nhánh cây không?"""
        return type(modifier).__name__ not in self.FORBIDDEN_MODIFIERS

    def get_rune_kind(self) -> str:
        return 'element'

    def on_update(self, bullet, dt: float, context: dict = None) -> None:
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

    # Điểm tốn khi lắp vào 1 chiêu — mỗi chiêu có ngân sách RuneSlots.MAX_POINTS.
    # Mặc định 1; modifier mạnh hơn tự override giá trị cao hơn (không sửa RuneSlots).
    POINT_COST: int = 1

    # Thứ tự chạy on_fire giữa các rune CÙNG CẤP (anh em, gắn vào cùng 1 node).
    # Thấp = chạy TRƯỚC. Rune BUFF thuần (chỉ nhân/đổi thuộc tính viên đạn rồi
    # return [] — VD Heavy Hitter, Lightened Heart, Piercing Eyes) đặt giá trị
    # THẤP để luôn áp buff TRƯỚC khi rune SPAWNER/TRIGGER (Split, Furious
    # Outburst, Rolling Stone...) "chụp" trạng thái viên đạn. Nhờ vậy kết quả
    # KHÔNG phụ thuộc thứ tự slot của các rune anh em (L1/L2/R1/R2) — chỉ cấu
    # trúc CHA-CON (neo vào Trigger) mới mang ý nghĩa, đúng luật Mystralia.
    ON_FIRE_PRIORITY: int = 100

    # Taxonomy: Trigger = rune CHỦ ĐỘNG cast ra đòn/hiệu ứng phụ khi 1 điều
    # kiện xảy ra (thẻ có badge "Triggered on ..."), VD Furious Outburst,
    # Rolling Stone, Perfect Storm, Flash of Swords. Modifier thuần chỉ đổi
    # thuộc tính/quỹ đạo/nhân bản đạn (mặc định IS_TRIGGER=False).
    # LƯU Ý: 1 số Modifier (VD Destructive Path) tái dùng method trigger_once
    # cho tiện cơ chế, nhưng vẫn là MODIFIER — nên phải khai báo TƯỜNG MINH
    # ở đây thay vì suy ra từ việc có trigger_once hay không.
    IS_TRIGGER: bool = False
    TRIGGER_ON: str = ""   # 'spawn' | 'distance' | 'hit'... (chỉ Trigger đặt)

    def __init__(self):
        self._children: list[RuneComponent] = []
        # Số lần cùng loại Modifier này được chọn/lắp — hiệu ứng nhân theo
        # stack (VD stack=2 thì Heavy Hitter +100% dmg thay vì +50%). Mọi
        # subclass dùng chung field này nên đặt ở đây thay vì lặp lại
        # `self.stack = 1` trong __init__ của từng file Modifier.
        self.stack = 1

    def get_rune_kind(self) -> str:
        return 'trigger' if self.IS_TRIGGER else 'modifier'

    def get_trigger_label(self) -> str:
        """Nhãn badge cho Trigger (VD 'Triggered on spawn'); rỗng nếu là Modifier."""
        if not self.IS_TRIGGER:
            return ""
        return f"Triggered on {self.TRIGGER_ON}" if self.TRIGGER_ON else "Triggered"

    def on_hit(self, bullet, enemy, context: dict) -> None:
        pass  # Modifier không có hiệu ứng trúng quái (mặc định)

    def add_child(self, rune: RuneComponent) -> None:
        """Thêm Rune con vào Modifier này (cấu trúc nối tiếp)."""
        self._children.append(rune)

    def get_children(self) -> list:
        return self._children
