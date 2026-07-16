from logic.rune.rune_component import ModifierRune

class PerfectStormModifier(ModifierRune):
    """
    Rune Trigger "Perfect Storm" — Epic Trigger "Triggered on spawn": cast 1
    cơn lốc hút quái mỗi khi cái nó neo vào (Spell gốc, hoặc Trigger phía
    trên nếu có) spawn ra 1 lần.

    - Damage 40% : % damage của cái nó neo vào (Spell/Trigger phía trên).
    - Duration 5s, Size 4 (~50px bán kính).
    - Apply 8 Vortex : hút quái về tâm liên tục, mạnh dần theo stack.
    - Trôi chậm theo hướng đường đạn + lượn zigzag ngang nhẹ (xem VortexZone).

    Giống RollingStone/FuriousOutburst: có `trigger_once()` nên Lightning/Ice
    (đòn tức thời) tự động gọi được qua game_loop._find_triggerable_modifiers()
    — chạy như 1 Trigger đơn giản (1 lần/cast, không có "cast graph").
    Riêng khi đứng trong cây của Fire (đạn thật, đi qua rune_tree.on_fire()),
    nó CÓ tham gia cơ chế "cast graph" (IS_CAST_GRAPH_TRIGGER) — nếu có
    FreneticEnergyModifier gắn vào nó, số lần/số lượng cast sẽ nhân lên
    tương ứng (xem RuneTree.resolve_and_fire_cast_graph).
    """
    IS_CAST_GRAPH_TRIGGER = True
    IS_TRIGGER     = True
    TRIGGER_ON     = "spawn"

    DAMAGE_PERCENT = 0.40
    DURATION       = 5.0
    SIZE_TO_PX     = 12.5     # Size 4 -> ~50px bán kính (thu nhỏ từ 110px)
    SIZE           = 4
    VORTEX_STACKS  = 8
    # Lực hút hiệu dụng = PULL_STRENGTH * VORTEX_STACKS (xem status_effect.py
    # 'vortex') = 5.0 * 8 = 40 px/s — bằng ~nửa tốc độ đi bộ quái (80px/s),
    # đủ để "hút" nhẹ nhàng chứ không kéo dính tức thời về tâm.
    PULL_STRENGTH  = 5.0
    POINT_COST     = 3        # Epic Trigger — mạnh, tốn điểm

    # ── Đạn có quỹ đạo (Fire) — tham gia cast graph, xem RuneTree ────────────

    def on_fire(self, bullet, context: dict) -> list:
        return []   # toàn bộ logic chạy qua resolve_and_fire_cast_graph

    def on_update(self, bullet, dt: float, context: dict = None) -> None:
        pass

    # ── Trigger dùng chung (Lightning/Ice tức thời + cast graph của Fire) ────

    def trigger_once(self, x: float, y: float, base_damage: float, context: dict,
                     dir_x: float = None, dir_y: float = None,
                     angle_jitter_deg: float = 0.0,
                     speed_mult: float = 1.0, size_mult: float = 1.0,
                     duration_mult: float = 1.0, source=None, **_extra):
        """Tạo 1 VortexZone tại (x, y) và TRẢ VỀ None (tự append vào
        context['active_effects'], không phải context['bullets'] vì đây là
        AoE di động chứ không phải đạn). dir_x/dir_y: hướng đường đạn đã spawn
        ra nó — tornado trôi chậm theo hướng này (Ice/Lightning không có
        đường đạn nên VortexZone tự fallback hướng ngẫu nhiên). angle_jitter_deg
        không dùng. size_mult co giãn bán kính vùng; speed_mult (VD từ Stars
        Aligned) co giãn tốc độ hút."""
        from logic.entities.attack_effect import VortexZone

        radius = self.SIZE * self.SIZE_TO_PX * size_mult
        zone = VortexZone(
            x, y,
            damage=base_damage * self.DAMAGE_PERCENT * self.stack,
            radius=radius,
            duration=self.DURATION,
            vortex_stacks=self.VORTEX_STACKS,
            pull_strength=self.PULL_STRENGTH * speed_mult,
            visual_type='wind_vortex',
            dir_x=dir_x or 0.0,
            dir_y=dir_y or 0.0,
        )
        active_effects = context.get('active_effects')
        if active_effects is not None:
            active_effects.append(zone)
        return None

    def get_display_name(self) -> str: return "Perfect Storm"

    def get_description(self) -> str:
        # Khớp y chang thẻ gốc (nội dung + format bullet ◆, mỗi stat 1 dòng).
        pct = int(self.DAMAGE_PERCENT * 100 * self.stack)
        return ("Casts a tornado that pulls foes toward its center.\n"
                f"◆ Damage: {pct}%\n"
                f"◆ Duration: {int(self.DURATION)}s\n"
                f"◆ Size: {self.SIZE}\n"
                f"◆ Apply {self.VORTEX_STACKS} Vortex")

    def get_color(self) -> tuple: return (120, 230, 150)
