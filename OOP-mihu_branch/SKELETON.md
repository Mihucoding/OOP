# SKELETON — Blueprint dự án Roguelike Rune Crafting

> **Cập nhật**: 2026-05-20  
> Tất cả file đã được implement đầy đủ.  
> File này ghi lại interface, luồng dữ liệu và quyết định thiết kế để tham khảo.

---

## Trạng thái file

| File | Trạng thái |
|------|-----------|
| `logic/entities/status_effect.py` | ✅ Stacks + chill + stun |
| `logic/entities/xp_orb.py` | ✅ |
| `logic/entities/bullet.py` | ✅ vx/vy + update + on_hit + redirect |
| `logic/entities/player.py` | ✅ inventory + 3 SpellBuild + active spell |
| `logic/entities/enemy.py` | ✅ slow_factor < 1.0 cho mọi effect |
| `logic/entities/ranged_enemy.py` | ✅ Stop 350px + fire 2s/lần |
| `logic/entities/enemy_bullet.py` | ✅ |
| `logic/entities/boss.py` | ✅ Charge + AoE + Summon |
| `logic/rune/rune_component.py` | ✅ ABC |
| `logic/rune/rune_tree.py` | ✅ Base Spell + Element/Modifier runtime |
| `logic/rune/rune_slots.py` | ✅ Core + 2 trái/2 phải |
| `logic/rune/elements/fire_rune.py` | ✅ |
| `logic/rune/elements/ice_rune.py` | ✅ chill |
| `logic/rune/elements/lightning_rune.py` | ✅ stun + instant dmg |
| `logic/rune/elements/wind_rune.py` | ✅ knockback + slow |
| `logic/rune/elements/poison_rune.py` | ✅ (không trong pool) |
| `logic/rune/modifiers/spiral_modifier.py` | ✅ |
| `logic/rune/modifiers/bounce_modifier.py` | ✅ |
| `logic/rune/modifiers/split_modifier.py` | ✅ |
| `logic/rune/modifiers/haste_rune.py` | ✅ Passive CDR -20%/stack |
| `logic/wave/wave_manager.py` | ✅ BOSS_WAVE=8, 15s interval |
| `logic/leveling/level_manager.py` | ✅ mix Rune + StatUpgrade |
| `logic/leveling/stat_upgrade.py` | ✅ 8 stats × 5 rarity |
| `logic/abilities/ultimate/ultimate_base.py` | ✅ ABC + factory |
| `logic/abilities/ultimate/fire_nova.py` | ✅ AoE burn + pushback |
| `logic/abilities/ultimate/ice_blizzard.py` | ✅ freeze 3s |
| `logic/abilities/ultimate/lightning_storm.py` | ✅ chain stun |
| `logic/abilities/ultimate/wind_cyclone.py` | ✅ pull + knockback |
| `logic/abilities/ultimate/shadow_nova.py` | ✅ AoE pure dmg |
| `logic/abilities/movement/dash_ability.py` | ✅ 200px, 3s CD |
| `ui/game_loop.py` | ✅ 6 states |
| `ui/renderer.py` | ✅ |
| `ui/hud.py` | ✅ notification rune mới |
| `ui/input_handler.py` | ✅ |
| `ui/screens/main_menu.py` | ✅ |
| `ui/screens/level_up_screen.py` | ✅ |
| `ui/screens/game_over_screen.py` | ✅ |
| `ui/screens/win_screen.py` | ✅ |
| `ui/screens/rune_builder_screen.py` | ✅ Inventory + 3 chiêu + 4-slot canvas |

---

## PHẦN 1 — LOGIC

---

### `logic/entities/status_effect.py`

```python
class StatusEffect:
    # effect_type: 'burn' | 'chill' | 'slow' | 'stun' | 'poison'
    # stacks: 1-5, max_stacks: 5
    # slow_factor: 1.0 = bình thường, 0.0 = đứng yên

    def update(self, enemy, dt) -> None:
        # burn 5 stacks → 5% max_hp/s
        # chill → slow_factor = 1.0 - stacks/5.0
        # còn lại → damage_per_sec * dt

    def is_expired(self) -> bool: ...
```

---

### `logic/entities/xp_orb.py`

```python
class XPOrb:
    RADIUS = 8
    COLLECT_RADIUS = 40

    def check_collect(self, player_x, player_y) -> bool:
        # Euclidean dist <= COLLECT_RADIUS → alive=False, return True
```

---

### `logic/entities/bullet.py`

