from logic.rune.rune_component import ElementRune


class LightningRune(ElementRune):
    BONUS_DAMAGE = 15.0
    # 2 chỉ số hiển thị trên thẻ — game_loop tự quy đổi ra hằng số thật (xem
    # LIGHTNING_BEAM_RANGE/LIGHTNING_OVERLOAD_FILL_RATE), không hardcode riêng.
    LENGTH       = 12      # tầm bắn tia = LENGTH * LENGTH_TO_PX
    LENGTH_TO_PX = 160.0 / 12    # giữ đúng tầm bắn hiện tại (160px) quy theo LENGTH=12
    DURATION     = 2.0     # giây channel liên tục trước khi tự Overflow (khoá tạm)
    # Hit-And-Run: beam tức thời phản xạ (bẻ góc) khi chạm chướng ngại vật
    # trên map, đi tiếp theo hướng phản xạ với range reset về full — xem
    # game_loop._reflect_segment_chain.
    # SelfCentered giờ là cast-graph modifier: gắn thẳng beam thì vô hại (beam
    # không có đạn để quay), nhưng gắn dưới 1 Trigger (VD Flash of Swords) thì
    # tia kiếm do trigger sinh ra vẫn quay được → cho phép.
    # TwistOfFate: KHÔNG xoay vận tốc/lớn dần ở đây (beam tức thời) — thay vào
    # đó là công tắc chuyển tia thẳng sang vòng cung tĩnh (_execute_lightning_spiral_ring).

    def on_hit(self, bullet, enemy, context: dict) -> None:
        # Không vẽ thêm tia chớp overlay nữa — quái đã tự phản ứng bằng frame
        # "hit" có sẵn trong sprite sheet riêng của nó.
        enemy.take_damage(self.BONUS_DAMAGE * bullet.element_stack)

    def get_display_name(self) -> str:
        return "Lightning Rune"

    def get_description(self) -> str:
        return f"Instant chain lightning + {self.BONUS_DAMAGE} bonus damage"

    def get_color(self) -> tuple:
        return (200, 180, 255)
