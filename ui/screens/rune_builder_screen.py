"""
RuneBuilderScreen — Màn hình Rune Builder kiểu Mylistra.

Layout (1280×720):
┌───────────────┬──────────────────────────────────┐
│  INVENTORY    │  [Chiêu 1] [Chiêu 2] [Chiêu 3]   │
│  (300px)      │                                   │
│               │          [Base Spell]             │
│  [Rune 1]     │         /            \            │
│  [Rune 2]     │      [L1]            [R1]         │
│  [Rune 3]     │       |               |           │
│  ...          │      [L2]            [R2]         │
└───────────────┴──────────────────────────────────┘

Tương tác:
  • Click rune trong inventory → chọn (highlight)
  • Click slot trống hợp lệ   → đặt rune đã chọn vào slot
  • Click slot có rune + đang chọn rune → swap (nếu compatible)
  • Click slot có rune + không chọn     → lấy rune về inventory
  • Click rune đang chọn lại            → bỏ chọn
  • ESC / Tab / Enter                   → lưu và đóng
"""
import math
import pygame

SCREEN_W, SCREEN_H = 1280, 720

# ── Kích thước panel ──────────────────────────────────────────────────────────
INV_PANEL_W  = 290
INV_X        = 10
INV_Y_START  = 110
INV_ITEM_H   = 66
INV_ITEM_W   = INV_PANEL_W - 20

NODE_R       = 38   # Bán kính slot node
SPELL_BTN_W  = 150
SPELL_BTN_H  = 34
SPELL_BTN_Y  = 72

# ── Màu ───────────────────────────────────────────────────────────────────────
COL_BG         = (12, 12, 22)
COL_PANEL      = (20, 20, 35)
COL_LINE       = (80, 80, 100)
COL_LINE_ACT   = (140, 140, 170)   # đường nối active
COL_EMPTY      = (50, 50, 65)
COL_EMPTY_BD   = (90, 90, 110)
COL_VALID_BD   = (80, 200, 80)     # viền xanh: có thể đặt vào
COL_INVALID_BD = (80, 80, 80)
COL_SELECTED   = (255, 220, 50)    # màu viền item đang chọn
COL_INACTIVE   = (40, 40, 50)      # slot có rune nhưng parent trống
COL_DIVIDER    = (50, 50, 70)
COL_TEXT       = (220, 220, 220)
COL_HINT       = (100, 100, 120)


TAB_INV   = 'inventory'
TAB_STATS = 'stats'
TAB_BTN_H = 32
TAB_BTN_W = (INV_PANEL_W - 20) // 2


