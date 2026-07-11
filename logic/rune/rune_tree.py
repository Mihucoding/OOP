"""
RuneTree — Cây Rune kết hợp Elements + Modifiers cho 1 chiêu.

Chiêu luôn có Base Spell (đạn thường), nên RuneTree không cần Element để bắn.
Elements thêm hiệu ứng khi trúng; Modifiers thay đổi hành vi đạn.
"""
import math
from logic.rune.rune_component import RuneComponent, ElementRune, ModifierRune


class CastParams:
    """Tham số 1 'cast' trong đồ thị neo (Spell gốc hoặc 1 Trigger).

    damage_mult/speed_mult/size_mult: các con số CỘNG DỒN được (nhân giao
    hoán) — nhiều Modifier cùng gắn vào 1 cast thì cứ nhân dồn, thứ tự không
    quan trọng.

    batches: mỗi Modifier kiểu Frenetic Energy/Stars Aligned tự thêm ĐÚNG 1
    batch riêng của mình qua add_batch() — KHÔNG ghi đè lên nhau. Nhờ vậy khi
    2 rune cùng gắn vào 1 cast (VD Frenetic + Stars Aligned), phần 'Spawn
    Count' của MỖI rune vẫn giữ đúng đội hình riêng (cone toả ngẫu nhiên hay
    line dàn hàng), không bị rune còn lại "ghi đè" đội hình."""
    __slots__ = ('damage_mult', 'speed_mult', 'size_mult', 'batches',
                 'orbit', 'orbit_radius', 'orbit_duration', 'duration_mult')

    def __init__(self):
        self.damage_mult = 1.0
        self.speed_mult  = 1.0
        self.size_mult   = 1.0
        self.batches: list = []   # [(count:int, pattern:str, spread:float), ...]
        # Orbit movement (Self-Centered): các bản của cast này quay quanh tâm
        # (player nếu là Spell gốc, hoặc NGUỒN spawn nếu là Trigger — VD tia
        # kiếm Flash of Swords quay quanh boomerang đã spawn ra nó).
        self.orbit          = False
        self.orbit_radius   = 0.0
        self.orbit_duration = 0.0
        self.duration_mult  = 1.0   # nhân thời lượng bản spawn (Trigger dùng)

    @property
    def spawn_count(self) -> int:
        """Tổng số bản (1 bản gốc + tổng số bản mỗi batch đóng góp)."""
        return 1 + sum(count for count, _pattern, _spread in self.batches)

    def add_batch(self, count: int, pattern: str, spread: float) -> None:
        """pattern: 'cone' (toả ngẫu nhiên trong `spread` độ) | 'line' (dàn
        hàng vuông góc hướng bay, cách nhau `spread` px) | 'ring' (rải đều
        quanh 1 vòng tròn bán kính `spread` px quanh nguồn — dùng cho orbit)."""
        if count > 0:
            self.batches.append((count, pattern, spread))


