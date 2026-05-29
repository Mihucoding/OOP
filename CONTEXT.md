# CONTEXT — Đồ Án Game: 2D Survival Roguelike (Rune Crafting)

> **Cập nhật lần cuối**: 2026-05-20

---

## 1. Thông tin chung

| Mục | Giá trị |
|-----|---------|
| Thể loại | 2D Top-down Survival Roguelike |
| Ngôn ngữ | Python 3.11 + Pygame-CE |
| Trình độ | Sinh viên năm 1 — code rõ ràng, comment tiếng Việt |
| Resolution | 1280 × 720 |
| Góc nhìn | Top-down, player luôn ở center màn hình |
| OOP Pattern | Composite Pattern · Open/Closed · Composition over Inheritance |

---

## 2. Điều khiển

| Input | Hành động |
|-------|-----------|
| W / A / S / D | Di chuyển 4 hướng + chéo |
| Mouse position | Hướng ngắm |
| Left click | Bắn chiêu active về phía con trỏ |
| **Right click** | Kích hoạt **Ultimate** (cooldown 8s) |
| **Space** | **Dash** 200px theo hướng di chuyển (cooldown 3s) |
| **Q / E** | Chuyển chiêu trước / sau khi đang chơi |
| **Tab** | Mở / Đóng Rune Builder |
| 1 / 2 / 3 | Chọn phần thưởng khi lên cấp |
| R | Chơi lại (GameOver / WinScreen) |
| ESC | Thoát / Đóng màn hình hiện tại |

---

## 3. Hệ thống Rune

### 3.1 Element Rune (4 loại — leaf node)

| Class | Effect on_hit | Stack Effect |
|-------|--------------|--------------|
| `FireRune` | Burn: 8 damage/s × 3s | ×2 → dps nhân đôi |
| `IceRune` | Chill: slow + stacks (5 stacks = đóng băng) | ×2 → chill sâu hơn |
| `LightningRune` | Stun: đứng yên hoàn toàn 0.8s + 15 instant dmg | ×2 → stun lâu hơn + dmg gấp đôi |
| `WindRune` | Knockback 120px + slow 30% × 2s | ×2 → knockback xa hơn |

> `PoisonRune` vẫn tồn tại trong code nhưng **không có trong pool lên cấp**.

### 3.2 Modifier Rune (4 loại — composite node)

| Class | Hành vi | Stack Effect |
|-------|---------|--------------|
| `SpiralModifier` | Rotate velocity 180°/s mỗi frame | ×2 → xoắn nhanh gấp đôi |
| `BounceModifier` | Nảy sang quái gần nhất (max 2 lần) | ×2 → nảy max 4 lần |
| `SplitModifier` | Tạo thêm 2 viên đạn ±20° khi bắn | ×2 → tạo thêm 4 viên |
| `HasteRune` | **Passive** — không ảnh hưởng đạn, giảm 20% cooldown chiêu/stack | Tối thiểu 0.1s |

### 3.2b Same-Element Stack

Nếu Slot 0 đã có ElementRune, có thể đặt cùng loại vào Slot 1/2/3/4:
- Không tạo element mới trong `tree.elements`
- Tăng `element_stack` trên element Slot 0
- Ví dụ: Slot 0 = FireRune + Slot 2 = FireRune → `element_stack = 2` → burn damage × 2

### 3.3 Composite Pattern

```
RuneComponent (ABC)
├── on_hit(bullet, enemy, context)   ← abstract
├── on_update(bullet, dt)            ← abstract
├── on_fire(bullet, context) → list  ← abstract
└── get_children() → list            ← default []

ElementRune(RuneComponent)   ← leaf: chỉ on_hit
ModifierRune(RuneComponent)  ← composite: on_update + on_fire + children
```

### 3.4 SpellBuild + RuneTree (đã cập nhật — 3 chiêu riêng)

