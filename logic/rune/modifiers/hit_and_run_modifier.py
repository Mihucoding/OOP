from logic.rune.rune_component import ModifierRune


class HitAndRunModifier(ModifierRune):
    """
    Rune "Hit-And-Run" (Common Modifier) — đạn/tia PHẢN XẠ VẬT LÝ khi chạm
    chướng ngại vật trên map (góc tới = góc phản xạ, như tia sáng dội gương),
    rồi bay tiếp theo hướng mới. Rìa map KHÔNG tính là tường — bay ra ngoài
    map thì cứ để ra. Mỗi lần phản xạ, range/duration RESET về full — như
    đứng tại điểm chạm tường bắn 1 phát mới. Stack: mỗi bản +1 lượt phản xạ
    tối đa (bounce_max = MAX_BOUNCE * stack).

    KHÔNG tự làm gì trong on_hit/on_update — chỉ là 1 "cờ hiệu" để game_loop
    (nơi có quyền truy cập world_map/collision_rects, logic/ không được import
    pygame) tự dò rune này trong cây rồi áp phản xạ:
      • Fire/Wind (đạn/boomerang bay thật, có vận tốc mỗi frame):
        game_loop._update_bullet_wall_bounce raycast đoạn di chuyển mỗi frame.
      • Ice/Lightning (đòn tức thời, vẽ 1 đường thẳng): game_loop bẻ đường
        thành chuỗi đoạn phản xạ qua _reflect_segment_chain trước khi build
        hitbox/hiệu ứng.
    """
    MAX_BOUNCE = 1
    POINT_COST = 1   # Common Modifier — rẻ

    def on_hit(self, bullet, enemy, context: dict) -> None:
        pass

    def on_update(self, bullet, dt: float, context: dict = None) -> None:
        pass

    def on_fire(self, bullet, context: dict) -> list:
        return []

    def get_display_name(self) -> str: return "Hit-And-Run"
    def get_description(self) -> str:
        # Khớp y chang thẻ gốc (nội dung + format bullet ◆).
        return f"◆ Bounce +{int(self.MAX_BOUNCE * self.stack)}"
    def get_color(self) -> tuple: return (255, 220, 50)
