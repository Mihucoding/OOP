from logic.rune.rune_component import ModifierRune

class DestructivePathModifier(ModifierRune):
    """
    Rune "Con Đường Hủy Diệt" — để lại 1 vệt lửa LIÊN TỤC dọc đường đã đi qua,
    mỗi điểm trên vệt tự tồn tại TRAIL_DURATION giây rồi mờ dần, áp 1 Burn cho
    địch chạm vào (xem FireTrailEffect).

    - Đạn có quỹ đạo (Fire/Wind): on_fire() tạo 1 FireTrailEffect tại điểm bắn,
      on_update() nối thêm điểm mỗi frame khi đạn bay — đạn đi tới đâu vệt
      hiện ra tới đó.
    - Lightning/Ice (đòn tức thời, không có Bullet để tự on_update): game_loop
      tự tìm rune này trong cây (giống cách tìm HitAndRunModifier) rồi gọi
      leave_trail_along() với 2 đầu mút gai/tia — rải điểm dọc suốt chiều dài
      NGAY một lượt, thay vì chỉ 1 điểm tại chân người chơi như bản cũ.
    """
    TRAIL_INTERVAL = 22.0    # px giữa 2 điểm lấy mẫu trên vệt
    TRAIL_DURATION = 5.0     # giây mỗi điểm tồn tại
    TRAIL_RADIUS   = 26.0    # bán kính vùng gây Burn quanh mỗi điểm
    BURN_STACK     = 1
    POINT_COST     = 1       # Common Modifier — rẻ

    # ── Đạn có quỹ đạo (Fire / Wind) ─────────────────────────────────────────

    def on_fire(self, bullet, context: dict) -> list:
        bullet._trail_fx = self._spawn_trail(bullet.x, bullet.y, context)
        return []

    def on_update(self, bullet, dt: float, context: dict = None) -> None:
        trail = getattr(bullet, '_trail_fx', None)
        if trail is not None:
            trail.add_point(bullet.x, bullet.y, self.TRAIL_INTERVAL)

    # ── Đòn tức thời (Ice / Lightning) — game_loop tự gọi khi tìm thấy rune này ──

    def leave_trail_along(self, x1: float, y1: float, x2: float, y2: float,
                          context: dict) -> None:
        """Rải điểm dọc đoạn (x1,y1)-(x2,y2) NGAY một lượt (dùng cho gai băng/
        tia sét — đòn tức thời, không có quá trình bay để on_update theo)."""
        import math
        trail = self._spawn_trail(x1, y1, context)
        dist = math.hypot(x2 - x1, y2 - y1)
        steps = max(1, int(dist // self.TRAIL_INTERVAL))
        for i in range(1, steps + 1):
            t = i / steps
            trail.add_point(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)

    # ── Dùng chung ────────────────────────────────────────────────────────────

    def _spawn_trail(self, x: float, y: float, context: dict):
        from logic.entities.attack_effect import FireTrailEffect
        from logic.rune.rune_tree import RuneTree
        from logic.rune.elements.fire_rune import FireRune

        fire = FireRune()
        fire.element_stack = self.BURN_STACK
        tree = RuneTree()
        tree.add_element(fire)

        trail = FireTrailEffect(x, y, self.TRAIL_RADIUS, self.TRAIL_DURATION, tree)
        active_effects = context.get('active_effects')
        if active_effects is not None:
            active_effects.append(trail)
        return trail

    def get_display_name(self) -> str: return "Destructive Path"

    def get_description(self) -> str:
        # Khớp y chang thẻ gốc (nội dung + format bullet ◆).
        return (f"◆ Leaves a trail of fire that lasts {self.TRAIL_DURATION:.0f}s "
                f"and applies {self.BURN_STACK} Burn")

    def get_color(self) -> tuple: return (255, 120, 50)
