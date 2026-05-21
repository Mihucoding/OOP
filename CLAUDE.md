# CLAUDE.md — Đồ Án Roguelike Rune Crafting

<<<<<<< HEAD
> **Cập nhật lần cuối**: 2026-05-20
=======
> **Tự động cập nhật**: Cuối mỗi prompt, Claude PHẢI cập nhật file này.
>>>>>>> 3e15ae77a0ed8863193acdf98696434a388c7c55

---

## Dự án

<<<<<<< HEAD
**Tên**: 2D Top-down Survival Roguelike — Rune Crafting System  
**Ngôn ngữ**: Python 3.11 + Pygame-CE  
**Resolution**: 1280 × 720  
**Trình độ**: Sinh viên năm 1 — comment tiếng Việt, code rõ ràng  
=======
**Tên**: 2D Top-down Survival Roguelike — Rune Crafting System
**Ngôn ngữ**: Python + Pygame-CE
**Resolution**: 1280 × 720
**Trình độ**: Sinh viên năm 1 — comment tiếng Việt, code rõ ràng
>>>>>>> 3e15ae77a0ed8863193acdf98696434a388c7c55
**Mục tiêu OOP**: Composite Pattern · Open/Closed · Composition over Inheritance

---

## Quy tắc bất biến

1. `logic/` **KHÔNG** import pygame hoặc bất kỳ thứ gì từ `ui/`
2. `ui/` CÓ THỂ import từ `logic/`
3. Mỗi Rune = 1 file riêng trong `elements/` hoặc `modifiers/`
4. `Bullet` nhận `RuneTree` lúc runtime — không subclass theo loại đạn
<<<<<<< HEAD
5. Thêm Rune mới = thêm class mới, **không sửa** `RuneComponent`, `Bullet`
6. `RuneTree.on_hit` set tạm `bullet.element_stack` per element → mỗi element stack độc lập
=======
5. Thêm Rune mới = thêm class mới, **không sửa** `RuneComponent`, `RuneTree`, `Bullet`
>>>>>>> 3e15ae77a0ed8863193acdf98696434a388c7c55

---

## Thông số đã chốt

| Mục | Giá trị |
|-----|---------|
<<<<<<< HEAD
| Element Rune | 4: FireRune, IceRune, LightningRune, WindRune |
| Chiêu riêng | 3: Chiêu 1, Chiêu 2, Chiêu 3 |
| Modifier Rune | 4: SpiralModifier, BounceModifier, SplitModifier, HasteRune |
| Passive Rune | HasteRune (giảm cooldown chiêu) |
| Rune slots | Slot 0 (Hệ chính, element) + L1/L2/R1/R2 (modifier) |
| Same-element stack | Cùng element với Slot 0 có thể vào nhánh → tăng element_stack |
| Rune Builder | Tab → [Inventory]/[Chỉ số] + Chiêu 1/2/3 + Tree Canvas |
| Lên cấp | 3 card mix Rune + StatUpgrade (tỉ lệ theo wave) |
| StatUpgrade rarity | 5 bậc: Common/Uncommon/Rare/Epic/Legendary (trọng số 50/28/15/6/1%) |
| Player stats | HP, Speed, Damage, Armor, HPRegen, Lucky, CDR, XPRange |
| Lucky | Crit chance + Rarity boost + Extra XP orbs |
| Ultimate | Right-click, từ Slot 0 element, cooldown 8s |
| Dash | Space, 200px, cooldown 3s |
| Boss trigger | Wave 8 HOẶC 12 phút |
| Wave interval | 15s / Spawn base 3 |
| StatusEffect | burn/chill (stacks) + slow + stun + poison |
| Enemy types | Enemy + RangedEnemy (30% từ wave 2) + Boss |
| Map | Vô hạn, player center, camera scroll |
=======
| Rune Element | 3: FireRune, IceRune, PoisonRune |
| Rune Modifier | 3: SpiralModifier, BounceModifier, SplitModifier |
| Rune tree depth | Tối đa 3 cấp |
| Rune stack | Có — cùng Rune chọn nhiều lần được |
| Lựa chọn lên cấp | 3 Rune ngẫu nhiên |
| Wave | Theo thời gian + random nhỏ |
| Boss trigger | Wave 3–4 HOẶC 7–8 phút |
| Boss skills | Charge, AoE Slam, Summon |
| Map | Cố định, player center, camera scroll |
>>>>>>> 3e15ae77a0ed8863193acdf98696434a388c7c55
| Thua | HP = 0 |
| Thắng | Boss chết |

