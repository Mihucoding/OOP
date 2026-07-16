from logic.rune.rune_component import ElementRune
from logic.entities.status_effect import StatusEffect


class FireRune(ElementRune):
    """
    Rune Lửa — đốt cháy quái khi trúng đạn.
    Stack: chọn 2 lần → burn_damage nhân đôi.
    """

    BURN_DAMAGE = 8.0    # damage/giây
    BURN_DURATION = 3.0  # giây

    def on_hit(self, bullet, enemy, context: dict) -> None:
        """
        Viên ngọc Lửa bắt đầu phát huy tác dụng khi đạn chạm mục tiêu.
        Đầu tiên nó lấy chỉ số (stack) của ngọc này, tính toán sát thương diện rộng (splash damage) dựa theo chỉ số đó.
        Sau đó, nếu đây là đòn nổ lan, nó có cơ hội tạo ra hiệu ứng 'burn' (thiêu đốt) dính vào list `StatusEffect` của quái.
        Nhờ StatusEffect này, quái sẽ bị trừ máu liên tục ở hàm Enemy.update (Bước 9).

        👉 BƯỚC TIẾP THEO (Bước 19): Ở khía cạnh logic, mọi thứ đã xử lý xong! Quái đã nhận sát thương. Bây giờ, game sẽ vẽ tất cả lên màn hình. Hãy mở [ui/renderer.py](file:///c:/Users/acer/Downloads/OOP-mihu_branch/ui/renderer.py) và tìm hàm `draw_enemy`.
        """
        burn = StatusEffect(
            effect_type="burn",
            damage_per_sec=self.BURN_DAMAGE * bullet.element_stack,
            duration=self.BURN_DURATION,
        )
        enemy.add_status(burn)

    def get_display_name(self) -> str:
        return "Fire Rune"

    def get_description(self) -> str:
        return f"Burns for {self.BURN_DAMAGE} HP/s over {self.BURN_DURATION}s"

    def get_color(self) -> tuple:
        return (255, 100, 30)