```python
class Bullet:
    BASE_SPEED = 400
    RADIUS = 6
    LIFETIME = 3.0
    MAX_BOUNCE = 2

    def __init__(self, x, y, target_x, target_y, damage, rune_tree=None):
        # vx, vy = normalize(target - pos) * BASE_SPEED
        # element_stack = 1  (set lại bởi game_loop từ primary element)

    def update(self, dt):
        # rune_tree.on_update(self, dt)
        # x += vx*dt, y += vy*dt
        # elapsed += dt → alive=False nếu >= LIFETIME

    def on_hit(self, enemy, context):
        # bounce_redirect = False
        # rune_tree.on_hit(self, enemy, context)
        # nếu bounce_redirect vẫn False → alive = False

    def redirect(self, new_vx, new_vy):
        # vx, vy = new values
        # bounce_redirect = True, elapsed = 0
```

---

### `logic/entities/player.py`

```python
class SpellBuild:
    BASE_FIRE_RATE = 0.5
    fire_timer: float    # cooldown riêng
    fire_rate:  float    # giảm được qua HasteRune / CDR

    def tick(dt): ...
    def can_fire() -> bool: ...
    def reset_fire_timer(): ...
    def rebuild_rune_tree(): ...
    def _recalculate_fire_rate(): ...   # đọc HasteRune trong slots

class Player:
    BASE_HP = 100; BASE_SPEED = 200; BASE_FIRE_RATE = 0.5; BASE_DAMAGE = 20

    # Stats cơ bản (nâng qua StatUpgrade)
    armor:    float   # % giảm damage nhận (tối đa 75%)
    hp_regen: float   # HP/s thụ động
    xp_range: float   # +px bán kính hút XP
    lucky:    float   # 0-100: crit + rarity + XP drops

    # Abilities
    ultimate_cooldown: float
    ultimate_timer:    float
    movement_ability:  DashAbility

    def get_crit_chance() -> float: ...   # lucky * 0.004 (max 0.4)
    def can_ultimate() -> bool: ...
    def reset_ultimate(): ...
    def take_damage(amount): ...          # áp armor trước khi trừ HP
    def update(dt, move_x, move_y): ...   # tick spells + ult + move ability + regen
```

---

### `logic/entities/enemy.py`

```python
class Enemy:
    def update(self, dt, player_x, player_y):
        # slow_factor = min(eff.slow_factor for eff if eff.slow_factor < 1.0)
        # di chuyển về player với speed * slow_factor

    def add_status(self, effect):
        # cùng loại → refresh remaining + tăng stacks (burn/chill)
        # khác loại → append

    def drop_xp(self) -> XPOrb: ...
```

---

### `logic/entities/ranged_enemy.py`

```python
class RangedEnemy(Enemy):
    STOP_DISTANCE = 350
    FIRE_RATE = 2.0

    def update(self, dt, player_x, player_y):
        # chỉ di chuyển nếu dist > STOP_DISTANCE
        # đếm fire_timer

    def can_fire(self) -> bool: ...
    def reset_fire_timer(self): ...
```

---

### `logic/entities/enemy_bullet.py`

```python
class EnemyBullet:
    SPEED = 220; RADIUS = 5; DAMAGE = 12.0; LIFETIME = 4.0

    def __init__(self, x, y, target_x, target_y):
        # vx, vy = normalize(target - pos) * SPEED

    def update(self, dt):
        # x += vx*dt, y += vy*dt
        # elapsed += dt → alive=False nếu >= LIFETIME
```

---

### `logic/entities/boss.py`

```python
class Boss(Enemy):
    # 3 skills với cooldown riêng

    def _update_charge(self, dt, px, py, slow):
        # charging: lao về charge_target với CHARGE_SPEED
        # không charge: di chuyển bình thường, đếm cooldown

    def _update_aoe(self, dt):
        # aoe_active: đếm aoe_timer → tắt khi hết
        # không active: đếm cooldown → bật

    def _update_summon(self, dt):
        # đếm cooldown → pending_summon = True

    def check_aoe_hit(self, player_x, player_y) -> float: ...
    def check_charge_hit(self, player_x, player_y, player_radius) -> float: ...
```

---

### `logic/rune/rune_component.py`

```python
class RuneComponent(ABC):       # interface gốc
class ElementRune(RuneComponent):   # leaf — chỉ on_hit
class ModifierRune(RuneComponent):  # composite — on_update + on_fire + children
```

---

### `logic/rune/rune_tree.py`