---

## Trạng thái hiện tại

<<<<<<< HEAD
**Ngày cập nhật**: 2026-05-20  
**Giai đoạn**: **HOÀN CHỈNH** — toàn bộ logic + UI đã implement

### Tất cả file đã implement ✅

**Logic:**
- `logic/entities/status_effect.py`
- `logic/entities/xp_orb.py` — scatter + auto-magnet
- `logic/entities/bullet.py` — is_crit flag
- `logic/entities/player.py` — 3 SpellBuild + armor/regen/lucky/ultimate/dash
- `logic/entities/enemy.py` — drop_xp(lucky)
- `logic/entities/ranged_enemy.py`
- `logic/entities/enemy_bullet.py`
- `logic/entities/boss.py`
- `logic/rune/rune_component.py`
- `logic/rune/rune_tree.py`
- `logic/rune/rune_slots.py` — Slot 0 element + same-element stack
- `logic/rune/elements/fire_rune.py`
- `logic/rune/elements/ice_rune.py`
- `logic/rune/elements/lightning_rune.py`
- `logic/rune/elements/wind_rune.py`
- `logic/rune/elements/poison_rune.py` (không trong pool)
- `logic/rune/modifiers/spiral_modifier.py`
- `logic/rune/modifiers/bounce_modifier.py`
- `logic/rune/modifiers/split_modifier.py`
- `logic/rune/modifiers/haste_rune.py` — passive CDR
- `logic/wave/wave_manager.py` — timing đã điều chỉnh
- `logic/leveling/level_manager.py` — mix Rune + StatUpgrade
- `logic/leveling/stat_upgrade.py` — 8 stats × 5 rarity
- `logic/abilities/ultimate/ultimate_base.py`
- `logic/abilities/ultimate/fire_nova.py`
- `logic/abilities/ultimate/ice_blizzard.py`
- `logic/abilities/ultimate/lightning_storm.py`
- `logic/abilities/ultimate/wind_cyclone.py`
- `logic/abilities/ultimate/shadow_nova.py`
- `logic/abilities/movement/dash_ability.py`

**UI:**
- `ui/game_loop.py` — Q/E switch, Space dash, RMB ultimate, crit check
- `ui/renderer.py` — crit bullet, ultimate flash ring
- `ui/hud.py` — spell bar + cooldown slots (RMB/SPACE) + stats display
- `ui/input_handler.py`
- `ui/screens/main_menu.py`
- `ui/screens/level_up_screen.py` — Rune card + Stat card + rarity colors
- `ui/screens/game_over_screen.py`
- `ui/screens/win_screen.py`
- `ui/screens/rune_builder_screen.py` — tab Inventory/Chỉ số
=======
**Ngày cập nhật**: 2026-04-30
**Giai đoạn**: Skeleton hoàn chỉnh — đang implement từng file

### File đã viết hoàn chỉnh (Claude)
- [x] `SKELETON.md` — sườn toàn bộ project cho Gemini dùng
- [x] `requirements.txt`
- [x] `logic/rune/rune_component.py` — ABC Composite Pattern
- [x] `logic/rune/rune_tree.py` — RuneTree MAX_DEPTH=3
- [x] `logic/rune/elements/fire_rune.py` — FireRune
- [x] `logic/entities/status_effect.py` — StatusEffect

