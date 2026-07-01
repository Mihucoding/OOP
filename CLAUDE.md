# CLAUDE.md — Đồ Án Roguelike Rune Crafting

> **Cập nhật lần cuối**: 2026-05-20

---

## Dự án

**Tên**: 2D Top-down Survival Roguelike — Rune Crafting System  
**Ngôn ngữ**: Python 3.11 + Pygame-CE  
**Resolution**: 1280 × 720  
**Trình độ**: Sinh viên năm 1 — comment tiếng Việt, code rõ ràng  
**Mục tiêu OOP**: Composite Pattern · Open/Closed · Composition over Inheritance

---

## Quy tắc bất biến

1. `logic/` **KHÔNG** import pygame hoặc bất kỳ thứ gì từ `ui/`
2. `ui/` CÓ THỂ import từ `logic/`
3. Mỗi Rune = 1 file riêng trong `elements/` hoặc `modifiers/`
4. `Bullet` nhận `RuneTree` lúc runtime — không subclass theo loại đạn
5. Thêm Rune mới = thêm class mới, **không sửa** `RuneComponent`, `Bullet`
6. `RuneTree.on_hit` set tạm `bullet.element_stack` per element → mỗi element stack độc lập
7. Chọn **2 hệ bắt buộc** đầu ván (màn `SkillSelectScreen`) → mỗi hệ = 1 chiêu; lõi slot 0 tự điền + **khóa cứng** (`RuneSlot.locked`), chỉ gắn modifier vào nhánh
8. Tinh chỉnh UI builder/skill-select qua `ui/rune_ui_config.py` (board size, node reach, link width, element registry) — không sửa code vẽ

---

## Thông số đã chốt

| Mục | Giá trị |
|-----|---------|
| Element Rune | 4: FireRune, IceRune, LightningRune, WindRune |
| Chiêu | **2** — chọn 2 hệ khác nhau đầu ván (swap Q/E), lõi khóa cứng |
| Modifier Rune | 4: SpiralModifier, BounceModifier, SplitModifier, HasteRune |
| Passive Rune | HasteRune (giảm cooldown chiêu) |
| Rune slots | Slot 0 (Hệ chính, element — khóa) + L1/L2/R1/R2 (modifier) |
| Same-element stack | Cùng element với Slot 0 có thể vào nhánh → tăng element_stack |
| Chọn hệ | `SkillSelectScreen` sau Main Menu — bắt buộc 2 hệ khác nhau |
| Config UI | `ui/rune_ui_config.py` — board/node/link/element registry |
| Rune Builder | Tab → [Ability panel] + selector 2 crystal (Q/E) + Tree Canvas |
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
| Thua | HP = 0 |
| Thắng | Boss chết |

---

## Trạng thái hiện tại

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

---

## Lịch sử quyết định

| Ngày | Quyết định | Lý do |
|------|-----------|-------|
| 2026-04-30 | Python + Pygame-CE | SV năm 1, quen thuộc |
| 2026-04-30 | Composite Pattern cho Rune | Yêu cầu đề bài OOP |
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
| 2026-07-01 | UI builder theo phong cách Watcher's Heart | Board lục giác dày, mũi tên, animation morph, icon sprite |
| 2026-07-01 | Chọn 2 hệ đầu ván (SkillSelectScreen) | Mỗi hệ = 1 chiêu, lõi khóa cứng; element bắt buộc |
| 2026-07-01 | 3 chiêu → 2 chiêu | Khớp mô hình chọn-2-hệ, swap Q/E |
| 2026-07-01 | `ui/rune_ui_config.py` | Config-driven: chỉnh board/node/link/element 1 nơi |
| 2026-07-01 | Board + node/nối supersample smoothscale | Anti-alias cho nét mịn, viền mảnh + glow mềm |
| 2026-07-01 | Cấu trúc slot per-element (Fire 5 mod/3 nhánh) | `slot_defs_for_rune()`; các hệ khác giữ 4 mod/2 nhánh |

---

## Test coverage

| Test suite | Kết quả |
|-----------|---------|
| Logic imports | ✅ PASSED |
| UI imports | ✅ PASSED |
| Combo tests (61 cases) | ✅ 61/61 PASSED |
| Builder slot tests | ✅ PASSED |
| SpellBuild/RuneSlots tests | ✅ 32 unittest PASSED |
