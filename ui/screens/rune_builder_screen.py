r"""
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
        self.inventory_rects   = []
        self.spell_button_rects = []
        self.background_snapshot = None

    def set_background_snapshot(self, surface: pygame.Surface) -> None:
        self.background_snapshot = surface.copy()

    # ── Vẽ ────────────────────────────────────────────────────────────────────

    def draw(self, player, dt: float = 0.0) -> None:
        if self.status_timer > 0:
            self.status_timer -= dt

        self._layout_watcher_slots(player)
        self._draw_watcher_background(player)
        self._draw_top_spell_bar(player)
        self._draw_ability_panel(player)
        self._draw_watcher_tree(player)
        self._draw_inventory_strip(player)
        self._draw_instructions()
        if self.status_timer > 0:
            self._draw_status()

    def _layout_watcher_slots(self, player) -> None:
        spell = player.get_active_spell()
        config = self._tree_config_for_element(
            self._element_key(spell), (895, 405), 250)
        coords = config["node_positions"]
        for slot in player.get_active_spell().rune_slots.slots:
            if slot.id in coords:
                slot.x, slot.y = coords[slot.id]

    def _draw_watcher_background(self, player) -> None:
        if self.background_snapshot is not None:
            small = pygame.transform.smoothscale(self.background_snapshot, (160, 90))
            blurred = pygame.transform.smoothscale(small, (SCREEN_W, SCREEN_H))
            self.screen.blit(blurred, (0, 0))
        else:
            self.screen.fill((7, 13, 27))

        dim = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        dim.fill((2, 7, 18, 130))
        self.screen.blit(dim, (0, 0))

        theme = self._theme_for_element(self._element_key(player.get_active_spell()))
        accent = theme["color"]
        for i in range(9):
            alpha = max(18, 64 - i * 5)
            ring = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            pygame.draw.circle(ring, (*accent, alpha), (895, 405), 610 - i * 56, 1)
            self.screen.blit(ring, (0, 0))

    def _draw_top_spell_bar(self, player) -> None:
        title = self.font_big.render("WATCHER'S HEART", True, (238, 246, 244))
        self.screen.blit(title, title.get_rect(center=(910, 34)))
        pygame.draw.line(self.screen, (62, 148, 126), (610, 72), (1210, 72), 2)
        pygame.draw.line(self.screen, (20, 70, 68), (650, 92), (1170, 92), 2)

        self.spell_button_rects = []
        total_w = len(player.spells) * 58 + (len(player.spells) - 1) * 16
        start_x = 910 - total_w // 2
        for i, spell in enumerate(player.spells):
            rect = pygame.Rect(start_x + i * 74, 82, 58, 36)
            self.spell_button_rects.append(rect)
            active = i == player.active_spell_index
            col = self._spell_theme_color(spell)
            bg = (17, 42, 48) if active else (9, 18, 28)
            pygame.draw.rect(self.screen, bg, rect, border_radius=18)
            pygame.draw.rect(self.screen, col if active else (60, 90, 92), rect, 2, border_radius=18)
            dot_x = rect.centerx
            dot_y = rect.centery
            pygame.draw.circle(self.screen, col, (dot_x, dot_y), 6)
            pygame.draw.circle(self.screen, (245, 255, 255), (dot_x, dot_y), 3)

    def _draw_ability_panel(self, player) -> None:
        spell = player.get_active_spell()
        profile = self._spell_profile(player, spell)
        x, y, w, h = 42, 112, 465, 455
        col = profile["color"]

        self._draw_neon_panel(pygame.Rect(x, y, w, h), col)
        self._draw_rune_crest((x + w // 2, y + 54), col, profile["glyph"], large=True)

        name = self.font_big.render(profile["name"], True, col)
        self.screen.blit(name, name.get_rect(center=(x + w // 2, y + 136)))

        text_y = y + 176
        for line in self._wrap_text(profile["description"], self.font_small, w - 56):
            surf = self.font_small.render(line, True, (238, 242, 246))
            self.screen.blit(surf, (x + 28, text_y))
            text_y += 25
        text_y += 6

        for label, value, value_color in profile["stats"]:
            bullet = self.font_small.render("+", True, (255, 255, 255))
            self.screen.blit(bullet, (x + 28, text_y))
            label_s = self.font_small.render(f"{label}: ", True, (245, 245, 245))
            self.screen.blit(label_s, (x + 54, text_y))
            val_s = self.font_small.render(value, True, value_color)
            self.screen.blit(val_s, (x + 54 + label_s.get_width(), text_y))
            text_y += 27

        attr_y = 574
        for title, body in profile["attributes"]:
            rect = pygame.Rect(42, attr_y, 465, 60)
            self._draw_neon_panel(rect, col, fill=(7, 13, 30, 220), border_alpha=110)
            title_s = self.font_small.render(title, True, col)
            self.screen.blit(title_s, (rect.x + 20, rect.y + 8))
            for i, line in enumerate(self._wrap_text(body, self.font_small, rect.w - 40)[:2]):
                body_s = self.font_small.render(line, True, (238, 242, 246))
                self.screen.blit(body_s, (rect.x + 20, rect.y + 31 + i * 16))
            attr_y += 68

    def _draw_inventory_strip(self, player) -> None:
        self.inventory_rects = []
        x0, y0 = 72, 46
        for i, rune in enumerate(player.rune_inventory[:8]):
            rect = pygame.Rect(x0 + i * 48, y0, 38, 38)
            self.inventory_rects.append((rect, i))
            color = self._rune_ui_color(rune)
            selected = i == self.selected_inv_idx
            pygame.draw.circle(self.screen, (10, 18, 28), rect.center, 21)
            pygame.draw.circle(self.screen, color, rect.center, 17)
            pygame.draw.circle(self.screen, (255, 255, 255) if selected else (8, 20, 26), rect.center, 19, 3)
            glyph = self._rune_glyph(rune)
            glyph_s = self.font_small.render(glyph, True, (8, 18, 22))
            self.screen.blit(glyph_s, glyph_s.get_rect(center=rect.center))

        badge = pygame.Rect(x0 + 8 * 48 + 8, y0 + 5, 32, 24)
        pygame.draw.rect(self.screen, (245, 245, 245), badge, border_radius=8)
        count_s = self.font_small.render(str(len(player.rune_inventory)), True, (18, 24, 32))
        self.screen.blit(count_s, count_s.get_rect(center=badge.center))

    def _draw_watcher_tree(self, player) -> None:
        spell = player.get_active_spell()
        rune_slots = spell.rune_slots
        key = self._element_key(spell)
        theme = self._theme_for_element(key)
        col = theme["color"]
        config = self._tree_config_for_element(key, (895, 405), 250)

        self._draw_hex_board(config, theme)

        for start, end in config["accent_edges"]:
            pygame.draw.line(self.screen, theme["accent"], start, end, 8)
            pygame.draw.line(self.screen, col, start, end, 3)

        links = config["edges"]
        for a, b in links:
            sa = rune_slots.get(a)
            sb = rune_slots.get(b)
            active = rune_slots.is_active(a) and rune_slots.is_active(b)
            link_col = col if active else (18, 34, 58)
            width = 5 if active else 3
            pygame.draw.line(self.screen, link_col, (sa.x, sa.y), (sb.x, sb.y), width)
            pygame.draw.line(self.screen, (4, 12, 24), (sa.x, sa.y), (sb.x, sb.y), 1)

        for slot in rune_slots.slots:
            self._draw_watcher_slot(slot, rune_slots, col, compact_dots=config.get("compact_dots", False))

        for p in config["decorative_nodes"]:
            pygame.draw.circle(self.screen, (10, 20, 36), p, 18)
            pygame.draw.circle(self.screen, theme["muted"], p, 18, 2)

    def _draw_watcher_slot(self, slot, rune_slots, theme_color, compact_dots: bool = False) -> None:
        active = rune_slots.is_active(slot.id)
        can_drop = self.selected_rune is not None and rune_slots.can_place(slot.id, self.selected_rune)
        rune = slot.rune
        color = self._rune_ui_color(rune) if rune else theme_color

        if rune:
            self._draw_rune_crest((slot.x, slot.y), color, self._rune_glyph(rune), large=(slot.id == 0))
        else:
            radius = 30 if slot.id == 0 else 22
            pygame.draw.circle(self.screen, (6, 15, 28), (slot.x, slot.y), radius)
            pygame.draw.circle(self.screen, color if can_drop else (48, 102, 100), (slot.x, slot.y), radius, 3)
            if can_drop:
                plus = self.font_big.render("+", True, color)
                self.screen.blit(plus, plus.get_rect(center=(slot.x, slot.y - 2)))

        dot_gap = 15 if compact_dots else 18
        dot_r = 7 if compact_dots else 9
        dot_y = 43 if slot.id == 0 else 31
        for i in range(5):
            px = slot.x - dot_gap * 2 + i * dot_gap
            py = slot.y + dot_y
            pygame.draw.circle(self.screen, (4, 12, 22), (px, py), dot_r)
            pygame.draw.circle(self.screen, color if rune and active else (70, 120, 126), (px, py), dot_r, 2)

        if rune and not active:
            slash = self.font_small.render("LOCKED", True, (120, 80, 90))
            self.screen.blit(slash, slash.get_rect(center=(slot.x, slot.y + 66)))

    def _draw_hex_board(self, config: dict, theme: dict) -> None:
        color = theme["color"]
        points = config["hex_points"]
        board = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        pygame.draw.polygon(board, (*color, 58), points, 12)
        pygame.draw.polygon(board, (6, 10, 30, 138), points)
        pygame.draw.polygon(board, (*theme["muted"], 210), points, 4)
        pygame.draw.polygon(board, (*self._shade_color(color, 1.25), 145), points, 1)
        cx, cy = config["center"]

        for a, b in config.get("major_grid_lines", []):
            pygame.draw.line(board, (*self._shade_color(color, 0.45), 135), a, b, 2)

        guide_color = (*self._shade_color(color, 0.38), 95)
        guide_edges = config.get("grid_lines", config["guide_edges"])
        for a, b in guide_edges:
            pygame.draw.line(board, guide_color, a, b, 1)

        self.screen.blit(board, (0, 0))

    def _draw_neon_panel(
        self,
        rect: pygame.Rect,
        color: tuple,
        fill=(9, 15, 33, 225),
        border_alpha=150,
    ) -> None:
        surf = pygame.Surface(rect.size, pygame.SRCALPHA)
        surf.fill(fill)
        self.screen.blit(surf, rect.topleft)
        pygame.draw.rect(self.screen, (0, 0, 0), rect.move(4, 5), 2)
        pygame.draw.rect(self.screen, color, rect, 2)
        pygame.draw.rect(self.screen, (*color, border_alpha), rect.inflate(10, 10), 1)

    def _draw_rune_crest(self, center: tuple[int, int], color: tuple, glyph: str, large: bool = False) -> None:
        radius = 58 if large else 42
        points = self._hex_points(center[0], center[1], radius)
        glow = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        pygame.draw.polygon(glow, (*color, 75), self._hex_points(center[0], center[1], radius + 10))
        self.screen.blit(glow, (0, 0))
        pygame.draw.polygon(self.screen, self._shade_color(color, 0.62), points)
        pygame.draw.polygon(self.screen, self._shade_color(color, 1.22), points, 4)
        inner = self._hex_points(center[0], center[1], radius - 10)
        pygame.draw.polygon(self.screen, self._shade_color(color, 0.92), inner)
        glyph_font = self.font_big if large else self.font_small
        glyph_s = glyph_font.render(glyph, True, (245, 255, 255))
        self.screen.blit(glyph_s, glyph_s.get_rect(center=center))

    def _hex_points(self, cx: int, cy: int, radius: int) -> list[tuple[int, int]]:
        return [
            (
                int(cx + math.cos(math.radians(60 * i - 30)) * radius),
                int(cy + math.sin(math.radians(60 * i - 30)) * radius),
            )
            for i in range(6)
        ]

    def _lerp_point(self, a: tuple[int, int], b: tuple[int, int], t: float) -> tuple[int, int]:
        return (int(a[0] + (b[0] - a[0]) * t), int(a[1] + (b[1] - a[1]) * t))

    def _hex_lattice_points(self, center: tuple[int, int], radius: int) -> dict:
        vertices = self._hex_points(center[0], center[1], radius)
        intersections, grid = self._hex_grid_intersections(center, radius)
        return {
            "center": center,
            "vertices": vertices,
            "intersections": intersections,
            "grid_lines": grid["minor"],
            "major_grid_lines": grid["major"],
            "rays": {
                i: {
                    0.32: self._lerp_point(center, vertices[i], 0.32),
                    0.52: self._lerp_point(center, vertices[i], 0.52),
                    0.72: self._lerp_point(center, vertices[i], 0.72),
                }
                for i in range(6)
            },
            "chords": {
                (a, b, t): self._lerp_point(vertices[a], vertices[b], t)
                for a, b in ((5, 0), (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 2), (0, 3))
                for t in (0.35, 0.5, 0.65)
            },
        }

    def _hex_grid_intersections(self, center: tuple[int, int], radius: int) -> tuple[dict, list]:
        cx, cy = center
        row_step = radius / 4
        col_step = radius / 4
        sqrt3 = math.sqrt(3)

        def point(q: float, r: float) -> tuple[int, int]:
            return (int(cx + q * col_step * sqrt3), int(cy + r * row_step))

        named = {
            "top_left": point(-0.8, -2.05),
            "top_center": point(0.0, -1.55),
            "top_right": point(0.8, -2.05),
            "mid_left": point(-1.25, -0.45),
            "mid_center": point(0.0, -0.35),
            "mid_right": point(1.25, -0.45),
            "low_left": point(-1.55, 1.15),
            "low_center": point(0.0, 1.05),
            "low_right": point(1.55, 1.15),
            "bottom_center": point(0.0, 2.15),
        }

        vertices = self._hex_points(cx, cy, radius)
        edge_midpoints = [
            self._lerp_point(vertices[i], vertices[(i + 1) % 6], 0.5)
            for i in range(6)
        ]
        grid_lines = [
            (edge_midpoints[0], edge_midpoints[3]),
            (edge_midpoints[1], edge_midpoints[4]),
            (edge_midpoints[2], edge_midpoints[5]),
        ]
        major_lines = list(grid_lines)
        for t in (1 / 3, 2 / 3):
            grid_lines.extend([
                (self._lerp_point(edge_midpoints[5], edge_midpoints[0], t),
                 self._lerp_point(edge_midpoints[2], edge_midpoints[3], t)),
                (self._lerp_point(edge_midpoints[0], edge_midpoints[1], t),
                 self._lerp_point(edge_midpoints[3], edge_midpoints[4], t)),
                (self._lerp_point(edge_midpoints[1], edge_midpoints[2], t),
                 self._lerp_point(edge_midpoints[4], edge_midpoints[5], t)),
            ])

        return named, {"minor": grid_lines, "major": major_lines}

    def _theme_for_element(self, key: str) -> dict:
        themes = {
            "wind": {
                "color": (80, 245, 55),
                "accent": (34, 180, 36),
                "muted": (34, 110, 62),
                "glyph": "W",
            },
            "lightning": {
                "color": (58, 255, 218),
                "accent": (128, 90, 255),
                "muted": (35, 126, 118),
                "glyph": "Z",
            },
            "fire": {
                "color": (255, 104, 28),
                "accent": (205, 40, 24),
                "muted": (128, 63, 32),
                "glyph": "F",
            },
            "ice": {
                "color": (90, 200, 255),
                "accent": (80, 120, 255),
                "muted": (44, 103, 145),
                "glyph": "I",
            },
            "basic": {
                "color": (190, 220, 230),
                "accent": (70, 120, 132),
                "muted": (55, 92, 102),
                "glyph": "*",
            },
        }
        return themes.get(key, themes["basic"])

    def _element_key(self, spell) -> str:
        tree = spell.rune_slots.build_rune_tree()
        element = tree.elements[0] if tree.elements else None
        if element is None:
            return "basic"
        from logic.rune.elements.wind_rune import WindRune
        from logic.rune.elements.lightning_rune import LightningRune
        from logic.rune.elements.fire_rune import FireRune
        from logic.rune.elements.ice_rune import IceRune
        if isinstance(element, WindRune):
            return "wind"
        if isinstance(element, LightningRune):
            return "lightning"
        if isinstance(element, FireRune):
            return "fire"
        if isinstance(element, IceRune):
            return "ice"
        return "basic"

    def _tree_config_for_element(self, key: str, center: tuple[int, int], radius: int) -> dict:
        lattice = self._hex_lattice_points(center, radius)
        v = lattice["vertices"]
        c = lattice["chords"]
        grid = lattice["intersections"]
        ray = lambda idx, t: self._lerp_point(center, v[idx], t)

        configs = {
            "wind": {
                "node_positions": {
                    0: ray(5, 0.52),
                    1: ray(4, 0.52),
                    2: ray(0, 0.52),
                    3: ray(3, 0.72),
                    4: ray(1, 0.72),
                },
                "edges": [(0, 1), (1, 3), (3, 4), (4, 2), (2, 0)],
                "accent_edges": [(ray(5, 0.52), ray(4, 0.52)), (ray(3, 0.72), ray(4, 0.52)), (ray(1, 0.72), ray(0, 0.52))],
                "decorative_nodes": [ray(2, 0.72), ray(3, 0.52), ray(1, 0.52), c[(3, 4, 0.5)]],
            },
            "lightning": {
                "node_positions": {
                    0: c[(5, 0, 0.5)],
                    1: ray(4, 0.52),
                    2: ray(1, 0.52),
                    3: ray(2, 0.56),
                    4: ray(5, 0.72),
                },
                "edges": [(0, 1), (0, 2), (1, 3), (2, 4), (4, 3)],
                "accent_edges": [(c[(5, 0, 0.5)], ray(1, 0.52)), (ray(4, 0.52), ray(2, 0.56)), (ray(5, 0.72), ray(2, 0.56))],
                "decorative_nodes": [ray(0, 0.72), ray(3, 0.72), c[(5, 2, 0.5)], c[(0, 3, 0.5)]],
            },
            "fire": {
                "node_positions": {
                    0: ray(5, 0.52),
                    1: ray(4, 0.55),
                    2: ray(0, 0.55),
                    3: ray(3, 0.50),
                    4: ray(1, 0.50),
                },
                "edges": [(0, 1), (0, 2), (1, 4), (2, 3), (3, 4)],
                "accent_edges": [(ray(5, 0.52), ray(3, 0.50)), (ray(5, 0.52), ray(1, 0.50)), (ray(4, 0.55), ray(0, 0.55))],
                "decorative_nodes": [ray(2, 0.72), ray(3, 0.72), ray(1, 0.72), c[(2, 3, 0.5)]],
            },
            "ice": {
                "node_positions": {
                    0: grid["top_left"],
                    1: grid["mid_center"],
                    2: grid["mid_right"],
                    3: grid["low_center"],
                    4: grid["low_left"],
                },
                "edges": [(0, 1), (1, 3), (1, 2), (3, 4), (3, 2)],
                "accent_edges": [
                    (grid["top_left"], grid["mid_center"]),
                    (grid["mid_center"], grid["low_center"]),
                    (grid["mid_center"], grid["mid_right"]),
                    (grid["low_center"], grid["low_left"]),
                ],
                "decorative_nodes": [grid["mid_left"], grid["low_right"], grid["bottom_center"], grid["top_right"]],
                "compact_dots": True,
                "clean_guides": True,
            },
            "basic": {
                "node_positions": {
                    0: ray(5, 0.52),
                    1: ray(4, 0.52),
                    2: ray(0, 0.52),
                    3: ray(3, 0.52),
                    4: ray(1, 0.52),
                },
                "edges": [(0, 1), (0, 2), (1, 3), (2, 4)],
                "accent_edges": [],
                "decorative_nodes": [ray(2, 0.72), ray(3, 0.72), ray(1, 0.72), lattice["center"]],
            },
        }
        config = configs.get(key, configs["basic"])
        guide_edges = [
            (center, point) for point in v
        ] + [
            (v[5], v[2]), (v[0], v[3]), (v[4], v[1])
        ]
        return {
            "center": center,
            "radius": radius,
            "hex_points": v,
            "guide_edges": guide_edges,
            "grid_lines": lattice["grid_lines"],
            "major_grid_lines": lattice["major_grid_lines"],
            **config,
        }

    def _spell_theme_color(self, spell) -> tuple:
        return self._theme_for_element(self._element_key(spell))["color"]

    def _spell_profile(self, player, spell) -> dict:
        tree = spell.rune_slots.build_rune_tree()
        element = tree.elements[0] if tree.elements else None
        key = self._element_key(spell)
        theme = self._theme_for_element(key)
        name = "BASIC SHOT"
        description = "A reliable projectile shaped by the runes socketed into this spell."
        color = theme["color"]
        glyph = theme["glyph"]
        attrs = [("Rune Core", "Place an element in the first socket to define this spell.")]

        from logic.rune.elements.lightning_rune import LightningRune
        from logic.rune.elements.fire_rune import FireRune
        from logic.rune.elements.ice_rune import IceRune
        from logic.rune.elements.wind_rune import WindRune
        from logic.rune.elements.blood_rune import BloodRune
        element_bonus = 0
        if isinstance(element, LightningRune):
            name = "EXAE AURA"
            description = "A dangerous beam of lightning."
            stack = getattr(element, "element_stack", 1) if element else 1
            attrs = [
                ("Static", "Builds up until it casts a chain of lightning at nearby foes."),
                ("Overflow", "Casts lightning bolts while moving after prolonged use."),
            ]
            element_bonus = LightningRune.BONUS_DAMAGE * stack
        elif isinstance(element, FireRune):
            name = "FUR IGINI"
            description = "A short-ranged punch of fire."
            attrs = [("Burn", "Deals stacking damage over time.")]
        elif isinstance(element, IceRune):
            name = "GLACIA SPIRE"
            description = "A charged shard that grows into a piercing ice spike."
            attrs = [("Chill", "Slows enemies and extends control while charging.")]
        elif isinstance(element, WindRune):
            name = "CELE AER"
            description = "A boomerang gust that returns when called back."
            attrs = [("Pierce", "Passes through targets and pushes enemies away.")]
        elif isinstance(element, BloodRune):
            name = "BLOOD HEX"
            description = "A heavy blood projectile with punishing impact damage."
            color = element.get_color()
            glyph = "B"
            attrs = [("Hemorrhage", "Blood runes favor direct damage and aggressive hits.")]

        modifier_count = len(tree.modifiers)
        total_damage = player.damage + element_bonus
        stats = self._spell_stats_for_element(
            key, player, spell, total_damage, modifier_count, element)
        return {
            "name": name,
            "description": description,
            "color": color,
            "glyph": glyph,
            "stats": stats,
            "attributes": attrs,
        }

    def _spell_stats_for_element(
        self,
        key: str,
        player,
        spell,
        total_damage: float,
        modifier_count: int,
        element,
    ) -> list:
        theme = self._theme_for_element(key)
        if key == "wind":
            return [
                ("Damage", f"{total_damage + 40:.0f}", (255, 255, 255)),
                ("Duration", "0.24s", (255, 255, 255)),
                ("Speed", "30", (255, 255, 255)),
                ("Pierce", "2", theme["color"]),
                ("Modifiers", str(modifier_count), theme["color"]),
            ]
        if key == "lightning":
            return [
                ("Damage", f"{total_damage:.0f}", (255, 255, 255)),
                ("Duration", "2.0s", (255, 255, 255)),
                ("Length", "160", (255, 255, 255)),
                ("Apply", "20 Static", theme["color"]),
                ("Modifiers", str(modifier_count), theme["color"]),
            ]
        if key == "fire":
            burn = getattr(element, "BURN_DAMAGE", 8.0)
            return [
                ("Damage", f"{total_damage + 30:.0f}", (255, 255, 255)),
                ("Duration", "0.1s", (255, 255, 255)),
                ("Size", "1.5", (255, 255, 255)),
                ("Apply", f"{burn:.0f} Burn", theme["color"]),
                ("Modifiers", str(modifier_count), theme["color"]),
            ]
        if key == "ice":
            return [
                ("Damage", f"{total_damage:.0f}-{total_damage * 2.35:.0f}", (255, 255, 255)),
                ("Charge", "1.25s", (255, 255, 255)),
                ("Length", "130-360", (255, 255, 255)),
                ("Apply", "Chill", theme["color"]),
                ("Modifiers", str(modifier_count), theme["color"]),
            ]
        return [
            ("Damage", f"{total_damage:.0f}", (255, 255, 255)),
            ("Fire rate", f"{1 / max(spell.fire_rate, 0.01):.1f}/s", (255, 255, 255)),
            ("Range", "Bullet", (255, 255, 255)),
            ("Modifiers", str(modifier_count), theme["color"]),
            ("Ultimate CD", f"{player.ultimate_cooldown:.1f}s", (255, 255, 255)),
        ]

    def _shade_color(self, color: tuple[int, int, int], scale: float) -> tuple[int, int, int]:
        return tuple(max(0, min(255, int(part * scale))) for part in color)

    def _rune_ui_color(self, rune) -> tuple:
        if rune is None:
            return self._theme_for_element("basic")["color"]
        from logic.rune.elements.wind_rune import WindRune
        from logic.rune.elements.lightning_rune import LightningRune
        from logic.rune.elements.fire_rune import FireRune
        from logic.rune.elements.ice_rune import IceRune
        if isinstance(rune, WindRune):
            return self._theme_for_element("wind")["color"]
        if isinstance(rune, LightningRune):
            return self._theme_for_element("lightning")["color"]
        if isinstance(rune, FireRune):
            return self._theme_for_element("fire")["color"]
        if isinstance(rune, IceRune):
            return self._theme_for_element("ice")["color"]
        return rune.get_color()

    def _rune_glyph(self, rune) -> str:
        name = rune.get_display_name().lower()
        if "lightning" in name:
            return "Z"
        if "fire" in name:
            return "F"
        if "ice" in name:
            return "I"
        if "wind" in name:
            return "W"
        if "blood" in name:
            return "B"
        if "split" in name:
            return "S"
        if "bounce" in name:
            return "B"
        if "spiral" in name:
            return "@"
        if "haste" in name:
            return "H"
        return rune.get_display_name()[:1].upper()

    def _wrap_text(self, text: str, font, max_w: int) -> list[str]:
        words = text.split()
        lines = []
        cur = ""
        for word in words:
            test = word if not cur else f"{cur} {word}"
            if font.size(test)[0] <= max_w:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines

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
        hint = self.font_small.render("Click rune -> socket | filled socket -> remove | ESC / Tab -> close", True, (100, 160, 160))
        self.screen.blit(hint, hint.get_rect(midbottom=(910, SCREEN_H - 14)))

    def _draw_status(self) -> None:
        surf = self.font_small.render(self.status_msg, True, (255, 100, 100))
        self.screen.blit(surf, surf.get_rect(center=(274, 96)))

    # ── Left Tab Buttons ──────────────────────────────────────────────────────

    def _draw_left_tabs(self) -> None:
        tabs = [(TAB_INV, "Inventory"), (TAB_STATS, "Stats")]
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
        title = self.font_small.render("- CHARACTER STATS -", True, (220, 180, 80))
        self.screen.blit(title, title.get_rect(centerx=INV_PANEL_W // 2, y=y))
        y += 30

        stats = [
            ("HP",           f"{int(player.hp)} / {player.max_hp}",  (220, 60,  60)),
            ("Speed",        f"{int(player.speed)}",                  (100, 200, 255)),
            ("Damage",       f"{int(player.damage)}",                 (255, 160, 50)),
            ("Armor",        f"{int(player.armor)}%",                 (120, 180, 255)),
            ("Regen",        f"{player.hp_regen:.1f}/s",              (80,  220, 120)),
            ("Luck",         f"{int(player.lucky)}",                  (255, 230, 80)),
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
        sep = self.font_small.render("- ACTIVE SPELL -", True, (160, 180, 220))
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
            msg  = self.font_small.render("No runes yet.", True, COL_HINT)
            msg2 = self.font_small.render("Level up to earn runes!", True, COL_HINT)
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
                    more_surf = self.font_small.render(f"... and {more} more rune{'s' if more != 1 else ''}", True, COL_HINT)
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
        note = self.font_small.render("Basic shots always fire - main element is optional", True, (90, 90, 110))
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
        slot_labels = {0: "Main", 1: "L1", 2: "R1", 3: "L2", 4: "R2"}
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
        surf  = self.font_small.render(f"Current combo:  {desc}", True, (180, 200, 180))
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
            if self._handle_spell_button_click(mx, my, player):
                return False
            if any(rect.collidepoint(mx, my) for rect, _ in self.inventory_rects):
                self._handle_inventory_click(mx, my, player)
                return False
            # Ưu tiên click slot (canvas bên phải)
            if mx > INV_PANEL_W:
                self._handle_slot_click(mx, my, player)
            elif self.left_tab == TAB_INV:
                self._handle_inventory_click(mx, my, player)

        return False

    def _handle_tab_click(self, mx: int, my: int) -> bool:
        tabs = [(TAB_INV, "Inventory"), (TAB_STATS, "Stats")]
        for i, (tab_id, _) in enumerate(tabs):
            x = INV_X + i * (TAB_BTN_W + 8)
            rect = pygame.Rect(x, 36, TAB_BTN_W, TAB_BTN_H)
            if rect.collidepoint(mx, my):
                self.left_tab = tab_id
                return True
        return False

    def _handle_inventory_click(self, mx: int, my: int, player) -> None:
        inventory = player.rune_inventory
        if self.inventory_rects:
            for rect, idx in self.inventory_rects:
                if idx >= len(inventory):
                    continue
                if rect.collidepoint(mx, my):
                    if self.selected_inv_idx == idx:
                        self.selected_rune = None
                        self.selected_inv_idx = -1
                    else:
                        self.selected_rune = inventory[idx]
                        self.selected_inv_idx = idx
                    return

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
        if self.spell_button_rects:
            for i, rect in enumerate(self.spell_button_rects):
                if rect.collidepoint(mx, my):
                    player.rebuild_all_spells()
                    player.set_active_spell(i)
                    self.selected_rune = None
                    self.selected_inv_idx = -1
                    return True

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
                        self._show_status("Invalid! Place the parent slot first.")
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
                        self._show_status("This rune type does not match the slot!")
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