```
Player:
    spells: [Chiêu 1, Chiêu 2, Chiêu 3]
    active_spell_index: int

SpellBuild:
    name: str
    rune_slots: RuneSlots
    rune_tree: RuneTree

RuneTree:
    elements:  list[ElementRune]   ← mọi Element trong cây của chiêu
    modifiers: list[ModifierRune]  ← mọi Modifier trong cây của chiêu
    MAX_DEPTH = 3

Đạn thường là mặc định:
  - Không cần Element vẫn bắn được đạn thường
  - Modifier như Spiral/Bounce/Split dùng được ngay (Slot 0 trống)
  - Slot 0 (Hệ chính) chỉ thêm hiệu ứng Element on_hit

Ví dụ:
  Chiêu 1: Spiral + Fire    → đạn thường bay xoắn, trúng gây burn
  Chiêu 2: Bounce + Ice     → đạn thường nảy, trúng gây chill
  Chiêu 3: Split + Wind     → đạn tách, trúng knockback
```

### 3.5 RuneSlots — Slot-based Rune Builder

```
Mỗi chiêu có 1 cây 2 trái - 2 phải:

              [0: Hệ chính]     ← optional ElementRune
              /              \
        [1: L1]              [2: R1]    ← chỉ ModifierRune
            |                    |
        [3: L2]              [4: R2]    ← chỉ ModifierRune

Quy tắc đặt rune (Hướng B):
  - Slot 0: Hệ chính (optional), chỉ nhận ElementRune
  - Slot 1/2: chỉ nhận ModifierRune, đặt được ngay khi Slot 0 trống
  - Slot 3 cần Slot 1 có rune; Slot 4 cần Slot 2 có rune
  - Đạn thường là mặc định ngoài cây, luôn bắn được
```

### 3.6 Flow Rune Builder (Mylistra-style)

```
Lên cấp → Chọn Rune → Rune vào INVENTORY
                             ↓
            [Tab] → Rune Builder (full screen)
                             ↓
     Chọn Chiêu 1/2/3 → Click inventory rune → Click slot trống
                             ↓
     [Tab / ESC / Enter] → Rebuild 3 chiêu → Game tiếp tục
```

### 3.7 Stack Rune

- Modifier: có thuộc tính `stack` — dùng cùng một instance, tăng stack
- Element: có thuộc tính `element_stack` trên instance — mỗi element độc lập
- `bullet.element_stack` được set tạm từng element khi gọi `RuneTree.on_hit`

---

## 4. StatusEffect (đã cập nhật)

| Type | Tác dụng | Stacking |
|------|---------|---------|
| `burn` | damage_per_sec. 5 stacks → 5% max HP/s | Có (max 5 stacks) |
| `chill` | Slow dựa theo stacks: 1→20%, 5→100% slow | Có (max 5 stacks) |
| `slow` | Giảm tốc cố định (slow_factor) | Không stack |
| `stun` | slow_factor = 0.0 (đứng yên hoàn toàn) | Không stack |
| `poison` | damage_per_sec đơn giản | Không stack |

Enemy update kiểm tra `eff.slow_factor < 1.0` (không phân biệt loại) → chill, slow, stun đều dùng cùng cơ chế.

---

## 5. Enemy System (đã cập nhật)

| Class | Hành vi | HP | Speed | XP |
|-------|---------|----|----|-----|
| `Enemy` | Chase player | 50 | 80 | 10 |
| `RangedEnemy` | Dừng ở 350px, bắn đạn 2s/lần | 50 | 80 | 15 |
| `Boss` | Charge + AoE + Summon | 1000 | 50 | 500 |

### EnemyBullet
- `RangedEnemy` bắn `EnemyBullet` về phía player
- Speed 220, Damage 12, Lifetime 4s
- Va chạm player → `player.take_damage(12)`

### Boss Skills
1. **Charge**: lao thẳng 350 px/s trong 1.2s (cooldown 8s)
2. **AoE Slam**: vùng tròn bán kính 120px, 40 dmg/s trong 1.5s (cooldown 12s)
3. **Summon**: triệu hồi 4 Enemy xung quanh (cooldown 15s, dùng `pending_summon` flag)