```python
class RuneTree:
    MAX_DEPTH = 3

    # Base Spell luôn bắn được, không cần Element chính
    # elements: list[ElementRune]  ← mọi Element trong cây chiêu
    # element (property) → elements[0]  ← backward compat
    # modifiers: list[ModifierRune]

    def add_element(self, elem): ...    # thêm element phụ
    def set_element(self, elem): ...    # thay thế toàn bộ = [elem]
    def add_modifier(self, mod, parent=None, depth=1) -> bool: ...

    def on_hit(self, bullet, enemy, context):
        # for elem in elements:
        #     bullet.element_stack = elem.element_stack  ← set tạm per-element
        #     elem.on_hit(bullet, enemy, context)
        # bullet.element_stack = original  ← phục hồi
        # traverse modifiers

    def on_update(self, bullet, dt): ...  # traverse modifiers
    def on_fire(self, bullet, context) -> list: ...  # traverse → Split returns bullets
    def is_ready(self) -> bool: ...  # luôn True vì có Base Spell
    def get_all_runes(self) -> list: ...  # elements + traverse modifiers
    def describe(self) -> str: ...  # "Đạn thường" nếu cây trống
```

---

### `logic/rune/rune_slots.py`

```python
# Mỗi chiêu có 5 slot (Hướng B):
# Slot 0 (Hệ chính, x=760, y=150) — 'element', optional, chỉ nhận ElementRune
# Slot 1 (L1, x=560, y=310) — 'modifier', parent=0, chỉ nhận ModifierRune, đặt ngay
# Slot 2 (R1, x=960, y=310) — 'modifier', parent=0, chỉ nhận ModifierRune, đặt ngay
# Slot 3 (L2, x=560, y=500) — 'modifier', parent=1, cần Slot 1 có rune
# Slot 4 (R2, x=960, y=500) — 'modifier', parent=2, cần Slot 2 có rune

class RuneSlot:
    id, parent_id, slot_type, x, y, rune

class RuneSlots:
    NODE_RADIUS = 38

    def can_place(self, slot_id, rune) -> bool:
        # slot trống + can_accept (element/modifier type check)
        # Slot 0 và Slot 1/2 (parent=0): đặt ngay không cần điều kiện
        # Slot 3/4: cần parent (1/2) có rune

    def is_active(self, slot_id) -> bool:
        # element slot: active nếu có rune
        # modifier Slot 1/2: active nếu có rune (Slot 0 không bắt buộc)
        # modifier Slot 3/4: active nếu có rune VÀ parent active

    def place(self, slot_id, rune) -> bool: ...
    def remove(self, slot_id): ...      # trả về rune cũ
    def swap(self, slot_id, rune): ...  # đổi nếu compatible

    def build_rune_tree(self) -> RuneTree:
        # reset _children của tất cả modifier
        # add mọi Element từ slot active
        # add Modifier; nếu parent là Modifier thì nối child, nếu không thì root
```

---

### `logic/rune/elements/`

```python
class FireRune(ElementRune):
    BURN_DAMAGE = 8.0; BURN_DURATION = 3.0
    # on_hit: StatusEffect('burn', dps=BURN_DAMAGE * element_stack, ...)

class IceRune(ElementRune):
    SLOW_FACTOR = 0.6; SLOW_DURATION = 3.0
    # on_hit: StatusEffect('chill', slow_factor=0.6**element_stack, ...)

class LightningRune(ElementRune):
    STUN_DURATION = 0.8; BONUS_DAMAGE = 15.0
    # on_hit: StatusEffect('stun', slow_factor=0.0, ...)
    #         enemy.take_damage(BONUS_DAMAGE * element_stack)

class WindRune(ElementRune):
    KNOCKBACK_DIST = 120.0; SLOW_FACTOR = 0.7; SLOW_DURATION = 2.0
    # on_hit: knockback theo hướng đạn (fallback vx/vy nếu dist=0)
    #         StatusEffect('slow', ...)
```

---

### `logic/rune/modifiers/`

```python
class SpiralModifier(ModifierRune):
    ROTATE_SPEED = 180.0; stack = 1
    # on_update: rotation matrix, angle = radians(ROTATE_SPEED * stack * dt)

class BounceModifier(ModifierRune):
    MAX_BOUNCE = 2; BOUNCE_SPEED = 420.0; stack = 1
    # on_hit: tìm nearest enemy (dist > 0) → bullet.redirect()
    #         bỏ qua enemy trùng vị trí bullet (dist=0)

class SplitModifier(ModifierRune):
    SPLIT_ANGLE = 20.0; stack = 1
    # on_fire: tạo 2*stack viên đạn ±SPLIT_ANGLE*i so với hướng gốc
```

