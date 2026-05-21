# Tóm tắt trao đổi — Roguelike Rune Crafting

> Cập nhật: 2026-05-20  
> Mục đích: lưu lại mọi quyết định đã chốt để tiếp tục dễ dàng.

---

## Trạng thái hiện tại: HOÀN CHỈNH ✅

**Test**: 32/32 PASSED  
**Điều khiển**:

| Phím | Hành động |
|------|-----------|
| WASD | Di chuyển |
| Left click | Bắn chiêu active |
| Right click | Ultimate (cooldown 8s) |
| Space | Dash 200px (cooldown 3s) |
| Q / E | Chuyển chiêu trước/sau |
| Tab | Mở Rune Builder (dừng game) |
| ESC | Đóng màn hình hiện tại |

---

## Hệ thống Rune (Hướng B — đã chốt)

```
Slot 0: Hệ chính (optional ElementRune)
Slot 1/2: Modifier hoặc cùng element Slot 0 (stack booster)
Slot 3/4: Modifier hoặc cùng element Slot 0 (cần Slot 1/2)

Same-element stack:
  Slot 0: FireRune + Slot 1: FireRune → element_stack = 2 → burn x2
  Slot 1: SpiralModifier + Slot 2: FireRune → Spiral + Fire stack 2
```

---

## Hệ thống Lên Cấp (2 loại)

3 card mỗi lần lên cấp = mix Rune + StatUpgrade:
- Wave 0–4: 2 Rune + 1 Stat
- Wave 5+: 1 Rune + 2 Stat

**StatUpgrade rarity** (50/28/15/6/1%):

| Stat | Common | Legendary |
|------|--------|-----------|
| Max HP | +15 | +80 |
| Speed | +10 | +50 |
| Damage | +3 | +20 |
| Armor | +3% | +20% |
| HP Regen | +1/s | +8/s |
| XP Range | +30px | +150px |
| Lucky | +5 | +28 |
| CDR | -5% | -22% |

Lucky cao → shift rarity weight về Rare/Epic khi lên cấp.

---

## Hệ thống Ultimate

Right-click → kích hoạt dựa theo **Slot 0 element** của chiêu active:

| Element | Ultimate | Hiệu ứng |
|---------|----------|----------|
| FireRune | Fire Nova | AoE 220px, burn + pushback |
| IceRune | Ice Blizzard | AoE 240px, đóng băng 3s |
| LightningRune | Thunder Chain | 6 enemy, stun + 60 dmg |
| WindRune | Wind Cyclone | Hút vào + knockback |
| (trống) | Shadow Nova | AoE 180px, 50 dmg thuần |

Cooldown 8s (giảm được qua CDR stat).

---

## Hệ thống Movement

`Space` → **Dash** 200px theo hướng WASD (cooldown 3s).

Architecture mở rộng: `MovementAbility` base class  
→ Blink (teleport cursor), GhostStep (iframe) có thể thêm sau.

---

## Player Stats đầy đủ

```python
player.hp          # hiện tại
player.max_hp      # tăng qua stat
player.speed       # tăng qua stat
player.damage      # tăng qua stat
player.armor       # % giảm damage (max 75%)
player.hp_regen    # HP/s thụ động
player.xp_range    # +px bán kính hút XP
player.lucky       # 0-100: crit + rarity + XP drops
player.ultimate_cooldown   # giây (giảm qua CDR)
player.movement_ability    # DashAbility (mặc định)
```

Crit chance = `lucky × 0.4%` (tối đa 40%, 2× damage).

---

## Cấu trúc file mới (2026-05-20)

```
logic/
├── leveling/
│   └── stat_upgrade.py      # StatUpgrade + rarity pool
├── abilities/
│   ├── ultimate/
│   │   ├── ultimate_base.py  # ABC + get_ultimate_for_spell()
│   │   ├── fire_nova.py
│   │   ├── ice_blizzard.py
│   │   ├── lightning_storm.py
│   │   ├── wind_cyclone.py
│   │   └── shadow_nova.py
│   └── movement/
│       └── dash_ability.py   # MovementAbility + DashAbility
└── rune/modifiers/
    └── haste_rune.py         # passive CDR
```

---

## Điều chỉnh cân bằng game (2026-05-20)

| Thông số | Cũ | Mới |
|----------|----|-----|
| BOSS_WAVE | 4 | 8 |
| BOSS_TIME | 7 phút | 12 phút |
| SPAWN_INTERVAL | 8s | 15s |
| SPAWN_COUNT_BASE | 5 | 3 |
| RANDOM_INTERVAL | 5s | 8s |
| XP orb count | 1 | 3–5 (scatter + lucky) |
| XP magnet radius | 40px | 180px + xp_range |

---

## Gợi ý Phase 2 (chưa làm)

**Rune mới:**
- `LifestealRune` — Heal % damage gây ra
- `PiercingRune` — Đạn xuyên 1 enemy thêm
- `ExplosiveRune` — Nổ AoE nhỏ khi trúng

**Stats mới:**
- Bullet Speed, Bullet Size, Multi-shot

**Movement mới:**
- Blink (Shift → teleport cursor, 6s)
- GhostStep (F → iframe 1s, 8s)

**Combo detection:**
- Fire + Spiral → Burn spread sang enemy cạnh
- Ice + Bounce → Chill double
- Wind + Spiral → Knockback theo vòng xoắn