---

## 6. Wave System

| Thông số | Giá trị |
|----------|---------|
| Spawn chính | Mỗi **15s**, tăng dần: `SPAWN_COUNT_BASE(3) + wave` quái |
| Spawn phụ | Mỗi **8s**, 1 quái ngẫu nhiên |
| RangedEnemy | 30% cơ hội từ wave 2 trở đi |
| Boss trigger | Wave **8** HOẶC **12 phút** |
| Boss Summon | WaveManager xử lý `boss.pending_summon` flag |

---

## 7. Level-up System

| Thông số | Giá trị |
|----------|---------|
| Lựa chọn | 3 card = mix **Rune** + **StatUpgrade** (tỉ lệ theo wave) |
| Rune pool | Fire, Ice, Lightning, Wind, Spiral, Bounce, Split, HasteRune |
| Stat pool | MaxHP, Speed, Damage, Armor, HPRegen, Lucky, CDR, XPRange |
| Rarity | 5 bậc: Common/Uncommon/Rare/Epic/Legendary (trọng số 50/28/15/6/1%) |
| Lucky boost | Lucky cao → shift rarity weight về Rare/Epic |
| Wave 0–4 | 2 Rune + 1 Stat |
| Wave 5+ | 1 Rune + 2 Stat |
| Flow Rune | → inventory → đặt thủ công qua Rune Builder |
| Flow Stat | → apply trực tiếp lên player |
| XP để lên cấp | `xp_to_next` × 1.4 mỗi level |

---

## 8. Map & Camera

| Thông số | Giá trị |
|----------|---------|
| Map | Vô hạn (không có tường), grid động theo camera |
| Player | Luôn ở center màn hình (camera_x = player.x) |
| Camera | World offset: `screen_x = world_x - cam_x + SCREEN_W/2` |

---

## 9. Win / Lose

| Điều kiện | Kết quả |
|-----------|---------|
| HP = 0 | THUA → `GameOverScreen` |
| Boss chết | THẮNG → `WinScreen` |

---

## 10. UI & Màn hình

| State | Màn hình | Mô tả |
|-------|---------|-------|
| `menu` | `MainMenu` | Tiêu đề + Enter để bắt đầu |
| `playing` | `Renderer` + `HUD` | Game chính |
| `level_up` | `LevelUpScreen` | 3 card Rune (phím 1/2/3 hoặc click) |
| `rune_builder` | `RuneBuilderScreen` | Tab: Inventory + 3 chiêu + cây 2 trái/2 phải |
| `game_over` | `GameOverScreen` | R=restart, ESC=quit |
| `win` | `WinScreen` | R=restart, ESC=quit |

### HUD Elements
- HP bar + "HP X/Y" — góc trên trái
- XP bar + "Lv.X" — bên dưới HP bar
- Wave info — góc trên phải
- Chiêu active + Rune list (tên màu + stack count) — bên dưới XP bar
- Notification "[Tab] Mở Rune Builder (N rune chờ)" — khi có rune trong inventory

---

## 11. Cấu trúc thư mục (đầy đủ, đã implement)

