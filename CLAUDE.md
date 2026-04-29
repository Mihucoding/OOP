# CLAUDE.md — Đồ Án Roguelike Rune Crafting

> **Tự động cập nhật**: Cuối mỗi prompt, Claude PHẢI cập nhật file này.

---

## Dự án

**Tên**: 2D Top-down Survival Roguelike — Rune Crafting System
**Ngôn ngữ**: Python + Pygame-CE
**Resolution**: 1280 × 720
**Trình độ**: Sinh viên năm 1 — comment tiếng Việt, code rõ ràng
**Mục tiêu OOP**: Composite Pattern · Open/Closed · Composition over Inheritance

---

## Quy tắc bất biến

1. `logic/` **KHÔNG** import pygame hoặc bất kỳ thứ gì từ `ui/`
2. `ui/` CÓ THỂ import từ `logic/`
3. Mỗi Rune = 1 file riêng trong `elements/` hoặc `modifiers/`
4. `Bullet` nhận `RuneTree` lúc runtime — không subclass theo loại đạn
5. Thêm Rune mới = thêm class mới, **không sửa** `RuneComponent`, `RuneTree`, `Bullet`

---

## Thông số đã chốt

| Mục | Giá trị |
|-----|---------|
| Rune Element | 3: FireRune, IceRune, PoisonRune |
| Rune Modifier | 3: SpiralModifier, BounceModifier, SplitModifier |
| Rune tree depth | Tối đa 3 cấp |
| Rune stack | Có — cùng Rune chọn nhiều lần được |
| Lựa chọn lên cấp | 3 Rune ngẫu nhiên |
| Wave | Theo thời gian + random nhỏ |
| Boss trigger | Wave 3–4 HOẶC 7–8 phút |
| Boss skills | Charge, AoE Slam, Summon |
| Map | Cố định, player center, camera scroll |
| Thua | HP = 0 |
| Thắng | Boss chết |

---

## Trạng thái hiện tại

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

---

## Lịch sử quyết định

| Ngày | Quyết định | Lý do |
|------|-----------|-------|
| 2026-04-30 | Python + Pygame-CE | SV năm 1, quen thuộc |
| 2026-04-30 | Composite Pattern cho Rune | Yêu cầu đề bài OOP |
| 2026-04-30 | Tách logic/ + ui/ | Đề bài yêu cầu 2 phần |
| 2026-04-30 | ElementRune = leaf, ModifierRune = composite | Clean Composite Pattern |
| 2026-04-30 | Bullet nhận RuneTree runtime | Composition over Inheritance |
| 2026-04-30 | Camera = world offset đơn giản | Phù hợp SV năm 1 |
| 2026-04-30 | bullet.element_stack cho stack rune | Đơn giản, không cần đếm lại cây |
| 2026-04-30 | Boss.pending_summon cờ cho WaveManager | Tách biệt logic boss và spawn |
| 2026-04-30 | SKELETON.md cho Gemini/Gemma | Tiết kiệm token Claude |