---

### `logic/wave/wave_manager.py`

```python
class WaveManager:
    SPAWN_INTERVAL = 15.0; SPAWN_COUNT_BASE = 3
    RANDOM_INTERVAL = 8.0
    BOSS_WAVE = 8; BOSS_TIME = 12*60
    RANGED_CHANCE = 0.3  # 30% từ wave 2

    def update(self, dt, player_x, player_y, enemy_list, boss_ref) -> dict:
        # events = {
        #   'spawn_enemies': [(x, y, 'normal'|'ranged'), ...],
        #   'spawn_boss':    bool,
        #   'summon_enemies': int,
        # }
```

---

### `logic/leveling/level_manager.py`

```python
ALL_RUNES = [FireRune, IceRune, LightningRune, WindRune,
             SpiralModifier, BounceModifier, SplitModifier, HasteRune]

class LevelManager:
    def trigger_level_up(self, wave=0, player=None):
        # Mix Rune + StatUpgrade theo wave:
        # stat_count = min(2, 1 + wave//5)
        # Stat cards dùng player.lucky để boost rarity

    def apply_choice(self, index, player):
        # StatUpgrade → choice.apply(player) trực tiếp
        # Rune → player.add_to_inventory(rune)
```

---

### `logic/leveling/stat_upgrade.py`

```python
# 8 stats × 5 rarity: Common/Uncommon/Rare/Epic/Legendary
# Weights: 50/28/15/6/1% (lucky cao → shift về Rare+)

class StatUpgrade:
    stat_type: str   # 'max_hp'|'speed'|'damage'|'armor'|'hp_regen'|'xp_range'|'lucky'|'cdr'
    value:     int
    rarity:    str

    def apply(self, player): ...   # cộng trực tiếp vào player stats
    def get_color() -> tuple: ...  # màu theo rarity
    def get_value_text() -> str: ...

def generate_stat_upgrade(lucky=0.0) -> StatUpgrade: ...
```

---

### `logic/abilities/ultimate/`

```python
class UltimateAbility(ABC):
    COOLDOWN = 8.0; RADIUS = 200.0

    def activate(player, enemies, boss, context) -> dict:
        # Gọi _apply() trên targets trong RADIUS
        # Trả về visual_info {cx, cy, radius, color, duration}

    def _get_targets(player, enemies, boss) -> list: ...
    def _apply(player, targets, context): ...   # abstract

# 5 subclass: FireNova, IceBlizzard, LightningStorm, WindCyclone, ShadowNova
def get_ultimate_for_spell(spell) -> UltimateAbility:
    # Dựa theo type của slot0.rune
```

---

### `logic/abilities/movement/`

```python
class MovementAbility:
    COOLDOWN: float; NAME: str; COLOR: tuple
    timer: float

    def tick(dt): ...
    def is_ready() -> bool: ...
    def activate(player, move_x, move_y): ...   # abstract
    def reset(): ...

class DashAbility(MovementAbility):
    DASH_DIST = 200.0; COOLDOWN = 3.0
    # activate: player.x/y += direction * DASH_DIST
    # Tương lai: BlinkAbility (teleport cursor), GhostStep (iframe)
```

---

## PHẦN 2 — UI

---

### `ui/game_loop.py` — State Machine

```
States: MENU → PLAYING ⇄ RUNE_BUILDER → LEVEL_UP → GAME_OVER | WIN

Phím Tab: PLAYING ↔ RUNE_BUILDER
         builder._close(player) → player.rebuild_all_spells()

_update (chỉ PLAYING):
  1. player.update(dt, mx, my)
  2. bắn đạn nếu click + can_fire
  3. enemy + boss update
  4. RangedEnemy.can_fire → EnemyBullet spawn
  5. bullets + enemy_bullets update
  6. _handle_bullet_collisions
  7. enemy_bullet ↔ player collision
  8. _handle_enemy_player_collision (15 dmg/s contact)
  9. boss AoE check
  10. xp_orb collect → add_xp → level_up → STATE_LEVEL_UP
  11. wave_mgr.update → _process_wave_events
  12. _cleanup (filter alive=False)
  13. check game_over / win

_spawn_bullet(target_x, target_y):
  spell = player.get_active_spell()
  rune_tree = spell.rune_tree
  bullet = Bullet(player.pos, target, damage, rune_tree)
  extra = rune_tree.on_fire(bullet, context)
  bullets.extend([bullet] + extra)

_process_wave_events(events):
  spawn_enemies → Enemy hoặc RangedEnemy
  spawn_boss    → Boss(player.x + 650, player.y)
  summon_enemies → N Enemy xung quanh boss
```