```
OOP/
├── main.py
├── requirements.txt
├── logic/                              # PHẦN 1: Logic (không import pygame)
│   ├── entities/
│   │   ├── status_effect.py           # burn/chill/slow/stun/poison + stacks
│   │   ├── xp_orb.py                  # XP drop, auto-collect
│   │   ├── bullet.py                  # Bullet + RuneTree runtime
│   │   ├── player.py                  # Player + inventory + 3 SpellBuild
│   │   ├── enemy.py                   # Enemy base + chase AI
│   │   ├── ranged_enemy.py            # RangedEnemy (giữ khoảng cách + bắn)
│   │   ├── enemy_bullet.py            # Đạn của RangedEnemy
│   │   └── boss.py                    # Boss(Enemy) + 3 skills
│   ├── rune/
│   │   ├── rune_component.py          # ABC Composite Pattern
│   │   ├── rune_tree.py               # RuneTree (Base Spell + Elements + Modifiers)
│   │   ├── rune_slots.py              # RuneSlots (Core + L1/L2/R1/R2)
│   │   ├── elements/
│   │   │   ├── fire_rune.py           # Burn (stacks)
│   │   │   ├── ice_rune.py            # Chill (stacks, 5=đóng băng)
│   │   │   ├── lightning_rune.py      # Stun + instant damage
│   │   │   ├── wind_rune.py           # Knockback + slow
│   │   │   └── poison_rune.py         # Poison (không trong pool)
│   │   └── modifiers/
│   │       ├── spiral_modifier.py     # Xoắn ốc (rotation matrix)
│   │       ├── bounce_modifier.py     # Nảy quái gần nhất
│   │       └── split_modifier.py      # Tách đạn ±20°/stack
│   ├── wave/
│   │   └── wave_manager.py            # Timer spawn + RangedEnemy 30% + boss
│   └── leveling/
│       └── level_manager.py           # 3 random choices → inventory
└── ui/                                # PHẦN 2: UI + Game Loop
    ├── game_loop.py                   # State machine 6 states
    ├── renderer.py                    # Draw shapes + status halo + grid
    ├── hud.py                         # HP/XP bar + rune list + notification
    ├── input_handler.py               # WASD + mouse
    └── screens/
        ├── main_menu.py
        ├── level_up_screen.py         # 3 card (phím 1/2/3 + click)
        ├── game_over_screen.py
        ├── win_screen.py
        ├── rune_builder_screen.py     # Inventory + 3 chiêu + 4 slot rune
        └── rune_tree_screen.py        # (Legacy overlay — không dùng trong game)
```

---

## 12. Quy tắc bất biến (OOP)

1. `logic/` **KHÔNG** import pygame
2. `ui/` CÓ THỂ import từ `logic/`
3. Mỗi Rune = 1 file riêng
4. `Bullet` nhận `RuneTree` lúc runtime — không subclass theo loại đạn
5. Thêm Rune mới = thêm class mới, **không sửa** `RuneComponent`, `Bullet`
6. `RuneTree.on_hit` set tạm `bullet.element_stack` per element → mỗi element dùng stack riêng

---

## 13. Tiến độ

| Ngày | Việc đã làm |
|------|-------------|
| 2026-04-30 | Xác nhận requirements, tạo skeleton |
| 2026-05-19 | Implement toàn bộ logic + UI |
| 2026-05-19 | Thêm LightningRune, WindRune (thay Poison) |
| 2026-05-19 | StatusEffect stacks (burn 5x, chill) |
| 2026-05-19 | RangedEnemy + EnemyBullet |
| 2026-05-19 | Rune Builder fullscreen (Mylistra-style) |
| 2026-05-19 | Refactor RuneTree thành 3 chiêu riêng, mỗi chiêu Base + 2 trái/2 phải |
| 2026-05-19 | 61 combo tests PASSED, 24 multi-element tests PASSED |
| 2026-05-20 | Slot 0 element slot (Hướng B): nhánh chỉ Modifier, 24 tests PASSED |
| 2026-05-20 | Same-element stack vào nhánh → tăng element_stack |
| 2026-05-20 | Boss timing điều chỉnh, Q/E switch, per-spell cooldown, XP scatter/magnet |
| 2026-05-20 | HasteRune passive CDR |
| 2026-05-20 | 2 hệ lên cấp: Rune + StatUpgrade (8 stats × 5 rarity) |
| 2026-05-20 | Lucky stat (crit + rarity + XP drops) |
| 2026-05-20 | Ultimate system (5 loại từ Slot 0 element), right-click |
| 2026-05-20 | Dash (Space, 200px, 3s) + MovementAbility base |
| 2026-05-20 | Stats panel trong Rune Builder (tab Inventory/Chỉ số) |
| 2026-05-20 | 32 unittest PASSED |