class RuneTree:
    """
    Container chứa toàn bộ Rune của 1 viên đạn.
    - elements : list[ElementRune] — nhiều nguyên tố cùng hoạt động
    - modifiers: list[ModifierRune] — quỹ đạo / split / bounce
    - MAX_DEPTH = 3
    """

    MAX_DEPTH = 3

    def __init__(self):
        self.elements:  list[ElementRune]  = []
        self.modifiers: list[ModifierRune] = []

    # ── Backward-compat property ───────────────────────────────────────────────

    @property
    def element(self) -> ElementRune | None:
        """Element đầu tiên trong cây, giữ lại để tương thích code cũ."""
        return self.elements[0] if self.elements else None

    # ── Thiết lập Elements ────────────────────────────────────────────────────

    def set_element(self, elem: ElementRune) -> None:
        """Thay thế toàn bộ danh sách Element bằng 1 Element."""
        self.elements = [elem]

    def add_element(self, elem: ElementRune) -> None:
        """Thêm Element phụ vào danh sách."""
        self.elements.append(elem)

    # ── Thiết lập Modifiers ───────────────────────────────────────────────────

    def add_modifier(self, modifier: ModifierRune,
                     parent: ModifierRune = None,
                     depth: int = 1) -> bool:
        if depth > self.MAX_DEPTH:
            return False
        if parent is None:
            self.modifiers.append(modifier)
        else:
            parent.add_child(modifier)
        return True

    # ── Áp dụng cây ──────────────────────────────────────────────────────────

    def on_fire(self, bullet, context: dict) -> list:
        """Gọi khi đạn bắn. Trả về list đạn phụ (cast-graph rune tạo thêm)."""
        new_bullets: list = []
        for mod in self._fire_order(self.modifiers):
            self._traverse_fire(mod, bullet, context, new_bullets, depth=1)
        new_bullets.extend(self.resolve_and_fire_cast_graph(bullet, context))
        return new_bullets

    @staticmethod
    def _fire_order(nodes) -> list:
        """Sắp xếp các rune CÙNG CẤP theo ON_FIRE_PRIORITY (buff chạy trước
        spawner/trigger) — canonical hoá thứ tự on_fire để kết quả KHÔNG phụ
        thuộc thứ tự slot của rune anh em. sorted() ổn định nên rune cùng
        priority vẫn giữ nguyên thứ tự tương đối ban đầu."""
        return sorted(nodes, key=lambda n: getattr(n, 'ON_FIRE_PRIORITY', 100))

    # ── "Neo vào Trigger gần nhất, else Spell gốc" (Echoes of Mystralia) ────────
    #
    # Luật: mỗi Modifier/Trigger tự hỏi "tôi đang gắn vào cái gì?" — Trigger gần
    # nhất tính từ dưới lên (bỏ qua Modifier ở giữa), hoặc Spell gốc nếu không
    # có Trigger nào phía trên. Chỉ áp dụng cho rune CHỦ ĐỘNG khai báo tham gia
    # (contribute_cast / IS_CAST_GRAPH_TRIGGER) — rune cũ (HeavyHitter, Split,
    # RollingStone...) hoàn toàn không bị ảnh hưởng, vẫn chạy qua _traverse_fire
    # như trước giờ.

    def resolve_cast_graph(self):
        """Chỉ DUYỆT cây và tính CastParams (không thực thi gì cả) — dùng
        chung cho MỌI hệ, kể cả hệ không có Bullet object thật (Ice spike,
        Lightning beam). Trả về (root_params, trigger_params, trigger_reference,
        order) — xem resolve_trigger_firings() để tính lịch bắn Trigger từ đó."""
        root_params       = CastParams()
        trigger_params: dict = {}
        trigger_reference: dict = {}
        order: list = []
        for mod in self.modifiers:
            self._walk_cast_graph(mod, None, root_params, trigger_params,
                                  trigger_reference, order)
        return root_params, trigger_params, trigger_reference, order

    def resolve_trigger_firings(self, root_effective_damage: float, root_spawn_count: int,
                                trigger_params: dict, trigger_reference: dict, order: list) -> list:
        """Tính lịch bắn cho mọi Trigger tham gia cast graph — THUẦN TÍNH TOÁN,
        không tạo object gì. Trả về list (node, base_dmg, params) — mỗi phần
        tử là 1 LẦN node đó được kích hoạt (lặp theo spawn_count của Trigger
        tham chiếu); người gọi tự dùng params.batches (qua
        resolve_batch_positions) để tách đúng số lượng + đúng đội hình của
        TỪNG modifier gắn vào node đó (không trộn chung 1 đội hình).
        root_effective_damage/root_spawn_count: damage/số 'cast' của Spell gốc
        SAU khi đã áp root_params riêng của hệ đó (bullet.damage, hay damage
        gốc của spike/beam — mỗi hệ tự tính theo cách của mình)."""
        effective_damage = {None: root_effective_damage}
        total_instances  = {None: root_spawn_count}
        firings: list = []

        for node in order:
            ref     = trigger_reference[node]
            params  = trigger_params[node]
            percent = getattr(node, 'DAMAGE_PERCENT', 1.0)
            stack   = getattr(node, 'stack', 1)
            base_dmg = effective_damage[ref] * percent * stack * params.damage_mult
            effective_damage[node] = base_dmg

            times  = total_instances[ref]
            own_n  = params.spawn_count
            total_instances[node] = times * own_n

            for _ in range(times):
                firings.append((node, base_dmg, params))

        return firings

    def resolve_batch_positions(self, origin_x: float, origin_y: float, base_angle: float,
                                batches: list):
        """Trả về list (x, y, angle_jitter_deg) cho MỌI bản — bản đầu tiên
        luôn là bản GỐC (không lệch/không jitter), rồi tới từng batch theo
        ĐÚNG đội hình riêng của nó (không trộn lẫn dù nhiều rune cùng gắn vào
        1 cast, VD Frenetic toả cone + Stars Aligned dàn hàng cùng lúc)."""
        positions = [(origin_x, origin_y, 0.0)]
        for count, pattern, spread in batches:
            for i in range(count):
                positions.append(
                    self._resolve_spawn_position(origin_x, origin_y, base_angle, pattern, spread, i, count))
        return positions

    def _resolve_spawn_position(self, origin_x: float, origin_y: float, base_angle: float,
                                pattern: str, spread: float, index: int, total: int):
        """Trả về (x, y, angle_jitter_deg) cho bản thứ `index` trong tổng
        `total` bản của 1 batch:
        - 'cone': cùng 1 điểm (origin), góc bay toả ngẫu nhiên trong `spread` độ.
        - 'line': dàn hàng vuông góc `base_angle`, cách nhau `spread` px,
          cùng hướng (angle_jitter_deg = 0)."""
        if pattern == 'line' and total > 1:
            spacing  = spread if spread > 0 else 30.0
            centered = index - (total - 1) / 2.0
            perp = base_angle + math.pi / 2
            x = origin_x + math.cos(perp) * spacing * centered
            y = origin_y + math.sin(perp) * spacing * centered
            return x, y, 0.0
        if pattern == 'ring':
            # Rải đều quanh vòng tròn quanh nguồn — điểm bắt đầu quỹ đạo orbit.
            radius = spread if spread > 0 else 60.0
            ang = base_angle + 2 * math.pi * (index + 1) / (total + 1)
            x = origin_x + math.cos(ang) * radius
            y = origin_y + math.sin(ang) * radius
            return x, y, 0.0
        jitter = spread if spread > 0 else 20.0
        return origin_x, origin_y, jitter

    def resolve_and_fire_cast_graph(self, bullet, context) -> list:
        """Bản thực thi trên Bullet object thật (Fire/Wind) — dùng
        resolve_cast_graph()/resolve_trigger_firings() ở trên làm lõi tính toán."""
        root_params, trigger_params, trigger_reference, order = self.resolve_cast_graph()

        if (not order and not root_params.batches and root_params.damage_mult == 1.0
                and root_params.speed_mult == 1.0 and root_params.size_mult == 1.0
                and not root_params.orbit):
            return []   # không rune nào tham gia đồ thị — bỏ qua

        extra_bullets: list = []

        bullet.damage *= root_params.damage_mult
        bullet.vx     *= root_params.speed_mult
        bullet.vy     *= root_params.speed_mult
        bullet.radius *= root_params.size_mult

        base_angle = math.atan2(bullet.vy, bullet.vx)
        root_positions = self.resolve_batch_positions(bullet.x, bullet.y, base_angle, root_params.batches)
        root_spawns = [bullet]
        for x, y, jitter_deg in root_positions[1:]:   # [0] la ban goc (chinh bullet), khong tao them
            copy = self._spawn_copy_at(bullet, x, y, base_angle, jitter_deg)
            root_spawns.append(copy)
            extra_bullets.append(copy)

        # Self-Centered gắn vào Spell gốc → mọi bản của Spell quay quanh player.
        if root_params.orbit:
            for i, spawn in enumerate(root_spawns):
                self._start_orbit(spawn, root_params, base_angle, i, len(root_spawns))

        firings = self.resolve_trigger_firings(
            bullet.damage, root_params.spawn_count, trigger_params, trigger_reference, order)
        for node, base_dmg, params in firings:
            batches = self._orbit_even_batches(node, params.batches)
            positions = self.resolve_batch_positions(bullet.x, bullet.y, base_angle, batches)
            for tx, ty, jitter_deg in positions:
                spawned = node.trigger_once(
                    tx, ty, base_dmg, context,
                    dir_x=bullet.vx, dir_y=bullet.vy,
                    angle_jitter_deg=jitter_deg,
                    speed_mult=params.speed_mult,
                    size_mult=params.size_mult,
                    duration_mult=params.duration_mult,
                    source=bullet,
                )
                if spawned is not None:
                    extra_bullets.append(spawned)

        return extra_bullets

    @staticmethod
    def _orbit_even_batches(node, batches):
        """Trigger quay orbit (Flash of Swords, ORBIT_EVEN_SPACING=True) → đổi
        MỌI batch (line/cone/ring) thành 'ring' để các bản rải ĐỀU quanh vòng.
        Lưỡi kiếm quay quanh nguồn nên đội hình thẳng/cone sẽ ra góc lệch không
        đều; ring cho khoảng cách góc đều nhau. Trigger thường không có cờ này
        thì giữ nguyên batch."""
        if not getattr(node, 'ORBIT_EVEN_SPACING', False):
            return batches
        r = getattr(node, 'ORBIT_RADIUS', 60.0)
        return [(count, 'ring', r) for count, _pattern, _spread in batches]

    def _start_orbit(self, bullet, cast_params, base_angle: float, index: int, total: int) -> None:
        """Bật orbit cho 1 bản spawn: quay quanh tâm (player_x/player_y, do
        game_loop đồng bộ), bán kính/thời lượng lấy từ cast_params. Bỏ qua đạn
        có quỹ đạo riêng không hợp orbit (VD WindBoomerang: CAN_ORBIT=False) —
        vẫn nhận Spawn Count/Duration nhưng KHÔNG bị ép quay."""
        if not getattr(bullet, 'CAN_ORBIT', True):
            return
        bullet._orbit        = True
        bullet._orbit_radius = cast_params.orbit_radius
        bullet._orbit_angle  = base_angle + 2 * math.pi * index / max(1, total)
        # PHẢI khởi tạo player_x/player_y ở đây: game_loop chỉ đồng bộ tâm quay
        # về player khi bullet ĐÃ có sẵn 2 field này (điều kiện hasattr). Không
        # set → orbit_steer lấy nhầm tâm = chính vị trí đạn (đang chạy) → đạn
        # văng ra xa cực nhanh. Giá trị đầu = vị trí spawn (≈ player), frame sau
        # game_loop ghi đè bằng player.x/player.y thật.
        bullet.player_x = bullet.x
        bullet.player_y = bullet.y
        if cast_params.orbit_duration > 0:
            bullet.LIFETIME = cast_params.orbit_duration
            bullet.elapsed  = 0.0

    def _walk_cast_graph(self, node, current_ref, root_params,
                         trigger_params, trigger_reference, order):
        if getattr(node, 'IS_CAST_GRAPH_TRIGGER', False):
            trigger_params[node]    = CastParams()
            trigger_reference[node] = current_ref
            order.append(node)
            next_ref = node
        else:
            target = trigger_params[current_ref] if current_ref is not None else root_params
            if hasattr(node, 'contribute_cast'):
                node.contribute_cast(target)
            next_ref = current_ref
        for child in node.get_children():
            self._walk_cast_graph(child, next_ref, root_params,
                                  trigger_params, trigger_reference, order)

    def _spawn_copy_at(self, bullet, x: float, y: float, base_angle: float, jitter_deg: float):
        """Tạo 1 bản sao CÙNG LOẠI với bullet gốc (Bullet hoặc WindBoomerang...)
        tại (x, y) — dùng cho phần 'Spawn Count' của rune kiểu Frenetic
        Energy/Stars Aligned. Nhân bản đúng class để giữ hành vi riêng (VD
        WindBoomerang vẫn có quỹ đạo ra/về, không biến thành Bullet thẳng)."""
        import random
        angle = base_angle
        if jitter_deg > 0:
            angle += math.radians(random.uniform(-jitter_deg / 2, jitter_deg / 2))
        speed = math.hypot(bullet.vx, bullet.vy)
        cls = type(bullet)
        b = cls(x, y, x + math.cos(angle) * 100, y + math.sin(angle) * 100,
               bullet.damage, bullet.rune_tree)
        b.vx, b.vy          = math.cos(angle) * speed, math.sin(angle) * speed
        b.radius             = bullet.radius
        b.pierce_remaining   = getattr(bullet, 'pierce_remaining', 0)
        b.element_stack      = bullet.element_stack
        return b

    def on_update(self, bullet, dt: float, context: dict = None) -> None:
        """Gọi mỗi frame để cập nhật quỹ đạo đạn.
        context (tùy chọn) cho modifier tự sinh thêm đạn ngay trong on_update
        (VD: FuriousOutburstModifier nổ thêm cầu lửa theo quãng đường đã bay)."""
        for mod in self.modifiers:
            self._traverse_update(mod, bullet, dt, context, depth=1)

    def on_hit(self, bullet, enemy, context: dict) -> None:
        """
        Gọi khi đạn trúng quái.
        Áp dụng TẤT CẢ Elements (mỗi cái dùng element_stack của riêng nó),
        sau đó áp dụng Modifiers.
        """
        original_stack = bullet.element_stack
        for elem in self.elements:
            # Tạm đặt element_stack theo từng element (hỗ trợ stacking riêng)
            bullet.element_stack = getattr(elem, 'element_stack', 1)
            elem.on_hit(bullet, enemy, context)
        bullet.element_stack = original_stack  # phục hồi

        for mod in self.modifiers:
            self._traverse_hit(mod, bullet, enemy, context, depth=1)

    # ── Duyệt cây đệ quy ─────────────────────────────────────────────────────

    def _traverse_fire(self, node, bullet, context, result, depth):
        if depth > self.MAX_DEPTH:
            return
        new = node.on_fire(bullet, context) or []
        if new:
            result.extend(new)
        children = self._fire_order(node.get_children())
        for child in children:
            self._traverse_fire(child, bullet, context, result, depth + 1)
        # Rune con phải áp tiếp lên CÁC VIÊN MỚI do node này sinh ra (VD: Split) —
        # nếu không, buff đặt dưới Split trong cây chỉ tác động viên gốc, bỏ sót
        # toàn bộ viên tách dù chúng đứng "sau" buff trong luồng cây.
        for spawned in new:
            for child in children:
                self._traverse_fire(child, spawned, context, result, depth + 1)

    def _traverse_update(self, node, bullet, dt, context, depth):
        if depth > self.MAX_DEPTH:
            return
        node.on_update(bullet, dt, context)
        for child in node.get_children():
            self._traverse_update(child, bullet, dt, context, depth + 1)

    def _traverse_hit(self, node, bullet, enemy, context, depth):
        if depth > self.MAX_DEPTH:
            return
        node.on_hit(bullet, enemy, context)
        for child in node.get_children():
            self._traverse_hit(child, bullet, enemy, context, depth + 1)

    # ── Tiện ích ─────────────────────────────────────────────────────────────

    def get_all_runes(self) -> list:
        """Trả về toàn bộ Rune trong cây (dùng cho HUD / Builder)."""
        runes = list(self.elements)
        for mod in self.modifiers:
            self._collect(mod, runes)
        return runes

    def _collect(self, node: RuneComponent, out: list):
        out.append(node)
        for child in node.get_children():
            self._collect(child, out)

    def is_ready(self) -> bool:
        """Base Spell luôn bắn được, kể cả khi chưa gắn rune."""
        return True

    def get_visual_type(self) -> str:
        if not self.elements:
            return 'circle'
        from logic.rune.elements.fire_rune import FireRune
        from logic.rune.elements.ice_rune import IceRune
        from logic.rune.elements.lightning_rune import LightningRune
        from logic.rune.elements.wind_rune import WindRune

        elem = self.elements[0]
        if isinstance(elem, FireRune):
            return 'fire_bolt'
        if isinstance(elem, WindRune):
            return 'wind_boomerang'
        if isinstance(elem, LightningRune):
            return 'lightning_beam'
        if isinstance(elem, IceRune):
            return 'ice_eruption'
        return 'circle'

    def describe(self) -> str:
        """Mô tả ngắn gọn (dùng cho debug và Builder hint)."""
        elem_str = " | ".join(
            f"[{e.get_display_name()}]" for e in self.elements)
        mod_str  = " ".join(
            f"->{m.get_display_name()}" for m in self.modifiers)
        parts = [p for p in (elem_str, mod_str) if p]
        return " ".join(parts) if parts else "Basic shot"
