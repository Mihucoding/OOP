# Hướng dẫn chỉnh vị trí node cây Rune (lưới lục giác 17 điểm)

> Tài liệu này mô tả cách đặt / dời các node modifier của từng hệ bằng **số điểm lưới**.
> Cập nhật: 2026-07-01

---

## 1. Lưới lục giác 17 điểm

Mỗi hệ đặt node lên các **giao điểm** của lục giác, đánh số **0 → 16**:

```
              0
          1       2
       3      4      5
          6       7
       8      9      10
          11      12
       13     14     15
              16
```

- Đỉnh trên = `0`, đỉnh dưới = `16`
- Cạnh trái = `3 - 8 - 13`, cạnh phải = `5 - 10 - 15`
- Cột giữa = `0 - 4 - 9 - 14 - 16`
- **Core (lõi hệ) luôn cố định ở điểm `0`**

Toạ độ 17 điểm khai báo trong [`ui/rune_ui_config.py`](ui/rune_ui_config.py) → `GRID_POINTS`
(dạng `điểm: (dx, dy)`, đơn vị theo bán kính board; `dx<0` = trái, `dy<0` = lên).

---

## 2. Cách đọc sơ đồ một hệ

Một hệ = **core (điểm 0) + tối đa 5 modifier**, mỗi modifier nằm trên 1 điểm lưới và
nối **về phía core**. Ký hiệu `A → B` nghĩa là *node ở điểm A là con của node ở điểm B*
(mũi tên chỉ từ A **lên** B, dồn về core).

Ví dụ Fire: `1→0, 2→0, 9→4→0` đọc là:
- điểm `1` là con của core (0)
- điểm `2` là con của core (0)
- điểm `4` là con của core (0); điểm `9` là con của `4`

---

## 3. Sơ đồ hiện tại của 4 hệ

| Hệ | Điểm dùng | Luồng nối (con → cha) |
|----|-----------|------------------------|
| 🔥 **Fire** | 0,1,2,4,9,7 | `1→0` · `2→0` · `4→0` · `9→4` · `7→2` |
| ❄️ **Ice** | 0,4,9,11,7,12 | `4→0` · `9→4` · `11→9` · `7→4` · `12→7` |
| 🌪️ **Wind** | 0,4,9,6,14,12 | `4→0` · `9→4` · `6→4` · `14→9` · `12→9` |
| ⚡ **Lightning** | 0,1,6,2,4,7 | `1→0` · `6→1` · `2→0` · `4→2` · `7→2` |

> Các điểm **không dùng** tự động hiện thành **chấm mờ** (giống node "locked" trong game gốc).
> Mũi tên luôn chỉ **về core**.

---

## 4. Cách sửa / thêm layout cho một hệ

Đổi vị trí node cần sửa **2 chỗ** (đã đồng bộ số slot):

### A. UI — vị trí + đường nối
File: [`ui/screens/rune_builder_screen.py`](ui/screens/rune_builder_screen.py) →
hàm `_tree_config_for_element`, trong dict `configs`:

```python
"fire": {
    "grid":  {0: 0, 1: 1, 2: 2, 3: 4, 4: 9},   # slot_id : số_điểm_lưới
    "edges": [(0, 1), (0, 2), (0, 3), (3, 4)],  # (cha, con) — mũi tên tự đảo về core
},
```

- `grid`: slot 0 luôn = điểm 0 (core). Các slot 1..N gán vào điểm bất kỳ trong 0-16.
- `edges`: cặp `(cha, con)` theo **slot_id** (không phải số điểm).

### B. Logic — quan hệ cha–con của slot
File: [`logic/rune/rune_slots.py`](logic/rune/rune_slots.py) → `SLOT_DEFS_<HỆ>`:

```python
SLOT_DEFS_FIRE = [
    (0, None, 'element',  760, 150),   # core (khóa)
    (1, 0,    'modifier', 600, 330),   # (slot_id, parent_slot_id, loại, x, y)
    (2, 0,    'modifier', 920, 330),
    (3, 0,    'modifier', 760, 330),
    (4, 3,    'modifier', 760, 510),   # slot 4 là con của slot 3
]
```

- `parent_slot_id` phải **khớp** với `edges` bên UI (con ← cha).
- Toạ độ `(x, y)` ở đây chỉ là placeholder — builder tự đặt lại theo `grid`.
- Số modifier có thể 1–5 tùy hệ (cả 4 hệ hiện đều đang dùng 5).

> ⚠️ Quy tắc đặt: slot con chỉ đặt được khi slot cha đã có rune
> (`RuneSlots.can_place`). Độ sâu tối đa = `RuneTree.MAX_DEPTH = 3` tầng.

---

## 5. Ví dụ: đổi Fire cho node 4 (điểm 9) sang điểm 12

1. UI: `"grid": {0:0, 1:1, 2:2, 3:4, 4:12}` (đổi `9`→`12`)
2. Logic: giữ nguyên `SLOT_DEFS_FIRE` (quan hệ cha–con không đổi)

→ Xong. Node cuối giờ nằm ở điểm 12 thay vì 9.

---

## 6. Các núm chỉnh khác (không liên quan grid)

Trong [`ui/rune_ui_config.py`](ui/rune_ui_config.py):

| Hằng số | Ý nghĩa |
|---------|---------|
| `BOARD_CENTER`, `BOARD_RADIUS` | Vị trí & độ to board |
| `NODE_REACH_SCALE` | Kéo node gần tâm (nối ngắn hơn) |
| `LINK_WIDTH_ACTIVE/INACTIVE`, `ARROW_SIZE` | Độ dày nối, cỡ mũi tên |

Vị trí **bộ chọn hệ** (2 crystal + Q/E): biến `y` trong
`_draw_top_spell_bar` ([`rune_builder_screen.py`](ui/screens/rune_builder_screen.py)) —
số nhỏ = đẩy lên cao hơn.
