import math
import random

from logic.rune.rune_component import ModifierRune

class RollingStoneModifier(ModifierRune):
    """
    Rune Trigger "Triggered on spawn" — nổ đúng 1 lần mỗi lần cast (không lặp
    lại theo quãng đường như FuriousOutburstModifier), tung ra 1 tảng đá lăn.

    Đá dừng lăn (rơi xuống) khi TRÚNG QUÁI ĐẦU TIÊN (pierce_remaining=0 →
    Bullet.on_hit tự set alive=False, xem bullet.py) HOẶC khi đã lăn đủ
    MAX_ROLL_DISTANCE mà chưa trúng ai — không xuyên qua nhiều địch như tên
    "lăn" nghe có vẻ vậy. game_loop._fall_rolling_stones() phát hiện bullet
    vừa chết (do trúng quái hoặc do đi đủ khoảng cách) rồi biến vị trí đó
    thành 1 tảng đá TĨNH vĩnh viễn (decoration + collision_rect, tái dùng
    world_map.rock_sprites) — chặn player/quái/boss y hệt đá mọc sẵn trên map.

    - Fire/Wind (có Bullet/WindBoomerang thật): gọi lúc bắn (on_fire).
    - Lightning/Ice (đòn tức thời): game_loop tự dò rune này qua
      `_find_triggerable_modifiers()` rồi gọi thẳng `trigger_once()`.
    """
    IS_TRIGGER     = True
    TRIGGER_ON     = "spawn"
    OWNS_SUBTREE   = True    # nhánh con áp lên tảng đá, không lên đạn cha
    DAMAGE_PERCENT = 0.25   # % damage gốc của chiêu
    DURATION       = 5.0    # giây đá lăn tồn tại tối đa nếu không trúng ai/không đủ MAX_ROLL_DISTANCE
    ROLL_RADIUS    = 22.0   # bán kính va chạm — to hơn đạn thường, cũng là bán kính tảng đá sau khi rơi
    ROLL_SPEED     = 220.0  # pixel/giây — lăn chậm nhưng dai
    MAX_ROLL_DISTANCE = 300.0   # lăn xa quá mức này mà chưa trúng ai thì tự rơi xuống
    POINT_COST     = 1      # Trigger "Common" trong thẻ tham khảo — rẻ hơn Outburst

    # ── Đạn có quỹ đạo (Fire) ────────────────────────────────────────────────

    def on_fire(self, bullet, context: dict) -> list:
        # Trả tảng đá + đạn phụ do NHÁNH CON sinh ra (VD lưỡi kiếm quay quanh
        # chính tảng đá). Nhánh con áp lên tảng đá, không đụng đạn chính.
        boulder = self.trigger_once(bullet.x, bullet.y, bullet.damage, context,
                                    dir_x=bullet.vx, dir_y=bullet.vy)
        if boulder is None:
            return []
        return [boulder] + self._attach_subtree_and_fire(boulder, context)

    def on_update(self, bullet, dt: float, context: dict = None) -> None:
        pass   # chỉ nổ lúc spawn — không lặp theo quãng đường
    
        
    # ── Trigger dùng chung cho mọi hệ (kể cả Wind/Lightning/Ice) ─────────────

    def trigger_once(self, x: float, y: float, base_damage: float, context: dict,
                     dir_x: float = None, dir_y: float = None,
                     duration_mult: float = 1.0, source=None, **_extra):
        """Tạo 1 tảng đá lăn tại (x, y) và TRẢ VỀ (không tự append). Người gọi
        chịu trách nhiệm thêm vào danh sách đạn. dir_x/dir_y: hướng lăn (None
        → ngẫu nhiên)."""
        from logic.entities.bullet import Bullet

        if dir_x is None or dir_y is None or math.hypot(dir_x, dir_y) < 1e-6:
            angle = random.uniform(0.0, math.tau)
            ux, uy = math.cos(angle), math.sin(angle)
        else:
            d = math.hypot(dir_x, dir_y)
            ux, uy = dir_x / d, dir_y / d

        boulder = Bullet(x, y, x + ux * 100.0, y + uy * 100.0,
                         base_damage * self.DAMAGE_PERCENT * self.stack, None)
        boulder.vx, boulder.vy   = ux * self.ROLL_SPEED, uy * self.ROLL_SPEED
        boulder.radius           = self.ROLL_RADIUS
        boulder.LIFETIME         = self.DURATION
        boulder.pierce_remaining = 0   # dừng lăn (rơi xuống) ngay khi trúng quái đầu tiên
        boulder.visual_type      = 'rolling_boulder'
        # game_loop._fall_rolling_stones() dùng điểm xuất phát này để biết đá
        # đã lăn được bao xa, tự rơi xuống khi đủ MAX_ROLL_DISTANCE.
        boulder._roll_origin_x   = x
        boulder._roll_origin_y   = y

        return boulder

    def get_display_name(self) -> str: return "Rolling Stone"

    def get_description(self) -> str:
        pct = int(self.DAMAGE_PERCENT * 100 * self.stack)
        return (f"On cast, rolls a boulder: {pct}% dmg, stops on first hit "
                f"or after rolling a while, then stays as a permanent rock (Cost: {self.POINT_COST})")

    def get_color(self) -> tuple: return (150, 120, 90)