### File có skeleton trong SKELETON.md (→ Gemini implement)
- [ ] `logic/entities/xp_orb.py`
- [ ] `logic/entities/bullet.py`
- [ ] `logic/entities/player.py`
- [ ] `logic/entities/enemy.py`
- [ ] `logic/entities/boss.py`
- [ ] `logic/rune/elements/ice_rune.py`
- [ ] `logic/rune/elements/poison_rune.py`
- [ ] `logic/rune/modifiers/spiral_modifier.py`
- [ ] `logic/rune/modifiers/bounce_modifier.py`
- [ ] `logic/rune/modifiers/split_modifier.py`
- [ ] `logic/wave/wave_manager.py`
- [ ] `logic/leveling/level_manager.py`
- [ ] `ui/input_handler.py`
- [ ] `ui/renderer.py`
- [ ] `ui/hud.py`
- [ ] `ui/game_loop.py`
- [ ] `ui/screens/main_menu.py`
- [ ] `ui/screens/level_up_screen.py`
- [ ] `ui/screens/game_over_screen.py`
- [ ] `ui/screens/win_screen.py`
- [ ] `main.py`
>>>>>>> 3e15ae77a0ed8863193acdf98696434a388c7c55

---

## Lịch sử quyết định

| Ngày | Quyết định | Lý do |
|------|-----------|-------|
| 2026-04-30 | Python + Pygame-CE | SV năm 1, quen thuộc |
| 2026-04-30 | Composite Pattern cho Rune | Yêu cầu đề bài OOP |
<<<<<<< HEAD
| 2026-05-19 | 3 SpellBuild riêng | Mỗi chiêu có cây rune độc lập |
| 2026-05-19 | Rune → inventory → builder | Thủ công hơn, chiều sâu hơn |
| 2026-05-20 | Slot 0 element slot (Hướng B) | Nhánh chỉ Modifier, đơn giản hơn |
| 2026-05-20 | Same-element stack vào nhánh | Cho phép tăng element_stack qua nhánh |
| 2026-05-20 | Boss wave 4→8, 7→12 phút | Boss xuất hiện quá sớm |
| 2026-05-20 | Per-spell cooldown | Luân chiêu có ý nghĩa chiến thuật |
| 2026-05-20 | XP orb scatter + magnet | UX nhặt XP tốt hơn |
| 2026-05-20 | Q/E chuyển chiêu trong game | Không cần mở builder để switch |
| 2026-05-20 | HasteRune passive | Modifier không ảnh hưởng đạn |
| 2026-05-20 | 2 hệ thống lên cấp (Rune + Stats) | Chiều sâu gameplay tăng dần |
| 2026-05-20 | Lucky → crit + rarity + XP | 1 stat ảnh hưởng 3 cơ chế |
| 2026-05-20 | Ultimate từ Slot 0 element | Tận dụng element đã chọn, có ý nghĩa |
| 2026-05-20 | Dash = Space, MovementAbility base | Mở rộng Blink/GhostStep sau |
| 2026-05-20 | Stats panel trong Rune Builder | Player thấy chỉ số ngay trong builder |

---

## Test coverage

| Test suite | Kết quả |
|-----------|---------|
| Logic imports | ✅ PASSED |
| UI imports | ✅ PASSED |
| Combo tests (61 cases) | ✅ 61/61 PASSED |
| Builder slot tests | ✅ PASSED |
| SpellBuild/RuneSlots tests | ✅ 32 unittest PASSED |
=======
| 2026-04-30 | Tách logic/ + ui/ | Đề bài yêu cầu 2 phần |
| 2026-04-30 | ElementRune = leaf, ModifierRune = composite | Clean Composite Pattern |
| 2026-04-30 | Bullet nhận RuneTree runtime | Composition over Inheritance |
| 2026-04-30 | Camera = world offset đơn giản | Phù hợp SV năm 1 |
| 2026-04-30 | bullet.element_stack cho stack rune | Đơn giản, không cần đếm lại cây |
| 2026-04-30 | Boss.pending_summon cờ cho WaveManager | Tách biệt logic boss và spawn |
| 2026-04-30 | SKELETON.md cho Gemini/Gemma | Tiết kiệm token Claude |
>>>>>>> 3e15ae77a0ed8863193acdf98696434a388c7c55
