# CONTEXT — Đồ Án Game: 2D Survival Roguelike (Rune Crafting)

## 1. Thông tin chung (đã xác nhận toàn bộ)

| Mục | Giá trị |
|-----|---------|
| Thể loại | 2D Top-down Survival Roguelike |
| Ngôn ngữ | Python + Pygame |
| Trình độ | Sinh viên năm 1 — code rõ ràng, comment tiếng Việt |
| Resolution | 1280 × 720 |
| Góc nhìn | Top-down, player luôn ở center màn hình |

---

## 2. Điều khiển

| Input | Hành động |
|-------|-----------|
| W / A / S / D | Di chuyển 4 hướng + chéo |
| Mouse position | Hướng ngắm |
| Left click | Bắn đạn về phía con trỏ |

---

## 3. Hệ thống Rune (đã xác nhận)

### Element Rune (3 loại — leaf node)
| Class | Hiệu ứng on_hit |
|-------|----------------|
| `FireRune` | Burn: damage over time |
| `IceRune` | Slow: giảm tốc độ quái |
| `PoisonRune` | Poison: rút máu từ từ |

### Modifier Rune (3 loại — composite node, có thể có con)
| Class | Hành vi |
|-------|---------|
| `SpiralModifier` | Quỹ đạo xoắn ốc (rotate velocity mỗi frame) |
| `BounceModifier` | Nảy sang quái gần nhất sau khi trúng |
| `SplitModifier` | Tạo thêm 2 đạn khi bắn (tổng 3 viên) |

### Composite Pattern
```
RuneComponent (ABC)
├── on_hit(bullet, enemy, context)   ← abstract
├── on_update(bullet, dt)            ← abstract
├── on_fire(bullet, context) → list  ← abstract
└── get_children() → list            ← default []

ElementRune(RuneComponent)  ← leaf
    on_hit: áp dụng hiệu ứng
    on_update: pass
    on_fire: return []
    get_children: return []

ModifierRune(RuneComponent)  ← composite
    on_hit: pass
    on_update: thay đổi trajectory
    on_fire: có thể tạo thêm đạn
    get_children: return self._children
    add_child(rune): thêm rune con
```

### RuneTree
```
RuneTree:
    element: ElementRune        (bắt buộc, chính xác 1)
    modifiers: [ModifierRune]   (parallel ở root)
    MAX_DEPTH = 3

Parallel: element + [SpiralMod, IceMod]  → xoắn + đóng băng
Serial:   element + SpiralMod(child=BounceMod) → xoắn, con nảy
```

### Stack Rune
- Cho phép chọn cùng 1 Rune nhiều lần
- Stack Fire × 2 = burn mạnh hơn hoặc lâu hơn
- Stack Spiral × 2 = xoắn ốc nhanh hơn

---

## 4. Wave System (đã xác nhận)

| Thông số | Giá trị |
|----------|---------|
| Spawn type | Theo thời gian + random nhỏ xen kẽ |
| Boss trigger | Sau wave 3–4 HOẶC 7–8 phút |
| Boss | To hơn + nhiều HP + skill riêng |

### Boss Skills
1. **Charge**: lao thẳng vào player tốc độ cao 1 giây
2. **AoE Slam**: vùng damage hình tròn xung quanh boss
3. **Summon**: triệu hồi 3–5 quái nhỏ

---

## 5. Level-up System (đã xác nhận)

| Thông số | Giá trị |
|----------|---------|
| Lựa chọn | 3 Rune ngẫu nhiên mỗi lần lên cấp |
| Stack | Có — có thể chọn cùng Rune nhiều lần |

---

## 6. Map & Camera

| Thông số | Giá trị |
|----------|---------|
| Map | Cố định, mặt phẳng đơn giản |
| Player | Luôn ở center màn hình |
| Camera | Scroll theo player (world offset) |

---

## 7. Win / Lose

| Điều kiện | Kết quả |
|-----------|---------|
| HP = 0 | THUA → GameOverScreen |
| Boss chết | THẮNG → WinScreen |

---

## 8. UI & Sprite System

- Default: vẽ hình học (colored shapes) — không cần asset
- Sprite: Renderer có cache, nếu có file ảnh thì dùng, không thì fallback shapes
- Hiệu ứng: status halos quanh enemy, particle đơn giản

---

## 9. Cấu trúc thư mục

```
DOANOOP/
├── main.py                         # Entry point
├── requirements.txt
├── assets/
│   ├── sprites/
│   ├── sounds/
│   └── fonts/
├── logic/                          # PHẦN 1: Game Logic (không import pygame)
│   ├── __init__.py
│   ├── entities/
│   │   ├── __init__.py
│   │   ├── player.py               # Player stats + movement logic
│   │   ├── enemy.py                # Enemy base + chase AI
│   │   ├── boss.py                 # Boss(Enemy) + 3 skills
│   │   ├── bullet.py               # Bullet + RuneTree
│   │   └── xp_orb.py              # XP drop
│   ├── rune/
│   │   ├── __init__.py
│   │   ├── rune_component.py       # ABC — Composite Pattern
│   │   ├── rune_tree.py            # RuneTree, max depth 3
│   │   ├── elements/
│   │   │   ├── __init__.py
│   │   │   ├── fire_rune.py
│   │   │   ├── ice_rune.py
│   │   │   └── poison_rune.py
│   │   └── modifiers/
│   │       ├── __init__.py
│   │       ├── spiral_modifier.py
│   │       ├── bounce_modifier.py
│   │       └── split_modifier.py
│   ├── wave/
│   │   ├── __init__.py
│   │   └── wave_manager.py         # Timer-based spawn + boss trigger
│   └── leveling/
│       ├── __init__.py
│       └── level_manager.py        # XP, level-up, 3 random rune choices
└── ui/                             # PHẦN 2: UI + Game Loop
    ├── __init__.py
    ├── game_loop.py                 # State machine: MENU→PLAYING→LEVELUP→END
    ├── renderer.py                  # Vẽ tất cả entities (shape + sprite support)
    ├── hud.py                       # HP bar, XP bar, wave counter
    ├── input_handler.py             # WASD + mouse → game commands
    └── screens/
        ├── __init__.py
        ├── main_menu.py
        ├── level_up_screen.py       # Hiển thị 3 Rune lựa chọn
        ├── game_over_screen.py
        └── win_screen.py
```

---

## 10. Phân công AI (tiết kiệm token)

| Phần | AI đề xuất | Lý do |
|------|-----------|-------|
| `logic/rune/` | **Claude** | OOP phức tạp, Composite Pattern |
| `logic/entities/` | **Claude** | Game logic chính |
| `logic/wave/` + `leveling/` | **Claude/Gemini** | Vừa phải |
| `ui/renderer.py` + `ui/hud.py` | **Gemini** | Boilerplate render |
| `ui/screens/` | **Gemma** | Simple UI, ít logic |
| `main.py` | **Claude** | Kết nối tất cả |

---

## 11. Tiến độ

| Ngày | Việc đã làm |
|------|-------------|
| 2026-04-30 | Xác nhận toàn bộ requirements (9 file traloi) |
| 2026-04-30 | Tạo cấu trúc thư mục + bắt đầu code |