---

### `ui/renderer.py`

```python
class Renderer:
    def world_to_screen(self, wx, wy, cam_x, cam_y) -> tuple:
        # sx = wx - cam_x + SCREEN_W/2

    def draw_all(self, player, enemies, boss, bullets, xp_orbs,
                 enemy_bullets, cam_x, cam_y):
        # background → xp_orbs → enemies → boss → enemy_bullets → bullets → player

    # Status halo: burn=orange, chill=light_blue, slow=blue, stun=yellow, poison=green
    # HP bar: đỏ tối → đỏ sáng (fill theo hp_ratio)
    # Boss: AoE vòng tròn đỏ mờ khi aoe_active
```

---

### `ui/screens/rune_builder_screen.py`

```python
class RuneBuilderScreen:
    # Left panel (0-290px): Inventory — list rune chưa đặt
    # Right area (290-1280px): nút Chiêu 1/2/3 + cây Base/L1/L2/R1/R2

    def draw(self, player, dt): ...
    def handle_event(self, event, player) -> bool:
        # Click Chiêu 1/2/3 → đổi player.active_spell_index
        # Click inventory → selected_rune, selected_inv_idx
        # Click empty valid slot → place + remove from inventory
        # Click occupied slot:
        #   có selected_rune → swap nếu compatible
        #   không selected → remove về inventory
        # ESC/Tab/Enter → _close(player) → return True

    def _close(self, player):
        # player.rebuild_all_spells()
        # reset selection
```

---

### `ui/screens/level_up_screen.py`

```python
class LevelUpScreen:
    CARD_W=210; CARD_H=290; CARD_GAP=50

    def draw(self, choices): ...  # 3 card + overlay tối + số phím 1/2/3
    def handle_event(self, event) -> int | None:
        # K_1→0, K_2→1, K_3→2
        # MOUSEBUTTONDOWN → index nếu click vào card
```

---

### `ui/hud.py`

```python
class HUD:
    def draw(self, player, wave_info):
        # HP bar (10,10) 220×20 màu đỏ
        # XP bar (10, 36) 220×14 màu xanh lá + "Lv.X"
        # Wave info góc phải trên
        # Chiêu active + Rune list: tên + màu + stack
        # Notification nếu inventory > 0: "[Tab] Mở Rune Builder (N rune chờ)"
```

---

## Luồng dữ liệu chính

```
InputHandler → move_x, move_y, firing, mouse_world
     ↓
Player.update → position
     ↓
WaveManager.update → events (spawn positions + types)
     ↓
GameLoop._process_wave_events → Enemy / RangedEnemy / Boss list
     ↓
Enemy.update → chase player (slow_factor từ status effects)
Boss.update  → Charge + AoE + Summon (pending_summon flag)
RangedEnemy  → can_fire → EnemyBullet spawn
     ↓
Bullet.update → rune_tree.on_update (Spiral xoay vx/vy)
     ↓
Collision detection:
  bullet ↔ enemy → bullet.on_hit → rune_tree.on_hit (ALL elements + mods)
                 → enemy.take_damage → drop XPOrb
  enemy_bullet ↔ player → player.take_damage
  enemy contact ↔ player → 15 dmg/s
     ↓
XPOrb.check_collect → player.add_xp → level_up → STATE_LEVEL_UP
     ↓
LevelManager.apply_choice → player.rune_inventory
     ↓
[Tab] RuneBuilderScreen → chọn Chiêu 1/2/3
     → spell.rune_slots.place/remove/swap
     → player.rebuild_all_spells → mỗi spell.rune_tree updated
     ↓
Renderer.draw_all → screen
HUD.draw → overlay
```

---

## Combo Rune tham khảo

| Chiêu | L1 | L2 | R1 | R2 | Hiệu ứng |
|-------|----|----|----|----|----------|
| Chiêu 1 | Spiral | Fire | — | — | Đạn thường xoắn, trúng gây burn |
| Chiêu 2 | Bounce | Ice | — | — | Đạn thường nảy, trúng gây chill |
| Chiêu 3 | Split | Wind | — | — | Đạn tách, trúng knockback |
| Chiêu 1 | Spiral | Fire | Bounce | Ice | Đạn xoắn + nảy, trúng burn + chill |
