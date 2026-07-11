from logic.rune.rune_component import ModifierRune

class FreneticEnergyModifier(ModifierRune):
    """
    Rune "Năng Lượng Cuồng Nộ" — không đụng trực tiếp vào bullet, mà GẮN VÀO
    Trigger gần nhất phía trên nó trong cây (hoặc thẳng vào Spell gốc nếu
    không có Trigger nào ở trên) — đúng luật "attach to nearest Trigger above,
    else Spell" của Echoes of Mystralia:
      - Spawn Count +2  : cái nó gắn vào giờ tự cast/spawn thêm 2 lần.
      - Damage x0.8     : mỗi lần cast/spawn đó giảm còn 80% damage.
      - Cast trong 1 cone 120° (thay vì luôn thẳng 1 hướng).

    Hoạt động trên cả 4 hệ: Fire/Wind đi qua RuneTree.on_fire() trực tiếp;
    Ice/Lightning không có Bullet object nên game_loop tự gọi
    RuneTree.resolve_cast_graph()/resolve_batch_positions() riêng (xem
    _release_ice_charge/_channel_lightning_attack).

    Đóng góp qua add_batch() (không ghi đè damage_mult/speed_mult/size_mult
    hay batch của rune khác) — nếu cùng gắn vào 1 cast với Stars Aligned,
    2 rune vẫn giữ ĐÚNG đội hình riêng (cone toả ngẫu nhiên của Frenetic không
    lẫn với line dàn hàng của Stars Aligned).
    """
    SPAWN_COUNT_DELTA = 2
    DAMAGE_MULT       = 0.8
    CONE_DEG          = 120.0
    POINT_COST        = 1   # Common Modifier

    def contribute_cast(self, cast_params) -> None:
        """Gọi bởi RuneTree._walk_cast_graph — chỉnh tham số của cái mình gắn vào."""
        cast_params.damage_mult *= self.DAMAGE_MULT ** self.stack
        cast_params.add_batch(self.SPAWN_COUNT_DELTA * self.stack, 'cone', self.CONE_DEG)

    # Không tham gia hệ on_fire/on_update cũ — toàn bộ hiệu ứng đi qua contribute_cast.
    def on_fire(self, bullet, context: dict) -> list:
        return []

    def on_update(self, bullet, dt: float, context: dict = None) -> None:
        pass

    def get_display_name(self) -> str: return "Frenetic Energy"

    def get_description(self) -> str:
        pct = int(self.DAMAGE_MULT ** self.stack * 100)
        n   = self.SPAWN_COUNT_DELTA * self.stack
        return (f"Gắn vào Spell/Trigger gần nhất phía trên: Spawn Count +{n}, "
                f"Damage x{pct/100:.2f}, cone {int(self.CONE_DEG)}° (Cost: {self.POINT_COST})")

    def get_color(self) -> tuple: return (60, 220, 200)