class RuneBuilderScreen:
    """Màn hình Rune Builder toàn màn hình."""

    def __init__(self, screen: pygame.Surface, font_big, font_small):
        self.screen     = screen
        self.font_big   = font_big
        self.font_small = font_small

        # State tương tác
        self.selected_rune     = None
        self.selected_inv_idx  = -1
        self.status_msg        = ""
        self.status_timer      = 0.0
        self.left_tab          = TAB_INV   # 'inventory' | 'stats'

    # ── Vẽ ────────────────────────────────────────────────────────────────────

    def draw(self, player, dt: float = 0.0) -> None:
        self.screen.fill(COL_BG)
        if self.status_timer > 0:
            self.status_timer -= dt

        self._draw_left_tabs()
        if self.left_tab == TAB_INV:
            self._draw_inventory_panel(player)
        else:
            self._draw_stats_panel(player)
        self._draw_divider()
        self._draw_spell_buttons(player)
        self._draw_tree_canvas(player)
        self._draw_header(player)
        self._draw_instructions()
        if self.status_timer > 0:
            self._draw_status()

    # ── Header ────────────────────────────────────────────────────────────────

    def _draw_header(self, player) -> None:
        title      = self.font_big.render("RUNE  BUILDER", True, (255, 210, 60))
        title_rect = title.get_rect(midtop=(SCREEN_W // 2, 8))
        self.screen.blit(title, title_rect)

        # Số rune trong inventory
        inv_count = len(player.rune_inventory)
        count_txt = self.font_small.render(
            f"Inventory: {inv_count} rune{'s' if inv_count != 1 else ''}", True, (160, 160, 180))
        self.screen.blit(count_txt, (INV_X, 70))

    def _draw_instructions(self) -> None:
        hints = [
            "Click inventory → chọn rune",
            "Click slot trống → đặt rune",
            "Click slot có rune → lấy lại",
            "ESC / Tab → lưu & đóng",
        ]
        y = SCREEN_H - len(hints) * 22 - 10
        for h in hints:
            surf = self.font_small.render(h, True, COL_HINT)
            self.screen.blit(surf, (INV_X, y))
            y += 22

    def _draw_status(self) -> None:
        surf = self.font_small.render(self.status_msg, True, (255, 100, 100))
        self.screen.blit(surf, surf.get_rect(center=(INV_PANEL_W // 2 + INV_X, 95)))

    # ── Left Tab Buttons ──────────────────────────────────────────────────────

    def _draw_left_tabs(self) -> None:
        tabs = [(TAB_INV, "Inventory"), (TAB_STATS, "Chỉ số")]
        for i, (tab_id, label) in enumerate(tabs):
            x      = INV_X + i * (TAB_BTN_W + 8)
            active = (self.left_tab == tab_id)
            bg     = (50, 60, 85) if active else (25, 25, 38)
            bd     = (255, 215, 0) if active else (70, 70, 90)
            pygame.draw.rect(self.screen, bg,
                             (x, 36, TAB_BTN_W, TAB_BTN_H), border_radius=5)
            pygame.draw.rect(self.screen, bd,
                             (x, 36, TAB_BTN_W, TAB_BTN_H), 2, border_radius=5)
            lbl = self.font_small.render(label, True,
                                         (255, 215, 0) if active else (160, 160, 180))
            self.screen.blit(lbl, lbl.get_rect(center=(x + TAB_BTN_W // 2, 36 + TAB_BTN_H // 2)))

    # ── Stats Panel ───────────────────────────────────────────────────────────

    def _draw_stats_panel(self, player) -> None:
        panel = pygame.Surface((INV_PANEL_W, SCREEN_H), pygame.SRCALPHA)
        panel.fill((18, 18, 30, 220))
        self.screen.blit(panel, (0, 0))

        y = INV_Y_START
        title = self.font_small.render("— CHỈ SỐ NHÂN VẬT —", True, (220, 180, 80))
        self.screen.blit(title, title.get_rect(centerx=INV_PANEL_W // 2, y=y))
        y += 30

        stats = [
            ("HP",           f"{int(player.hp)} / {player.max_hp}",  (220, 60,  60)),
            ("Tốc độ",       f"{int(player.speed)}",                  (100, 200, 255)),
            ("Sát thương",   f"{int(player.damage)}",                 (255, 160, 50)),
            ("Giáp",         f"{int(player.armor)}%",                 (120, 180, 255)),
            ("Hồi máu",      f"{player.hp_regen:.1f}/s",              (80,  220, 120)),
            ("May mắn",      f"{int(player.lucky)}",                  (255, 230, 80)),
            ("Crit",         f"{player.get_crit_chance()*100:.1f}%",  (255, 80,  80)),
            ("XP Range",     f"+{int(player.xp_range)}px",            (200, 255, 160)),
            ("Ult Cooldown", f"{player.ultimate_cooldown:.1f}s",      (200, 80,  255)),
        ]
        for label, value, color in stats:
            lbl_s = self.font_small.render(label, True, (160, 160, 180))
            val_s = self.font_small.render(value, True, color)
            self.screen.blit(lbl_s, (INV_X + 4, y))
            self.screen.blit(val_s, (INV_X + INV_ITEM_W - val_s.get_width() - 4, y))
            pygame.draw.line(self.screen, (40, 40, 55),
                             (INV_X, y + 20), (INV_PANEL_W - 4, y + 20), 1)
            y += 26

        # Chiêu hiện tại
        y += 10
        sep = self.font_small.render("— CHIÊU ĐANG ACTIVE —", True, (160, 180, 220))
        self.screen.blit(sep, sep.get_rect(centerx=INV_PANEL_W // 2, y=y))
        y += 28
        active_spell = player.get_active_spell()
        desc = active_spell.rune_tree.describe()
        d_surf = self.font_small.render(desc[:30], True, (180, 210, 180))
        self.screen.blit(d_surf, d_surf.get_rect(centerx=INV_PANEL_W // 2, y=y))
        y += 24
        for rune in active_spell.rune_tree.get_all_runes():
            stack = getattr(rune, 'element_stack', getattr(rune, 'stack', 1))
            txt   = rune.get_display_name() + (f" x{stack}" if stack > 1 else "")
            r_surf = self.font_small.render(txt, True, rune.get_color())
            self.screen.blit(r_surf, (INV_X + 8, y))
            y += 22
            if y > SCREEN_H - 60:
                break

    # ── Inventory Panel ───────────────────────────────────────────────────────

    def _draw_inventory_panel(self, player) -> None:
        # Nền panel
        panel = pygame.Surface((INV_PANEL_W, SCREEN_H), pygame.SRCALPHA)
        panel.fill((18, 18, 30, 220))
        self.screen.blit(panel, (0, 0))

        inventory = player.rune_inventory
        if not inventory:
            msg  = self.font_small.render("Chưa có rune.", True, COL_HINT)
            msg2 = self.font_small.render("Hãy lên cấp!", True, COL_HINT)
            self.screen.blit(msg,  (INV_X + 10, INV_Y_START))
            self.screen.blit(msg2, (INV_X + 10, INV_Y_START + 24))
            return

        for i, rune in enumerate(inventory):
            y     = INV_Y_START + i * INV_ITEM_H
            rect  = pygame.Rect(INV_X, y, INV_ITEM_W, INV_ITEM_H - 6)
            color = rune.get_color()
            r, g, b = color

            # Nền item
            bg_surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            bg_surf.fill((r, g, b, 40))
            self.screen.blit(bg_surf, rect.topleft)

            # Viền (highlight nếu đang chọn)
            border_color = COL_SELECTED if i == self.selected_inv_idx else color
            border_w     = 3 if i == self.selected_inv_idx else 1
            pygame.draw.rect(self.screen, border_color, rect, border_w, border_radius=6)

            # Icon nhỏ (hình tròn màu)
            pygame.draw.circle(self.screen, color,
                               (rect.x + 22, rect.centery), 14)

            # Tên
            name_surf = self.font_small.render(rune.get_display_name(), True, COL_TEXT)
            self.screen.blit(name_surf, (rect.x + 44, rect.y + 6))

            # Loại
            type_lbl = "Element" if hasattr(rune, 'on_update') and not hasattr(rune, '_children') else "Modifier"
            from logic.rune.rune_component import ElementRune, ModifierRune
            type_lbl  = "Element" if isinstance(rune, ElementRune) else "Modifier"
            type_surf = self.font_small.render(type_lbl, True, (r // 2 + 80, g // 2 + 80, b // 2 + 80))
            self.screen.blit(type_surf, (rect.x + 44, rect.y + 28))

            # Giới hạn hiển thị
            if y + INV_ITEM_H > SCREEN_H - 130:
                more = len(inventory) - i - 1
                if more > 0:
                    more_surf = self.font_small.render(f"... và {more} rune khác", True, COL_HINT)
                    self.screen.blit(more_surf, (INV_X + 10, y + INV_ITEM_H))
                break

    def _draw_divider(self) -> None:
        pygame.draw.line(self.screen, COL_DIVIDER,
                         (INV_PANEL_W + 5, 60), (INV_PANEL_W + 5, SCREEN_H - 10), 1)

    def _draw_spell_buttons(self, player) -> None:
        total_w = len(player.spells) * SPELL_BTN_W + (len(player.spells) - 1) * 12
        start_x = (INV_PANEL_W + SCREEN_W) // 2 - total_w // 2
        for i, spell in enumerate(player.spells):
            rect = pygame.Rect(
                start_x + i * (SPELL_BTN_W + 12),
                SPELL_BTN_Y,
                SPELL_BTN_W,
                SPELL_BTN_H,
            )
            active = i == player.active_spell_index
            bg = (55, 70, 95) if active else (35, 35, 50)
            bd = (255, 220, 80) if active else (90, 90, 110)
            pygame.draw.rect(self.screen, bg, rect, border_radius=6)
            pygame.draw.rect(self.screen, bd, rect, 2, border_radius=6)
            label = self.font_small.render(spell.name, True, COL_TEXT)
            self.screen.blit(label, label.get_rect(center=rect.center))

    # ── Tree Canvas ───────────────────────────────────────────────────────────

    def _draw_tree_canvas(self, player) -> None:
        active_spell = player.get_active_spell()
        rune_slots = active_spell.rune_slots

        # ── Label section ─────────────────────────────────────────────────────
        spell_lbl = self.font_small.render(f"[ {active_spell.name.upper()} ]", True, (160, 180, 220))
        self.screen.blit(spell_lbl, spell_lbl.get_rect(center=(760, 120)))

        # Ghi chú đạn thường luôn tồn tại
        note = self.font_small.render("Đạn thường luôn bắn — Hệ chính là tùy chọn", True, (90, 90, 110))
        self.screen.blit(note, note.get_rect(center=(760, 590)))

        # ── Đường nối: parent-child giữa các modifier slots ───────────────────
        for s in rune_slots.slots:
            if s.parent_id is not None:
                parent    = rune_slots.get(s.parent_id)
                is_active = rune_slots.is_active(s.id)
                color     = COL_LINE_ACT if is_active else COL_LINE
                pygame.draw.line(self.screen, color,
                                 (parent.x, parent.y), (s.x, s.y), 2)

        # ── Vẽ từng slot ──────────────────────────────────────────────────────
        slot_labels = {0: "Hệ chính", 1: "L1", 2: "R1", 3: "L2", 4: "R2"}
        for s in rune_slots.slots:
            label = slot_labels.get(s.id)
            self._draw_slot(s, rune_slots, extra_label=label)

        # ── Combo hint ────────────────────────────────────────────────────────
        self._draw_combo_hint(player)

    def _draw_dashed_line(self, start, end, color, width=1, dash=8, gap=5):
        """Vẽ đường nét đứt giữa 2 điểm."""
        import math
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        dist = math.hypot(dx, dy)
        if dist == 0:
            return
        steps = int(dist / (dash + gap))
        for i in range(steps):
            t0 = i * (dash + gap) / dist
            t1 = (i * (dash + gap) + dash) / dist
            t1 = min(t1, 1.0)
            p0 = (int(start[0] + dx * t0), int(start[1] + dy * t0))
            p1 = (int(start[0] + dx * t1), int(start[1] + dy * t1))
            pygame.draw.line(self.screen, color, p0, p1, width)

    def _draw_slot(self, slot, rune_slots, extra_label: str = None) -> None:
        x, y = slot.x, slot.y
        active = rune_slots.is_active(slot.id)

        if slot.is_empty():
            # Xác định có thể đặt rune đang chọn không
            can_drop = (self.selected_rune is not None
                        and rune_slots.can_place(slot.id, self.selected_rune))

            # Element slot dùng viền vàng nhạt để phân biệt
            if slot.slot_type == 'element':
                bg_color = (40, 38, 20)
                bd_color = COL_VALID_BD if can_drop else (160, 140, 50)
            else:
                bg_color = COL_EMPTY
                bd_color = COL_VALID_BD if can_drop else COL_EMPTY_BD
            bd_w = 3 if can_drop else (2 if slot.slot_type == 'element' else 1)

            pygame.draw.circle(self.screen, bg_color, (x, y), NODE_R)
            pygame.draw.circle(self.screen, bd_color, (x, y), NODE_R, bd_w)

            # Label loại slot (dùng extra_label nếu có)
            lbl  = extra_label if extra_label else "Rune"
            surf = self.font_small.render(lbl, True, bd_color)
            self.screen.blit(surf, surf.get_rect(center=(x, y - 6)))

            # Sub-hint cho element slot
            if slot.slot_type == 'element':
                sub = self.font_small.render("(Element)", True, (100, 90, 40))
                self.screen.blit(sub, sub.get_rect(center=(x, y + 12)))

            # Dấu + nếu có thể thả
            if can_drop:
                plus = self.font_big.render("+", True, COL_VALID_BD)
                self.screen.blit(plus, plus.get_rect(center=(x, y - 4)))

        else:
            from logic.rune.rune_component import ElementRune as _ElemRune
            rune  = slot.rune
            color = rune.get_color()
            r, g, b = color

            # Modifier slot chứa same-element → hiển thị dạng "stack booster"
            is_elem_booster = (slot.slot_type == 'modifier'
                               and isinstance(rune, _ElemRune))

            # Nền mờ glow
            glow = pygame.Surface((NODE_R * 2 + 20, NODE_R * 2 + 20), pygame.SRCALPHA)
            alpha = 60 if active else 20
            pygame.draw.circle(glow, (r, g, b, alpha),
                               (NODE_R + 10, NODE_R + 10), NODE_R + 10)
            self.screen.blit(glow, (x - NODE_R - 10, y - NODE_R - 10))

            # Thân node — element booster dùng nền tối hơn + viền vàng
            if is_elem_booster:
                node_color = (r // 3, g // 3, b // 3) if active else COL_INACTIVE
            else:
                node_color = color if active else COL_INACTIVE
            pygame.draw.circle(self.screen, node_color, (x, y), NODE_R)

            # Viền — booster dùng viền vàng nhạt
            if is_elem_booster and active:
                bd_color = (220, 190, 60)
            else:
                bd_color = (255, 255, 255) if active else (80, 80, 80)
            pygame.draw.circle(self.screen, bd_color, (x, y), NODE_R, 2)

            # Nhãn trung tâm
            if is_elem_booster:
                # Hiện dấu "+" màu rune
                plus = self.font_big.render("+", True, color)
                self.screen.blit(plus, plus.get_rect(center=(x, y)))
            else:
                abbr = self.font_big.render(rune.get_display_name()[:2], True, (0, 0, 0))
                self.screen.blit(abbr, abbr.get_rect(center=(x, y)))

            # Tên đầy đủ dưới node
            name_col  = COL_TEXT if active else (80, 80, 80)
            if is_elem_booster:
                name_surf = self.font_small.render(f"+{rune.get_display_name()}", True, name_col)
            else:
                name_surf = self.font_small.render(rune.get_display_name(), True, name_col)
            self.screen.blit(name_surf, name_surf.get_rect(center=(x, y + NODE_R + 16)))

            # Stack count
            if not is_elem_booster:
                if slot.slot_type == 'element':
                    # Tính live: 1 + số cùng hệ trong modifier slots đang active
                    from logic.rune.rune_component import ElementRune as _E
                    live_stack = 1 + sum(
                        1 for s in rune_slots.slots
                        if s.slot_type == 'modifier'
                        and rune_slots.is_active(s.id)
                        and isinstance(s.rune, _E)
                        and type(s.rune) == type(rune)
                    )
                    stack = live_stack
                else:
                    stack = getattr(rune, 'stack', 1)
                if stack > 1:
                    stk = self.font_small.render(f"x{stack}", True, (255, 220, 50))
                    self.screen.blit(stk, (x + NODE_R - 4, y - NODE_R - 2))

            if extra_label:
                lbl_color = (220, 190, 60) if slot.slot_type == 'element' else (160, 160, 120)
                sub_s = self.font_small.render(extra_label, True, lbl_color)
                self.screen.blit(sub_s, sub_s.get_rect(center=(x, y - NODE_R - 18)))

            # Inactive warning
            if not active:
                warn = self.font_small.render("(inactive)", True, (100, 80, 80))
                self.screen.blit(warn, warn.get_rect(center=(x, y + NODE_R + 32)))

    def _draw_combo_hint(self, player) -> None:
        tree  = player.get_active_spell().rune_slots.build_rune_tree()
        desc  = tree.describe()
        surf  = self.font_small.render(f"Combo hiện tại:  {desc}", True, (180, 200, 180))
        rect  = surf.get_rect(midbottom=(
            (INV_PANEL_W + SCREEN_W) // 2, SCREEN_H - 10))
        self.screen.blit(surf, rect)

    # ── Event Handling ────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event, player) -> bool:
        """Trả về True nếu cần đóng Builder và rebuild tree."""
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_TAB, pygame.K_RETURN):
                self._close(player)
                return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # Tab buttons (Inventory / Stats)
            if self._handle_tab_click(mx, my):
                return False
            if self._handle_spell_button_click(mx, my, player):
                return False
            # Ưu tiên click slot (canvas bên phải)
            if mx > INV_PANEL_W:
                self._handle_slot_click(mx, my, player)
            elif self.left_tab == TAB_INV:
                self._handle_inventory_click(mx, my, player)

        return False

    def _handle_tab_click(self, mx: int, my: int) -> bool:
        tabs = [(TAB_INV, "Inventory"), (TAB_STATS, "Chỉ số")]
        for i, (tab_id, _) in enumerate(tabs):
            x = INV_X + i * (TAB_BTN_W + 8)
            rect = pygame.Rect(x, 36, TAB_BTN_W, TAB_BTN_H)
            if rect.collidepoint(mx, my):
                self.left_tab = tab_id
                return True
        return False

    def _handle_inventory_click(self, mx: int, my: int, player) -> None:
        inventory = player.rune_inventory
        for i, rune in enumerate(inventory):
            y    = INV_Y_START + i * INV_ITEM_H
            rect = pygame.Rect(INV_X, y, INV_ITEM_W, INV_ITEM_H - 6)
            if rect.collidepoint(mx, my):
                if self.selected_inv_idx == i:
                    # Click lại → bỏ chọn
                    self.selected_rune    = None
                    self.selected_inv_idx = -1
                else:
                    self.selected_rune    = rune
                    self.selected_inv_idx = i
                return

    def _handle_spell_button_click(self, mx: int, my: int, player) -> bool:
        total_w = len(player.spells) * SPELL_BTN_W + (len(player.spells) - 1) * 12
        start_x = (INV_PANEL_W + SCREEN_W) // 2 - total_w // 2
        for i in range(len(player.spells)):
            rect = pygame.Rect(
                start_x + i * (SPELL_BTN_W + 12),
                SPELL_BTN_Y,
                SPELL_BTN_W,
                SPELL_BTN_H,
            )
            if rect.collidepoint(mx, my):
                player.rebuild_all_spells()
                player.set_active_spell(i)
                self.selected_rune = None
                self.selected_inv_idx = -1
                return True
        return False

    def _handle_slot_click(self, mx: int, my: int, player) -> None:
        rune_slots = player.get_active_spell().rune_slots

        for s in rune_slots.slots:
            dist = math.hypot(mx - s.x, my - s.y)
            if dist > rune_slots.NODE_RADIUS:
                continue

            if s.is_empty():
                # Slot trống: đặt rune đang chọn nếu hợp lệ
                if self.selected_rune is not None:
                    if rune_slots.place(s.id, self.selected_rune):
                        player.rune_inventory.pop(self.selected_inv_idx)
                        self.selected_rune    = None
                        self.selected_inv_idx = -1
                    else:
                        self._show_status("Không hợp lệ! Cần đặt slot cha trước.")
            else:
                # Slot có rune
                if self.selected_rune is not None:
                    # Swap nếu compatible
                    old = rune_slots.swap(s.id, self.selected_rune)
                    if old is not None:
                        player.rune_inventory.pop(self.selected_inv_idx)
                        player.rune_inventory.append(old)
                        self.selected_rune    = None
                        self.selected_inv_idx = -1
                    else:
                        self._show_status("Loại rune không khớp với slot!")
                else:
                    # Lấy rune về inventory
                    rune = rune_slots.remove(s.id)
                    if rune:
                        player.rune_inventory.append(rune)
            return

    def _show_status(self, msg: str, duration: float = 2.0) -> None:
        self.status_msg   = msg
        self.status_timer = duration

    def _close(self, player) -> None:
        """Rebuild tree và reset selection khi đóng."""
        player.rebuild_all_spells()
        self.selected_rune    = None
        self.selected_inv_idx = -1
        self.status_timer     = 0.0
