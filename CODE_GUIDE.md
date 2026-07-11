# CODE_GUIDE — Giải thích cấu trúc, tiến trình & cách vận hành game

> **Rune Craft Roguelike** · Python 3.11+ · Pygame-CE · 1280×720
> Tài liệu này giải thích **code chạy như thế nào, theo đúng thứ tự thực thi**, và đi sâu vào **cơ chế ghép Rune** (Composite Pattern) — thứ khiến mọi thao tác trong game hoạt động được.
> Viết cho người mới đọc code lần đầu — mỗi phần đều có ví dụ cụ thể, không chỉ liệt kê tên hàm.

---

## Mục lục

1. [Hai nguyên tắc kiến trúc bất biến](#1-hai-nguyên-tắc-kiến-trúc-bất-biến)
2. [Tiến trình dự án — đã làm gì, tới đâu](#2-tiến-trình-dự-án--đã-làm-gì-tới-đâu)
3. [Tiến trình chạy game — từ lúc bấm Run đến khi thoát](#3-tiến-trình-chạy-game--từ-lúc-bấm-run-đến-khi-thoát)
4. [Cây thư mục (bản đồ code)](#4-cây-thư-mục-bản-đồ-code)
5. [★ Cơ chế ghép Rune — Composite Pattern (giải thích kỹ)](#5--cơ-chế-ghép-rune--composite-pattern-giải-thích-kỹ)
6. [Bảng tra cứu: thao tác → cơ chế → file](#6-bảng-tra-cứu-thao-tác--cơ-chế--file)
7. [Các hệ thống phụ](#7-các-hệ-thống-phụ)
8. [Muốn mở rộng game?](#8-muốn-mở-rộng-game)
9. [★★ Sổ tay sửa/update — muốn đổi cái này thì sửa ở đâu](#9--sổ-tay-sửaupdate--muốn-đổi-cái-này-thì-sửa-ở-đâu)

---

## 1. Hai nguyên tắc kiến trúc bất biến

1. **`logic/` KHÔNG import `pygame` hay bất cứ gì từ `ui/`.**
   Nghĩa là toàn bộ *luật chơi* (đạn bay thế nào, rune ảnh hưởng ra sao, quái có bao nhiêu HP...) được viết bằng Python thuần túy, không dính tới việc vẽ hình. Nhờ vậy có thể viết `tests/test_rune_builds.py` để kiểm tra logic mà **không cần mở cửa sổ game**.
2. **`ui/` được phép import `logic/`.**
   Tầng UI (Pygame) chỉ có nhiệm vụ: đọc trạng thái từ `logic/`, vẽ nó lên màn hình, và khi người chơi bấm phím/chuột thì gọi hàm bên `logic/` để thay đổi trạng thái.

```
┌─────────────┐   đọc trạng thái để vẽ   ┌─────────────┐
│    ui/      │ ───────────────────────► │   logic/    │
│  (pygame,   │                          │ (thuần Python,│
│  vẽ + input)│ ◄─────────────────────── │  không pygame)│
└─────────────┘   gọi hàm để thay đổi     └─────────────┘
```

Ví dụ cụ thể: khi bạn bấm chuột trái để bắn, `ui/game_loop.py` gọi `logic/entities/bullet.py` để tạo viên đạn — nhưng bản thân `Bullet` không biết gì về Pygame, nó chỉ có tọa độ `x, y` và vận tốc `vx, vy` (số thực). `ui/renderer.py` mới là nơi lấy `bullet.x, bullet.y` và vẽ hình ảnh lên màn hình.

---

## 2. Tiến trình dự án — đã làm gì, tới đâu

Đây là dòng thời gian phát triển thực tế — không phải cách game chạy, mà là **quá trình đội đã xây nó lên** và **hiện đang đứng ở đâu**.

### 2.1. Nền móng ban đầu (trước phiên làm việc gần nhất)

Toàn bộ hệ thống lõi đã hoàn chỉnh và có test:

- Composite Pattern cho Rune (`RuneComponent` → `ElementRune`/`ModifierRune`), `RuneTree`, `RuneSlots`.
- 4 Element (Fire/Ice/Lightning/Wind) + `BloodRune`/`PoisonRune` (2 rune này về sau **bị loại khỏi pool**, xem 2.2).
- 4 Modifier (Spiral/Bounce/Split/Haste).
- Player với 3 `SpellBuild` (sau giảm còn 2), 8 chỉ số, Ultimate theo hệ, Dash.
- Wave/Boss, Leveling (Rune + StatUpgrade 5 bậc hiếm), XP orb, HUD, các màn Menu/LevelUp/GameOver/Win.
- 32+ unit test (`tests/test_rune_builds.py`, `tests/test_input_handler.py`...).

### 2.2. Phiên làm việc gần nhất — theo đúng thứ tự đã thực hiện

1. **Chỉnh Wind:** bỏ knockback (chỉ còn slow), tăng tốc xoay của `WindBoomerang` (480→960 độ/giây), thêm hiệu ứng glow quanh boomerang để phân biệt với nền.
2. **Bỏ `BloodRune` khỏi game:** xóa khỏi `level_manager.ALL_RUNES`, `rune_tree.get_visual_type()`, `renderer` sprite map, và mọi UI liên quan.
3. **Thêm màn chọn nguyên tố đầu ván** (`element_select_screen.py`, bản tự viết ban đầu): chọn 2/4 hệ, gán thẳng vào slot 0 của 2 `SpellBuild` (không qua inventory) — đồng thời **giảm từ 3 chiêu xuống 2 chiêu**.
4. **Redesign Rune Builder lần 1** (theo ảnh tham khảo *Echoes of Mystralia*): top nav kiểu `[1] RESOURCES ● WATCHER'S HEART ● RELICS [2]`, thanh kho ngang 5 slot chứa modifier phía trên cây, panel bên phải hiện thông tin modifier khi chọn.
5. **Kiểm tra tương thích rune ↔ nguyên tố:** phát hiện `Bounce` gây **crash** khi gắn vào Wind (boomerang thiếu `bounce_count`), và vô tác dụng trên Lightning/Ice. Thêm cơ chế `ElementRune.FORBIDDEN_MODIFIERS` + `accepts_modifier()` để mỗi hệ tự khai báo bổ trợ bị cấm. Đồng thời làm cho **Spiral/Split thật sự chạy được trên Wind** (trước đó boomerang bỏ qua `on_update`/`on_fire`).
6. **Merge lấy nhánh `dev-new`** (một bản redesign song song do đồng đội làm, cùng repo GitHub `Mihucoding/OOP`): sau khi cân nhắc 2 bản không tương thích, quyết định **lấy phần rune tree/skill-select/assets của `dev-new`** (layout cây riêng từng hệ qua `slot_defs_for_rune`, khóa cứng lõi qua `set_core`, ảnh artwork element thật, `rune_ui_config.py`) và **port lại các fix gameplay của phiên làm việc trước đó** lên trên nền mới (fix Bounce, Wind Spiral/Split, sửa VFX băng bị cắt cụt ở đầu mút).
7. **Tách riêng thanh kho 5-slot modifier khỏi rune tree của `dev-new`:** dev-new vốn chỉ có dải 8 orb nhỏ; đưa lại thanh kho `─○─○─○─○─○─` kiểu cũ, đặt canh giữa **ngay phía trên** cây rune (giữa bộ chọn chiêu và crest lõi), có chế độ cuộn khi bật cheat và nhiều hơn 5 modifier.
8. **Sửa logic ghép rune trong Builder theo 2 yêu cầu:**
   - Bỏ yêu cầu "phải có node cha mới đặt được node con" — modifier đặt vào node rời **tự nối lên tổ tiên gần nhất có rune** (`RuneSlots.effective_parent()`), có vẽ đường nét đứt minh họa.
   - Thêm **chuột phải để gỡ rune về kho** ở bất kỳ node nào (trừ lõi khóa), hoạt động ngay cả khi đang cầm 1 rune khác trong tay.
9. **Sửa lỗi VFX băng bị cắt ở đầu mút** (`renderer._tile_ice_spike_frames`): thêm vùng đệm cuối canvas để frame animation cuối cùng vẽ trọn vẹn thay vì bị cắt phẳng.
10. Viết tài liệu `CODE_GUIDE.md` (file này).

### 2.3. Trạng thái hiện tại (tính tới thời điểm viết tài liệu)

**Đã hoàn chỉnh và chạy được:**
- 4 nguyên tố + 4 bổ trợ, đủ luật tương thích (cấm Bounce đúng chỗ, auto-connect node rời).
- 2 chiêu độc lập, đổi bằng Q/E, mỗi chiêu 1 cây rune riêng theo layout của hệ.
- Rune Builder "Watcher's Heart" hoàn chỉnh: cây hex theo hệ + kho 5 slot + gỡ bằng chuột phải.
- Toàn bộ vòng chơi Menu → Skill Select → Playing → Level Up/Rune Builder → Game Over/Win.

**Đã biết nhưng CHƯA xử lý / lưu ý khi đọc code:**
- `PoisonRune` (`elements/poison_rune.py`) và `BloodRune` (`elements/blood_rune.py`) **có file nhưng KHÔNG nằm trong `ALL_RUNES`** — tồn tại trong code nhưng không xuất hiện khi chơi thật. Nếu thấy import các file này ở đâu đó cũ, đó là tàn dư trước khi bỏ.
- 1 test có sẵn `tests/test_input_handler.py::test_get_mouse_world_pos` đang **fail từ trước khi có phiên làm việc này**, không liên quan tới cơ chế rune — không phải lỗi mới.
- Nhánh Git `backup/pre-devnew-runetree` giữ bản UI rune builder **tự viết tay** (trước khi merge `dev-new`) — chỉ để tham khảo/khôi phục nếu cần, không phải nhánh đang code chính (`master`).

---

## 3. Tiến trình chạy game — từ lúc bấm Run đến khi thoát

Phần này mô tả **chính xác thứ tự các dòng code chạy**, từ file `main.py` cho tới khi thoát game. Đọc phần này trước sẽ giúp hiểu các phần sau dễ hơn nhiều.

### Bước 0 — Khởi động (`main.py`)

```python
from ui.game_loop import GameLoop

if __name__ == "__main__":
    game = GameLoop()   # (a) khởi tạo mọi thứ 1 lần
    game.run()          # (b) vòng lặp chạy mãi cho tới khi thoát
```

Chỉ 2 dòng — toàn bộ độ phức tạp nằm trong class `GameLoop` ở `ui/game_loop.py`.

### Bước 1 — `GameLoop.__init__` chạy 1 lần duy nhất

```python
def __init__(self):
    pygame.init()
    self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))   # mở cửa sổ
    self.renderer    = Renderer(self.game_surface)                # bộ vẽ world
    self.hud         = HUD(...)                                   # bộ vẽ thanh máu/chiêu
    self.input       = InputHandler()                             # đọc bàn phím/chuột
    self.menu        = MainMenu(...)
    self.builder     = RuneBuilderScreen(...)                     # màn lắp rune
    self.skill_select = SkillSelectScreen(...)                    # màn chọn 2 hệ
    ...
    self.state = self.STATE_MENU        # (★) bắt đầu ở màn Menu
    self._init_game_objects()           # tạo Player + list rỗng cho enemies/bullets...
```

Điều quan trọng nhất ở đây: **`self.state`** — một biến string quyết định game đang ở màn nào. Đây chính là kỹ thuật **state machine** (máy trạng thái). Toàn bộ game chỉ xoay quanh biến này:

```python
STATE_MENU           = 'menu'          # màn hình chính
STATE_ELEMENT_SELECT = 'skill_select'  # chọn 2 nguyên tố
STATE_PLAYING        = 'playing'       # đang chơi
STATE_LEVEL_UP       = 'level_up'      # màn chọn thẻ lên cấp (game vẫn vẽ nền phía sau)
STATE_RUNE_BUILDER   = 'rune_builder'  # màn lắp rune (Tab)
STATE_GAME_OVER      = 'game_over'
STATE_WIN            = 'win'
```

### Bước 2 — Vòng lặp chính (`run`) — chạy 60 lần/giây

```python
def run(self) -> None:
    running = True
    while running:                                  # lặp vô hạn cho tới khi thoát
        self._dt = self.clock.tick(FPS) / 1000.0     # (1) đo thời gian giữa 2 frame (giây)
        for event in pygame.event.get():             # (2) đọc mọi sự kiện (phím, chuột...)
            result = self._handle_event(event)       #     xử lý sự kiện tùy theo state
            if result == 'quit': running = False
        self._update(self._dt)                       # (3) cập nhật toàn bộ logic 1 bước
        self._draw()                                 # (4) vẽ lại toàn màn hình
        pygame.display.flip()                        # (5) hiện hình vừa vẽ lên cửa sổ
```

Đây là **vòng lặp game (game loop)** kinh điển: mỗi khung hình (frame) làm đúng 5 việc theo thứ tự — đo thời gian, xử lý input, cập nhật logic, vẽ, hiện hình. `dt` (delta time) là số giây đã trôi qua kể từ frame trước — mọi chuyển động trong game đều nhân với `dt` để tốc độ không phụ thuộc FPS máy (VD: `bullet.x += vx * dt`).

### Bước 3 — Hành trình 1 ván chơi, đúng theo state

```
MENU
  │  bấm "Start" → menu.handle_event() trả 'start'
  ▼
SKILL_SELECT (skill_select_screen.py)
  │  người chơi click chọn 2 hex nguyên tố → confirm
  │  game_loop:
  │     runes = [rune_cfg.make_element_rune(k) for k in đã_chọn]
  │     self.player.setup_spells(runes)   # ★ tạo 2 SpellBuild, mỗi cái 1 cây rune
  ▼
PLAYING (đây là state chiếm hầu hết thời gian chơi)
  │  mỗi frame: _update() làm 14 bước (di chuyển, bắn, update quái, va chạm,
  │             nhặt XP, spawn wave, dọn dẹp, kiểm tra thắng/thua...)
  │
  ├─ bấm Tab  ──────────────► RUNE_BUILDER (builder.draw() vẽ đè, game tạm dừng)
  │                                 │ bấm Tab/Esc lần nữa → builder._close() rebuild cây → PLAYING
  │
  ├─ nhặt đủ XP để lên cấp ─► LEVEL_UP (vẫn vẽ nền PLAYING phía sau, hiện card chọn)
  │                                 │ chọn xong → level_mgr.apply_choice() → PLAYING
  │
  ├─ HP player = 0  ────────► GAME_OVER
  │                                 │ bấm Restart → về SKILL_SELECT (ván mới)
  │
  └─ Boss chết      ────────► WIN
                                    │ bấm Restart → về SKILL_SELECT
```

Toàn bộ nhánh rẽ này nằm trong `_handle_event()` (khi có input) và cuối `_update()` (khi kiểm tra điều kiện thắng/thua):

```python
# cuối _update(), sau khi tính toán mọi thứ trong frame:
if not self.player.alive:
    self.state = self.STATE_GAME_OVER
if self.boss and not self.boss.alive:
    self.state = self.STATE_WIN
```

### Bước 4 — Bên trong 1 frame lúc đang `PLAYING` (`_update`, 14 bước)

Đây là hàm quan trọng nhất game — nó chạy **60 lần mỗi giây**, làm theo đúng thứ tự sau (số thứ tự khớp comment trong code `game_loop.py`):

| # | Việc làm | Ý nghĩa |
|---|---|---|
| 1 | Di chuyển player, cập nhật camera | Đọc phím WASD từ `input`, gọi `player.update()`, camera đuổi theo player |
| 2 | **Bắn đạn theo hệ đang chọn** | Xem chi tiết bên dưới — đây là chỗ cơ chế Rune "vào cuộc" |
| 3 | Update enemy + boss | Mỗi quái tự đuổi theo player (`enemy.update(dt, player.x, player.y)`) |
| 4 | RangedEnemy bắn đạn | Quái tầm xa tạo `EnemyBullet` bay về player |
| 5 | Update tất cả đạn | Gọi `bullet.update(dt)` cho từng viên — đây là lúc `RuneTree.on_update` chạy (Spiral xoay đạn) |
| 6 | Va chạm đạn ↔ quái | `_handle_bullet_collisions()` — đây là lúc `RuneTree.on_hit` chạy (Fire gắn burn, Bounce đổi hướng...) |
| 7 | Va chạm đạn quái ↔ player | Trừ máu player nếu bị bắn trúng |
| 8 | Quái chạm player | Trừ máu theo sát thương tiếp xúc |
| 9 | Boss AoE | Nếu boss đang bật vùng damage diện rộng |
| 10 | XP orb | Cập nhật hiệu ứng hút, nếu nhặt đủ → gọi `player.add_xp()`, nếu lên cấp → chuyển state `LEVEL_UP` |
| 11 | Wave manager | `wave_mgr.update()` quyết định có spawn quái/boss mới không |
| 12 | Hiệu ứng hình ảnh | Đếm giờ cho các flash/particle |
| 13 | `_cleanup()` | Xóa khỏi list mọi thứ đã chết/hết hạn (`bullet.alive == False`...) |
| 14 | Kiểm tra thắng/thua | Như đã nói ở Bước 3 |

**Bước 2 — chỗ "cơ chế ghép rune" thật sự chạy mỗi frame:**

```python
spell = self.player.get_active_spell()              # chiêu đang chọn (Q/E để đổi)
visual_type = spell.rune_tree.get_visual_type()     # 'fire_bolt' | 'ice_eruption' | ...

if firing:
    if self._get_lightning_rune(spell):
        self._channel_lightning_attack(...)         # Lightning: beam tức thời + chain
    elif self.player.can_fire():                    # còn giới hạn bởi cooldown chiêu
        if visual_type == 'wind_boomerang':
            self._spawn_wind_boomerang(...)          # Wind: đạn boomerang
        else:
            self._spawn_bullet(...)                  # Fire (và mọi hệ dùng đạn thường)
```

Chú ý: **Ice** không nằm trong nhánh `firing` này — nó xử lý riêng ở `_update_ice_charge()` (được gọi sớm hơn trong `_update`) vì cơ chế "giữ chuột để sạc" khác hẳn kiểu bắn tức thời. Cả 4 hệ **đều đọc modifier (Spiral/Split) từ cùng một `RuneTree`** dù đường xử lý khác nhau — đây là phần 5 sẽ giải thích kỹ.

### Bước 5 — Vẽ (`_draw`)

```python
def _draw(self) -> None:
    if self.state == self.STATE_MENU: self.menu.draw()
    elif self.state == self.STATE_ELEMENT_SELECT: self.skill_select.draw(self._dt)
    elif self.state in (PLAYING, LEVEL_UP):
        self.renderer.draw_all(player, enemies, boss, bullets, ...)   # vẽ world
        self.hud.draw(player, wave_info)                              # vẽ UI đè lên
        if self.state == LEVEL_UP: self.levelup_scr.draw(...)         # vẽ card đè tiếp
    elif self.state == STATE_RUNE_BUILDER: self.builder.draw(player, self._dt)
    elif self.state == STATE_GAME_OVER: self.gameover.draw(...)
    elif self.state == STATE_WIN: self.win_scr.draw(...)
```

`_draw()` **không thay đổi trạng thái game** — nó chỉ đọc (`player.hp`, `bullet.x`...) và vẽ. Toàn bộ thay đổi trạng thái nằm ở `_update()` và `_handle_event()`.

---

## 4. Cây thư mục (bản đồ code)

```
logic/
├── rune/                      ★ TRÁI TIM CỦA GAME (phần 5 giải thích kỹ)
│   ├── rune_component.py       # Lớp gốc: RuneComponent / ElementRune / ModifierRune
│   ├── rune_tree.py             # RuneTree — ghép element + modifier, duyệt cây
│   ├── rune_slots.py           # RuneSlots — bàn slot của builder → sinh ra RuneTree
│   ├── elements/                # Mỗi hệ 1 file: fire / ice / lightning / wind
│   └── modifiers/                # Mỗi bổ trợ 1 file: spiral / split / bounce / haste
├── entities/
│   ├── bullet.py                 # Đạn thường — GIỮ 1 RuneTree, mỗi sự kiện gọi tree
│   ├── wind_boomerang.py        # Đạn gió (dạng boomerang riêng, không kế thừa Bullet)
│   ├── player.py                 # Player + SpellBuild (mỗi chiêu 1 cây rune riêng)
│   ├── enemy.py / boss.py / ranged_enemy.py / fast_enemy.py / tank_enemy.py
│   └── status_effect.py          # burn / chill / slow / stun / poison
├── abilities/                    # Ultimate (theo hệ) + Dash + đòn đặc biệt lightning/ice
├── leveling/                     # level_manager (sinh 3 thẻ) + stat_upgrade (5 bậc hiếm)
└── wave/                         # wave_manager (spawn quái theo thời gian, boss)

ui/
├── game_loop.py                  # State machine + vòng lặp + điều phối bắn theo hệ
├── renderer.py                    # Vẽ world + hiệu ứng (fire/ice/lightning/wind VFX)
├── rune_ui_config.py              # Cấu hình layout cây rune từng hệ + ảnh element
├── hud.py                         # Thanh máu, thanh chiêu, cooldown
├── input_handler.py               # Đọc phím WASD + vị trí chuột trong world
└── screens/
    ├── main_menu.py
    ├── skill_select_screen.py     # Chọn 2 hệ đầu ván
    ├── rune_builder_screen.py     # Màn "Watcher's Heart" — lắp rune
    ├── level_up_screen.py
    ├── game_over_screen.py
    └── win_screen.py
```

---

## 5. ★ Cơ chế ghép Rune — Composite Pattern (giải thích kỹ)

### 4.0. Vấn đề cần giải quyết là gì?

Có **4 nguyên tố** (Fire/Ice/Lightning/Wind) và **4 bổ trợ** (Spiral/Split/Bounce/Haste). Nếu ghép mọi tổ hợp có thể xảy ra bằng cách viết class riêng cho từng combo (`FireSpiralBullet`, `FireSplitBullet`, `IceSpiralBullet`...) thì cần tới hàng chục class, và mỗi lần thêm 1 rune mới phải sửa lại rất nhiều chỗ. Đó là thiết kế tồi.

**Composite Pattern** giải quyết bằng cách: mỗi rune là **1 class nhỏ, độc lập**, và viên đạn **không cần biết** nó đang mang rune gì — nó chỉ gọi 3 "cái móc" chung (`on_fire`, `on_update`, `on_hit`) và để từng rune tự làm việc của mình.

### 4.1. Lớp gốc — `rune_component.py`

```python
from abc import ABC, abstractmethod

class RuneComponent(ABC):
    """Lớp trừu tượng (abstract class) — KHÔNG thể tạo instance trực tiếp.
    Mọi rune trong game đều PHẢI kế thừa từ đây."""

    @abstractmethod
    def on_hit(self, bullet, enemy, context): ...   # bắt buộc override: khi đạn trúng quái
    @abstractmethod
    def on_update(self, bullet, dt): ...            # bắt buộc override: mỗi frame (đổi quỹ đạo)
    @abstractmethod
    def on_fire(self, bullet, context) -> list: ...  # bắt buộc override: khi bắn (đẻ đạn phụ)

    def get_children(self) -> list:
        return []    # mặc định không có con — ElementRune giữ nguyên mặc định này
```

**Giải thích thuật ngữ cho người mới:**
- **`ABC` + `@abstractmethod`**: đây là cách Python bắt buộc "mọi lớp con phải tự viết lại (override) các hàm này". Nếu bạn tạo 1 class kế thừa `RuneComponent` mà quên viết `on_hit`, Python sẽ báo lỗi ngay khi bạn cố tạo instance — giúp tránh quên code.
- **Kế thừa (inheritance)**: `ElementRune(RuneComponent)` nghĩa là `ElementRune` "là một loại" `RuneComponent`, tự động có sẵn mọi thứ của cha, chỉ cần viết thêm/ghi đè phần khác biệt.
- **Đa hình (polymorphism)**: nhờ tất cả rune đều có chung 3 hàm `on_hit/on_update/on_fire`, đoạn code gọi `rune.on_hit(...)` **không cần quan tâm** `rune` là `FireRune` hay `SpiralModifier` — Python tự động chạy đúng phiên bản của từng class. Đây là lý do `Bullet` không cần `if rune is FireRune: ... elif rune is IceRune: ...` — chỉ cần gọi thẳng.

Hai lớp con:

```python
class ElementRune(RuneComponent):
    """LEAF (lá) trong cây — không có con, không đổi quỹ đạo, không đẻ đạn.
    Chỉ định nghĩa on_hit (hiệu ứng khi trúng: burn/chill/slow/dmg)."""
    FORBIDDEN_MODIFIERS: tuple = ()     # tên các Modifier bị cấm gắn cùng hệ này

    def accepts_modifier(self, modifier) -> bool:
        return type(modifier).__name__ not in self.FORBIDDEN_MODIFIERS

    def on_update(self, bullet, dt): pass       # element không làm gì mỗi frame
    def on_fire(self, bullet, context): return []  # element không đẻ thêm đạn
    def get_children(self): return []            # lá cây — không có con


class ModifierRune(RuneComponent):
    """COMPOSITE (nút hợp thành) — CÓ THỂ chứa modifier con (_children).
    Định nghĩa on_update / on_fire / on_hit tùy loại (Spiral chỉ có on_update, Split chỉ có on_fire...)."""
    def __init__(self):
        self._children: list[RuneComponent] = []

    def on_hit(self, bullet, enemy, context): pass   # mặc định không làm gì, Bounce sẽ override
    def add_child(self, rune): self._children.append(rune)
    def get_children(self): return self._children
```

> **Vì sao gọi là "Composite"?** Vì `ModifierRune` có thể **chứa các `ModifierRune` khác** bên trong nó (`_children`), y hệt như thư mục có thể chứa thư mục con. Một "cây" các modifier lồng nhau (Spiral chứa Bounce chứa Haste...) đều được xử lý bằng cùng 1 đoạn code đệ quy — không quan trọng cây sâu bao nhiêu tầng.

### 4.2. 4 Element & 4 Modifier — mỗi cái 1 file rất ngắn

Ví dụ đầy đủ `FireRune` (toàn bộ logic của hệ Lửa chỉ có nhiêu đây):

```python
class FireRune(ElementRune):
    BURN_DAMAGE = 8.0     # sát thương/giây
    BURN_DURATION = 3.0   # kéo dài bao lâu

    def on_hit(self, bullet, enemy, context) -> None:
        # bullet.element_stack: số lần rune Fire được xếp chồng (chọn Fire nhiều lần)
        burn = StatusEffect(effect_type="burn",
                             damage_per_sec=self.BURN_DAMAGE * bullet.element_stack,
                             duration=self.BURN_DURATION)
        enemy.add_status(burn)     # quái tự cộng dồn debuff burn vào list của nó
```

Bảng tóm tắt hàm nào được override ở từng rune (cột trống nghĩa là dùng mặc định, không làm gì):

| Rune | Loại | Override | Ý nghĩa |
|---|---|---|---|
| **FireRune** | Element | `on_hit` | Gắn `StatusEffect('burn', ...)` — quái mất máu dần |
| **IceRune** | Element | `on_hit` | Gắn `chill` (làm chậm); còn có `build_charge_attack()` riêng để tạo gai băng sạc |
| **LightningRune** | Element | `on_hit` | Gây damage tức thời + tạo hiệu ứng chớp |
| **WindRune** | Element | `on_hit` | Gắn `slow` |
| **SpiralModifier** | Modifier | `on_update` | Xoay vector `(bullet.vx, bullet.vy)` một góc nhỏ mỗi frame → đạn bay theo đường xoắn |
| **SplitModifier** | Modifier | `on_fire` | Tạo thêm N viên `Bullet` mới, lệch góc, **dùng chung `rune_tree`** với đạn gốc |
| **BounceModifier** | Modifier | `on_hit` | Tìm quái gần nhất còn sống, gọi `bullet.redirect(vx, vy)` để đổi hướng bay |
| **HasteRune** | Modifier | *(không override on_*)* | Chỉ có hàm riêng `calc_fire_rate()` — không đụng vào đạn, chỉ giảm cooldown của cả chiêu |

Ví dụ `SpiralModifier.on_update` (đổi quỹ đạo mỗi frame — toán xoay vector cơ bản):

```python
class SpiralModifier(ModifierRune):
    ROTATE_SPEED = 180.0   # độ / giây

    def on_update(self, bullet, dt: float) -> None:
        angle_rad = math.radians(self.ROTATE_SPEED * self.stack * dt)
        cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
        # Công thức xoay vector 2D: (vx, vy) → (vx', vy') một góc angle_rad
        vx_new = bullet.vx * cos_a - bullet.vy * sin_a
        vy_new = bullet.vx * sin_a + bullet.vy * cos_a
        bullet.vx, bullet.vy = vx_new, vy_new
```

### 4.3. `RuneSlots` — bàn cờ trong Rune Builder

Khi bạn mở Tab để lắp rune, bạn đang thao tác trực tiếp với 1 đối tượng `RuneSlots`. Nó không tự "biết" cách bắn đạn — nhiệm vụ duy nhất của nó là: **giữ trạng thái các ô đã lắp gì**, và khi cần thì **dịch trạng thái đó thành 1 `RuneTree`** để đạn dùng.

Mỗi hệ có sơ đồ slot khác nhau (đọc kỹ nếu tò mò sao Wind builder khác hình Fire builder), lấy ví dụ layout mặc định:

```
        [0] lõi — element, KHÓA CỨNG (đã chọn ở Skill Select, không đổi được nữa)
       /   |   \
     [1]  [2]  [3]      ← nhánh: chỉ nhận ModifierRune
      |         |
     [4]       [5]      ← "cháu" của node [1] và [3]
```

Các hàm quan trọng, đọc theo đúng thứ tự bạn tương tác:

```python
def set_core(self, rune) -> None:
    """Gọi 1 LẦN lúc bắt đầu ván (Skill Select) — gán element vào slot 0 và khóa cứng."""
    slot0 = self.get(0)
    slot0.rune = rune
    slot0.locked = True     # từ giờ không ai gỡ/đổi được node này nữa

def can_place(self, slot_id, rune) -> bool:
    """Trả lời: 'đặt rune này vào slot_id được không?' — builder gọi hàm này
    MỖI LẦN người chơi rê chuột tới 1 node, để quyết định vẽ viền xanh hay đỏ."""
    slot = self.get(slot_id)
    if slot.locked or not slot.is_empty():
        return False
    if slot.can_accept(rune):                 # đúng loại rune cho loại slot?
        if slot.slot_type == 'modifier' and isinstance(rune, ModifierRune):
            slot0_rune = self.get(0).rune
            if slot0_rune is not None and not slot0_rune.accepts_modifier(rune):
                return False    # ví dụ: Ice cấm Bounce → False ở đây
        return True
    # Trường hợp đặc biệt: modifier slot NHẬN THÊM 1 element CÙNG HỆ (để stack dmg)
    if slot.slot_type == 'modifier' and isinstance(rune, ElementRune):
        slot0_rune = self.get(0).rune
        return slot0_rune is not None and type(rune) == type(slot0_rune)
    return False

def effective_parent(self, slot_id):
    """Trèo lên theo parent_id cho tới khi gặp 1 node CÓ RUNE (bỏ qua node trống).
    Dùng để cho phép đặt modifier vào 1 node 'mồ côi' — nó vẫn tự nối lên gốc."""
    anc = self.get(slot_id).parent_id
    while anc is not None:
        if not self.get(anc).is_empty():
            return anc
        anc = self.get(anc).parent_id
    return None    # không có tổ tiên nào có rune → sẽ nối thẳng gốc cây (root)
```

**`build_rune_tree()` — hàm quan trọng nhất của `RuneSlots`**, dịch toàn bộ bàn slot thành 1 `RuneTree` sẵn sàng dùng để bắn:

```python
def build_rune_tree(self) -> RuneTree:
    tree = RuneTree()

    slot0 = self.get(0)
    if slot0.rune is not None:
        # Đếm có bao nhiêu rune CÙNG HỆ ở các nhánh → cộng vào element_stack
        # (VD: Fire ở lõi + Fire ở nhánh = element_stack 2 → burn damage nhân đôi)
        same_elem_boost = sum(1 for s in self.slots
                               if s.slot_type == 'modifier' and not s.is_empty()
                               and isinstance(s.rune, ElementRune)
                               and type(s.rune) == type(slot0.rune))
        slot0.rune.element_stack = 1 + same_elem_boost
        tree.add_element(slot0.rune)

    placed = {}   # slot_id đã xử lý → rune tương ứng (để nối con vào đúng cha)
    for s in self.slots:
        if s.slot_type != 'modifier' or s.is_empty():
            continue
        ep = self.effective_parent(s.id)          # tổ tiên gần nhất CÓ rune
        if ep is not None and ep in placed:
            tree.add_modifier(s.rune, parent=placed[ep])   # nối làm CON của rune đó
        else:
            tree.add_modifier(s.rune, parent=None)          # nối thẳng GỐC cây
        placed[s.id] = s.rune

    return tree
```

Vì sao cách này hay: dù bạn đặt rune vào node nào, lộn xộn ra sao, hàm này luôn tính ra đúng cây cha–con cuối cùng — kể cả khi node cha đang **trống** (nhờ `effective_parent` bỏ qua nó và tìm tiếp lên trên).

### 4.4. `RuneTree` — nơi "cây" thực sự chạy

`RuneTree` chỉ giữ 2 danh sách: `elements` và `modifiers` (mỗi modifier có thể có `_children` bên trong). Nó có 3 hàm khớp đúng 3 hàm của `RuneComponent`, và **duyệt cây bằng đệ quy** (đệ quy = hàm tự gọi lại chính nó cho từng node con):

```python
class RuneTree:
    def __init__(self):
        self.elements: list[ElementRune] = []
        self.modifiers: list[ModifierRune] = []

    def on_fire(self, bullet, context) -> list:
        """Gọi 1 LẦN lúc bắn. Trả về list đạn PHỤ (Split tạo ra)."""
        new_bullets = []
        for mod in self.modifiers:                          # duyệt từng modifier GỐC
            self._traverse_fire(mod, bullet, context, new_bullets, depth=1)
        return new_bullets

    def _traverse_fire(self, node, bullet, context, result, depth):
        if depth > self.MAX_DEPTH:       # giới hạn 3 tầng — tránh vòng lặp vô hạn
            return
        new = node.on_fire(bullet, context)     # cho CHÍNH node này làm việc của nó
        if new: result.extend(new)
        for child in node.get_children():                    # rồi lặp xuống TỪNG con
            self._traverse_fire(child, bullet, context, result, depth + 1)

    def on_update(self, bullet, dt):
        for mod in self.modifiers:
            self._traverse_update(mod, bullet, dt, depth=1)   # tương tự on_fire

    def on_hit(self, bullet, enemy, context):
        original_stack = bullet.element_stack
        for elem in self.elements:                            # áp MỌI element trước
            bullet.element_stack = getattr(elem, 'element_stack', 1)  # stack riêng từng elem
            elem.on_hit(bullet, enemy, context)
        bullet.element_stack = original_stack                 # khôi phục lại
        for mod in self.modifiers:                             # rồi tới MỌI modifier
            self._traverse_hit(mod, bullet, enemy, context, depth=1)
```

**Đọc kỹ hàm đệ quy `_traverse_fire` một lần nữa theo từng bước**, vì đây là chỗ dễ rối nhất với người mới:
1. Nhận vào 1 `node` (có thể là modifier gốc hoặc modifier con).
2. Cho `node` chạy việc của **chính nó** (`node.on_fire(...)`).
3. Lấy danh sách con của `node` (`node.get_children()`).
4. Với **từng đứa con**, gọi lại **chính hàm `_traverse_fire`** (đây là đệ quy) — con lại xử lý xong rồi tới cháu, tới chắt... cho tới khi hết cây hoặc chạm `MAX_DEPTH`.

Nhờ đệ quy, dù cây có 1 tầng hay 3 tầng, code xử lý **giống hệt nhau** — không cần viết riêng "nếu có 2 tầng thì..." "nếu có 3 tầng thì...".

`RuneTree` còn có `get_visual_type()` — quyết định renderer vẽ đạn kiểu gì:

```python
def get_visual_type(self) -> str:
    if not self.elements: return 'circle'          # chưa gắn hệ nào → đạn tròn cơ bản
    elem = self.elements[0]
    if isinstance(elem, FireRune):      return 'fire_bolt'
    if isinstance(elem, WindRune):      return 'wind_boomerang'
    if isinstance(elem, LightningRune): return 'lightning_beam'
    if isinstance(elem, IceRune):       return 'ice_eruption'
```

### 4.5. `Bullet` — chỉ giữ cây, không biết cây chứa gì

```python
class Bullet:
    def __init__(self, x, y, target_x, target_y, damage, rune_tree=None):
        self.x, self.y = x, y
        self.rune_tree = rune_tree      # ★ chỉ giữ 1 tham chiếu tới cây, KHÔNG copy dữ liệu
        self.element_stack = 1
        # tính vx, vy hướng về target_x, target_y...

    def update(self, dt: float) -> None:
        if self.rune_tree:
            self.rune_tree.on_update(self, dt)   # ★ Spiral xoay đạn XẢY RA Ở ĐÂY
        self.x += self.vx * dt
        self.y += self.vy * dt

    def on_hit(self, enemy, context: dict) -> None:
        self.bounce_redirect = False
        if self.rune_tree:
            self.rune_tree.on_hit(self, enemy, context)   # ★ Fire burn, Bounce nảy... XẢY RA Ở ĐÂY
        if not self.bounce_redirect:
            self.alive = False    # đạn biến mất sau khi trúng — TRỪ KHI Bounce vừa redirect nó
```

> **Đây là điểm mấu chốt của toàn bộ pattern:** `Bullet` **hoàn toàn không biết** rune_tree của nó có Fire hay Ice, có Spiral hay không. Nó chỉ gọi `self.rune_tree.on_update(self, dt)` và `self.rune_tree.on_hit(self, enemy, context)` — 2 dòng này **không bao giờ cần sửa** dù bạn thêm bao nhiêu rune mới. Đây chính là nguyên tắc **Open/Closed**: mở để mở rộng (thêm class rune mới), đóng để sửa đổi (không đụng vào `Bullet`).

### 4.6. Ví dụ dòng chảy đầy đủ — combo "Fire (lõi) + Split (nhánh 1) + Spiral (con của Split)"

```
① LẮP RUNE (lúc Tab mở builder):
   set_core(FireRune())           → slot0.rune = Fire, locked = True
   place(1, SplitModifier())      → slot1.rune = Split
   place(4, SpiralModifier())     → slot4.rune = Spiral (slot4.parent_id = 1)

② ĐÓNG BUILDER → rebuild_all_spells() → mỗi spell gọi build_rune_tree():
   effective_parent(4) = 1 (Split đã có rune) → Spiral trở thành CON của Split
   ⇒  RuneTree(elements=[Fire], modifiers=[Split(children=[Spiral])])

③ BẮN (_spawn_bullet trong game_loop.py):
   bullet = Bullet(player.x, player.y, target_x, target_y, damage, rune_tree)
   bullet.visual_type = tree.get_visual_type()      → 'fire_bolt'
   extra = tree.on_fire(bullet, context)
       └─ _traverse_fire(Split, depth=1):
             Split.on_fire() → tạo ra 2 Bullet mới (lệch góc), CÙNG rune_tree
             rồi lặp xuống con: _traverse_fire(Spiral, depth=2)
                   Spiral.on_fire() → (không làm gì, Spiral không override on_fire)
   bullets.append(bullet); bullets.extend(extra)   → giờ có 3 viên đạn bay ra

④ MỖI FRAME — bullet.update(dt) cho CẢ 3 viên:
       tree.on_update(bullet, dt)
       └─ _traverse_update(Split, depth=1): Split không làm gì (không override on_update)
             └─ _traverse_update(Spiral, depth=2): Spiral.on_update() xoay (vx, vy) của viên đạn đó
   ⇒ cả 3 viên đạn (gốc + 2 viên Split) đều tự xoay theo Spiral, vì chúng CHIA SẺ CHUNG 1 rune_tree

⑤ TRÚNG QUÁI — bullet.on_hit(enemy, context):
       tree.on_hit(bullet, enemy, context)
       ├─ Fire.on_hit(bullet, enemy, ...)   → enemy.add_status(burn, dmg = 8.0 × element_stack)
       └─ _traverse_hit(Split, depth=1): Split không làm gì lúc trúng
             └─ _traverse_hit(Spiral, depth=2): Spiral cũng không làm gì lúc trúng
```

Vài điều rút ra từ ví dụ trên:
- **Thứ tự luôn cố định**: element trước, rồi modifier gốc → con → cháu (đệ quy depth-first).
- **3 viên đạn (1 gốc + 2 từ Split) dùng CHUNG 1 object `RuneTree`** — không phải copy riêng — nên hiệu ứng Spiral áp dụng cho cả 3 mà không cần code thêm gì.
- **`element_stack`** là biến đếm số lần cùng 1 hệ được gắn (lõi + nhánh cùng loại) — dùng để nhân sát thương, được tính lại mỗi lần `build_rune_tree()`.

---

## 6. Bảng tra cứu: thao tác → cơ chế → file

| Thao tác trong game | Chạy được nhờ | File |
|---|---|---|
| Đạn gây cháy/đóng băng/giật/gió | `ElementRune.on_hit` gắn `StatusEffect` | `rune/elements/*.py`, `status_effect.py` |
| Đạn bay theo đường xoắn | `SpiralModifier.on_update` xoay vector `(vx, vy)` | `modifiers/spiral_modifier.py` |
| Bắn ra thêm nhiều đạn | `SplitModifier.on_fire` trả về list đạn mới | `modifiers/split_modifier.py` |
| Đạn nảy sang địch khác | `BounceModifier.on_hit` gọi `bullet.redirect()` | `modifiers/bounce_modifier.py` |
| Bắn nhanh hơn (giảm cooldown) | `HasteRune.calc_fire_rate()` (passive, không đụng đạn) | `modifiers/haste_rune.py`, `player.py` |
| Ghép nhiều rune cùng lúc | `RuneTree` duyệt cây đệ quy, gọi từng rune | `rune_tree.py` |
| Lắp/gỡ rune trong Tab menu | `RuneSlots.place/remove/swap` + `rune_builder_screen.py` xử lý click | `rune_slots.py`, `ui/screens/rune_builder_screen.py` |
| Node "mồ côi" tự nối lên gốc | `effective_parent()` + `build_rune_tree()` | `rune_slots.py` |
| Cấm Bounce trên Ice/Lightning/Wind | `ElementRune.accepts_modifier()` + `FORBIDDEN_MODIFIERS` | `rune_component.py`, `elements/*.py` |
| Q/E đổi qua lại 2 chiêu | `Player.spells[]` — mỗi phần tử 1 `SpellBuild` (cây rune độc lập) | `player.py` |
| 4 hệ bắn ra 4 kiểu khác hẳn | `game_loop._update()` bước 2, phân nhánh theo `get_visual_type()` | `game_loop.py` |
| Lên cấp ra 3 thẻ Rune/Stat | `LevelManager._generate_choices()` (tỉ lệ đổi theo wave) | `leveling/level_manager.py` |
| Quái xuất hiện dần theo thời gian | `WaveManager.update()` trả về danh sách cần spawn | `wave/wave_manager.py` |

---

## 7. Các hệ thống phụ

- **Player / SpellBuild** (`player.py`) — `setup_spells([element1, element2])` được gọi đúng 1 lần khi rời màn Skill Select, tạo ra **2 `SpellBuild`** (mỗi cái là 1 bộ `RuneSlots` + `RuneTree` + đồng hồ cooldown riêng). `Player.spells` là 1 list, `active_spell_index` cho biết đang dùng chiêu nào, đổi bằng phím Q/E.
  8 chỉ số: `HP, Speed, Damage, Armor, HPRegen, Lucky, CDR, XPRange`. `Lucky` ảnh hưởng 3 thứ cùng lúc: % chí mạng, độ hiếm thẻ lên cấp, số XP orb rơi ra. `Ultimate` (chuột phải, cooldown 8s, phép theo hệ lõi) và `Dash` (Space, cooldown 3s) là 2 class riêng trong `abilities/`.
- **Leveling** (`leveling/level_manager.py`) — mỗi lần lên cấp, sinh 3 thẻ trộn giữa Rune (từ `ALL_RUNES`) và `StatUpgrade` (5 bậc hiếm: Common/Uncommon/Rare/Epic/Legendary, trọng số 50/28/15/6/1%). Tỉ lệ Rune/Stat đổi theo wave (`wave // 5` quyết định số thẻ Stat).
- **Wave** (`wave/wave_manager.py`) — mỗi 15 giây spawn 1 đợt quái (số lượng tăng theo wave), 8 giây spawn lẻ 1 con random. Boss xuất hiện ở wave 8 **hoặc** sau 12 phút, tùy điều kiện nào tới trước. Từ wave 2 có 30% quái là `RangedEnemy`, wave 5 thêm `FastEnemy`, wave 10 thêm `TankEnemy`.
- **UI Builder** (`ui/screens/rune_builder_screen.py` + `ui/rune_ui_config.py`) — màn "Watcher's Heart" vẽ cây hex theo layout riêng từng hệ (`slot_defs_for_rune`), kho 5 slot chứa modifier chưa lắp, click trái để chọn/gắn, **click phải để gỡ về kho** (kể cả khi đang lỡ cầm 1 rune khác), node "mồ côi" được vẽ nét đứt nối lên tổ tiên gần nhất để không trông như bị rời.

---

## 8. Muốn mở rộng game?

Nhờ Open/Closed Principle, thêm nội dung mới **không cần sửa code cũ**:

- **Thêm 1 nguyên tố mới**:
  1. Tạo class kế thừa `ElementRune`, override `on_hit` để định nghĩa hiệu ứng.
  2. Thêm entry vào `rune_ui_config.ELEMENT_THEMES` + `ELEMENT_ORDER` (màu, tên hiển thị, icon).
  3. Thêm 1 layout slot riêng trong `rune_slots.py` nếu muốn cây khác hình các hệ kia (không bắt buộc).
  4. **Không đụng** `Bullet`, `RuneTree`, hay `game_loop.py` — trừ khi hệ mới cần 1 kiểu bắn hoàn toàn khác (như Ice/Lightning/Wind hiện tại).

- **Thêm 1 bổ trợ mới** (VD: "Homing" — đạn tự tìm mục tiêu gần nhất):
  1. Tạo class kế thừa `ModifierRune`, override `on_update` (hoặc `on_fire`/`on_hit` tùy hiệu ứng cần lúc nào).
  2. Thêm vào `ALL_RUNES` trong `level_manager.py` để nó xuất hiện trong pool thẻ lên cấp.
  3. Xong — `RuneTree` và `Bullet` **tự động** gọi nó đúng lúc, không cần sửa gì thêm.

---

## 9. ★★ Sổ tay sửa/update — muốn đổi cái này thì sửa ở đâu

Tra theo nhu cầu thực tế: "tôi muốn đổi X" → sửa file nào, biến/hàm nào. Sau khi sửa xong, **luôn chạy lại test**:

```bash
python -m pytest tests/ -q
```

(1 test `test_get_mouse_world_pos` fail sẵn từ trước, không liên quan — các test khác phải xanh hết.)

### 9.1. Nguyên tố (Fire/Ice/Lightning/Wind)

| Muốn đổi... | Sửa ở đâu |
|---|---|
| Sát thương / thời gian burn, chill, slow... | Hằng số đầu class trong `logic/rune/elements/*.py` (VD `FireRune.BURN_DAMAGE`, `IceRune.SLOW_DURATION`) |
| Hiệu ứng khi trúng địch (thêm debuff mới) | Sửa `on_hit()` của class element tương ứng — xem mẫu `StatusEffect(...)` trong `fire_rune.py` |
| Cấm/mở 1 modifier cho 1 hệ (VD không muốn cấm Bounce trên Wind nữa) | Sửa tuple `FORBIDDEN_MODIFIERS` đầu class trong `elements/*.py` |
| Mô tả hiển thị trong Skill Select / Builder | `get_display_name()`, `get_description()`, `get_color()` trong cùng file element |
| Kiểu bắn của 1 hệ (đạn thường / beam / sạc / boomerang) | `game_loop.py` hàm `_update()` bước 2 — phân nhánh theo `visual_type`; và `RuneTree.get_visual_type()` trong `rune_tree.py` để đổi cách nhận diện hệ |
| Layout cây rune (vị trí node) riêng của 1 hệ | `SLOT_DEFS_FIRE` / `SLOT_DEFS_ICE` / `SLOT_DEFS_WIND` / `SLOT_DEFS_LIGHTNING` trong `logic/rune/rune_slots.py` (mỗi phần tử là `(id, parent_id, slot_type, x, y)`) |
| Màu sắc / tên hiển thị / ảnh artwork trong Builder | `ui/rune_ui_config.py` — `ELEMENT_THEMES` (màu, glyph, tên chiêu, mô tả), phần load ảnh trong `_load_icons()` |
| Thêm 1 nguyên tố hoàn toàn mới | Xem mục 8 ("Muốn mở rộng game?") |

### 9.2. Modifier (Spiral/Split/Bounce/Haste)

| Muốn đổi... | Sửa ở đâu |
|---|---|
| Tốc độ xoay của Spiral | `SpiralModifier.ROTATE_SPEED` trong `modifiers/spiral_modifier.py` |
| Số đạn phụ / góc lệch của Split | `SplitModifier.SPLIT_ANGLE` và vòng lặp trong `on_fire()`, file `modifiers/split_modifier.py` |
| Số lần nảy tối đa / tốc độ bay lại của Bounce | `BounceModifier.MAX_BOUNCE`, `BOUNCE_SPEED` trong `modifiers/bounce_modifier.py` |
| % giảm cooldown của Haste mỗi stack | `HasteRune.REDUCTION_PER_STACK`, `MIN_FIRE_RATE` trong `modifiers/haste_rune.py` |
| Thêm 1 modifier hoàn toàn mới | Xem mục 8 |

### 9.3. Rune Builder ("Watcher's Heart") — giao diện lắp rune

| Muốn đổi... | Sửa ở đâu |
|---|---|
| Vị trí / kích thước cây hex (board) | `BOARD_CENTER`, `BOARD_RADIUS` trong `ui/rune_ui_config.py` |
| Vị trí thanh kho 5-slot "RESOURCES" | Hàm `_draw_modifier_storage()` trong `ui/screens/rune_builder_screen.py` — biến `cx`, `y0` |
| Số slot hiển thị trong kho (mặc định 5) | Hằng `VISIBLE` trong cùng hàm `_draw_modifier_storage()` |
| Cách gỡ rune về kho (chuột phải) | Hàm `_handle_slot_remove()` trong `rune_builder_screen.py` — gọi từ `handle_event()` khi `event.button == 3` |
| Luật "node rời tự nối lên tổ tiên" | `RuneSlots.effective_parent()` + `build_rune_tree()` trong `logic/rune/rune_slots.py` |
| Đường dây nối / mũi tên giữa các node | `_draw_tree_links()` trong `rune_builder_screen.py` |
| Panel mô tả chiêu bên trái (tên, damage, mô tả) | `_draw_ability_panel()` + `_spell_profile()` trong `rune_builder_screen.py` |
| Phím tắt mở/đóng Builder (mặc định Tab) | `game_loop._handle_event()` — đoạn kiểm tra `event.key in (K_ESCAPE, K_TAB)` |

### 9.4. Màn chọn nguyên tố đầu ván (Skill Select)

| Muốn đổi... | Sửa ở đâu |
|---|---|
| Số hệ được chọn (mặc định 2) | `SPELL_COUNT` trong `ui/rune_ui_config.py` |
| Giao diện màn chọn (bố cục hex, chữ) | `ui/screens/skill_select_screen.py` |
| Cách nguyên tố đã chọn biến thành chiêu | `Player.setup_spells()` trong `logic/entities/player.py` — gọi `slot_defs_for_rune()` + `rune_slots.set_core()` |

### 9.5. Chỉ số & khả năng của Player

| Muốn đổi... | Sửa ở đâu |
|---|---|
| HP / tốc độ / damage / fire rate cơ bản | Hằng số `BASE_HP`, `BASE_SPEED`, `BASE_DAMAGE`, `BASE_FIRE_RATE` đầu class `Player` trong `logic/entities/player.py` |
| Công thức tính % chí mạng theo Lucky | `Player.get_crit_chance()` |
| Cooldown Ultimate / Dash | `Player.ultimate_cooldown` (player.py); `DashAbility` trong `logic/abilities/movement/dash_ability.py` |
| Hiệu ứng Ultimate theo từng hệ | `logic/abilities/ultimate/ultimates.py` (FireNova/IceBlizzard/LightningStorm/WindCyclone/ShadowNova, được chọn qua `ultimate_base.get_ultimate_for_spell()`) |
| Số chiêu tối đa (đang là 2) | `rune_ui_config.SPELL_COUNT` (mục 9.4) — không sửa cứng trong `player.py` |

### 9.6. Độ hiếm & phần thưởng lên cấp

| Muốn đổi... | Sửa ở đâu |
|---|---|
| Tỉ lệ % mỗi bậc hiếm (Common→Legendary) | `RARITY_WEIGHTS` trong `logic/leveling/stat_upgrade.py` |
| Giá trị tăng của từng stat theo từng bậc hiếm | `STAT_DEFS` trong `stat_upgrade.py` |
| Tỉ lệ thẻ Rune vs thẻ Stat theo wave | `LevelManager._generate_choices()` trong `logic/leveling/level_manager.py` — biến `stat_count` |
| Danh sách rune có thể rơi ra khi lên cấp | `ALL_RUNES` trong `level_manager.py` (đây là chỗ thêm nguyên tố/modifier mới vào pool thật) |
| Số lượng thẻ mỗi lần lên cấp (đang là 3) | `CHOICES_COUNT` trong `level_manager.py` |

### 9.7. Kẻ địch & Wave/Boss

| Muốn đổi... | Sửa ở đâu |
|---|---|
| Thời gian giữa các đợt spawn / số quái mỗi đợt | `SPAWN_INTERVAL`, `SPAWN_COUNT_BASE` trong `logic/wave/wave_manager.py` |
| Wave/thời gian Boss xuất hiện | `BOSS_WAVE`, `BOSS_TIME` trong `wave_manager.py` |
| Tỉ lệ loại quái xuất hiện (thường/tầm xa/nhanh/tank) theo wave | Khối `if self.wave >= ...` trong `WaveManager.update()` |
| HP/tốc độ quái tăng theo wave | Biến `hp_mult`, `speed_mult` (công thức `1.0 + wave * 0.05`) trong `wave_manager.py` |
| Chỉ số riêng của 1 loại quái (HP, damage, tốc độ) | File riêng: `logic/entities/enemy.py` (thường), `ranged_enemy.py`, `fast_enemy.py`, `tank_enemy.py`, `boss.py` |
| Thêm 1 loại quái mới | Tạo file mới trong `logic/entities/`, kế thừa `Enemy`; thêm nhánh xử lý trong `WaveManager.update()` và `game_loop._process_wave_events()` |

### 9.8. Hình ảnh / hiệu ứng (VFX)

| Muốn đổi... | Sửa ở đâu |
|---|---|
| Hiệu ứng nổ/impact khi đạn trúng | `ui/renderer.py` — các hàm `_draw_*_effect` theo `kind` (VD `_draw_ice_spike_effect`) |
| Animation gai băng bị cắt/lỗi hình | `Renderer._tile_ice_spike_frames()` trong `renderer.py` — biến `pad` kiểm soát vùng đệm cuối |
| Ảnh sprite của quái/player/hiệu ứng | Thư mục `assets/sprites/`, `assets/element/`; đường dẫn nạp trong `renderer.py` hoặc `rune_ui_config._load_icons()` |

### 9.9. HUD & màn hình phụ

| Muốn đổi... | Sửa ở đâu |
|---|---|
| Thanh máu / thanh chiêu / hiển thị cooldown | `ui/hud.py` |
| Giao diện Level Up (thẻ chọn) | `ui/screens/level_up_screen.py` |
| Giao diện Game Over / Win | `ui/screens/game_over_screen.py`, `ui/screens/win_screen.py` |
| Phím điều khiển (WASD, chuột, Q/E, Space, Tab) | `ui/input_handler.py` (đọc phím) + `game_loop._handle_event()` (xử lý ý nghĩa từng phím) |

### 9.10. Debug / Cheat

| Muốn đổi... | Sửa ở đâu |
|---|---|
| Cheat noclip (F9) / nạp modifier vào kho (F8) | `game_loop._handle_event()` — khối kiểm tra `K_F9` / `K_F8`; hàm `_cheat_add_all_runes()` |
| Bật/tắt chế độ hiện toàn bộ kho khi cuộn | Cờ `player.cheat_mode`, đọc trong `_draw_modifier_storage()` (`rune_builder_screen.py`) |

---

> **Tóm lại toàn bộ tài liệu trong 1 câu:** game chạy được mọi combo Rune là nhờ **Composite Pattern** — `RuneSlots` dịch bàn lắp rune thành `RuneTree`, `RuneTree` duyệt cây đệ quy và gọi đúng hàm của từng `RuneComponent`, còn `Bullet` (và các đòn đánh Lightning/Ice/Wind) chỉ cần **giữ 1 tham chiếu tới cây** và gọi 3 điểm móc `on_fire / on_update / on_hit` — không bao giờ cần biết bên trong cây có những rune gì.
