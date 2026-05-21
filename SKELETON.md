<<<<<<< HEAD
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
=======
# SKELETON — Blueprint toàn bộ dự án Roguelike Rune Crafting

> Dùng file này để prompt Gemini/Gemma generate code từng phần.
> Mỗi section có: tên file, import, class/method, và mô tả logic cần làm.

---

## Cấu trúc thư mục

```
DOANOOP/
├── main.py
├── requirements.txt                  # pygame-ce>=2.4.0
├── logic/
│   ├── entities/
│   │   ├── status_effect.py          # ✅ ĐÃ VIẾT
│   │   ├── xp_orb.py
│   │   ├── bullet.py
│   │   ├── player.py
│   │   ├── enemy.py
│   │   └── boss.py
│   ├── rune/
│   │   ├── rune_component.py         # ✅ ĐÃ VIẾT
│   │   ├── rune_tree.py              # ✅ ĐÃ VIẾT
│   │   ├── elements/
│   │   │   ├── fire_rune.py          # ✅ ĐÃ VIẾT
│   │   │   ├── ice_rune.py
│   │   │   └── poison_rune.py
│   │   └── modifiers/
│   │       ├── spiral_modifier.py
│   │       ├── bounce_modifier.py
│   │       └── split_modifier.py
│   ├── wave/
│   │   └── wave_manager.py
│   └── leveling/
│       └── level_manager.py
└── ui/
    ├── game_loop.py
    ├── renderer.py
    ├── hud.py
    ├── input_handler.py
    └── screens/
        ├── main_menu.py
        ├── level_up_screen.py
        ├── game_over_screen.py
        └── win_screen.py
```

---

## PHẦN 1 — LOGIC (không import pygame)
>>>>>>> 3e15ae77a0ed8863193acdf98696434a388c7c55

---

### `logic/entities/xp_orb.py`

```python
class XPOrb:
    RADIUS = 8
<<<<<<< HEAD
    COLLECT_RADIUS = 40

    def check_collect(self, player_x, player_y) -> bool:
        # Euclidean dist <= COLLECT_RADIUS → alive=False, return True
=======
    COLLECT_RADIUS = 40  # player nhặt tự động khi trong bán kính này

    def __init__(self, x: float, y: float, value: int):
        self.x = x
        self.y = y
        self.radius = XPOrb.RADIUS
        self.value = value     # lượng XP cho player
        self.alive = True

    def check_collect(self, player_x: float, player_y: float) -> bool:
        # Trả về True nếu player đủ gần (dùng khoảng cách Euclidean)
        # Nếu True → set self.alive = False
        pass
>>>>>>> 3e15ae77a0ed8863193acdf98696434a388c7c55
```

---

### `logic/entities/bullet.py`

```python
<<<<<<< HEAD
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
=======
import math

class Bullet:
    BASE_SPEED = 400     # pixel/giây
    RADIUS = 6
    LIFETIME = 3.0       # giây tự hủy
    MAX_BOUNCE = 2       # số lần nảy tối đa (BounceModifier dùng)

    def __init__(self, x, y, target_x, target_y,
                 damage: float, rune_tree=None):
        self.x = float(x)
        self.y = float(y)
        self.radius = Bullet.RADIUS
        self.damage = damage
        self.rune_tree = rune_tree   # RuneTree | None
        self.alive = True
        self.elapsed = 0.0

        # Tính vector vận tốc hướng về target (normalize rồi nhân speed)
        # self.vx, self.vy = ...

        # State dùng bởi các Modifier
        self.spiral_angle = 0.0   # SpiralModifier xoay vận tốc mỗi frame
        self.bounce_count = 0     # BounceModifier đếm số lần đã nảy
        self.bounce_redirect = False  # BounceModifier set True để không bị kill ngay

        # Stack count — số lần cùng loại element được chọn
        # Dùng khi on_hit để nhân damage/duration
        self.element_stack = 1    # mặc định 1, RuneTree tính khi build

    def update(self, dt: float) -> None:
        # 1. Gọi rune_tree.on_update(self, dt) nếu có
        # 2. Di chuyển: self.x += self.vx * dt, self.y += self.vy * dt
        # 3. Cộng elapsed, nếu >= LIFETIME thì self.alive = False
        pass

    def on_hit(self, enemy, context: dict) -> None:
        # 1. Reset bounce_redirect = False
        # 2. Gọi rune_tree.on_hit(self, enemy, context) nếu có
        # 3. Nếu bounce_redirect vẫn False → self.alive = False
        pass

    def redirect(self, new_vx: float, new_vy: float) -> None:
        # BounceModifier gọi hàm này để đổi hướng đạn
        # Set self.vx, self.vy mới
        # Set self.bounce_redirect = True (giữ bullet sống)
        # Reset self.elapsed = 0
        pass
>>>>>>> 3e15ae77a0ed8863193acdf98696434a388c7c55
```

---

### `logic/entities/player.py`

```python
<<<<<<< HEAD
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
=======
import math

class Player:
    RADIUS = 15
    BASE_HP = 100
    BASE_SPEED = 200       # pixel/giây
    BASE_FIRE_RATE = 0.5   # giây giữa 2 lần bắn
    BASE_DAMAGE = 20

    def __init__(self, x=0.0, y=0.0):
        self.x = float(x)
        self.y = float(y)
        self.radius = Player.RADIUS
        self.max_hp = Player.BASE_HP
        self.hp = float(Player.BASE_HP)
        self.speed = Player.BASE_SPEED
        self.fire_rate = Player.BASE_FIRE_RATE
        self.damage = Player.BASE_DAMAGE
        self.alive = True
        self.fire_timer = 0.0   # đếm ngược, khi <= 0 mới được bắn

        # Rune Tree — import ở đây tránh circular import
        from logic.rune.rune_tree import RuneTree
        self.rune_tree = RuneTree()

        # Leveling
        self.level = 1
        self.xp = 0
        self.xp_to_next = 30   # XP cần lên cấp, tăng 1.4x mỗi cấp

    def update(self, dt: float, move_x: float, move_y: float) -> None:
        # move_x, move_y: từ input (-1, 0, 1)
        # 1. Normalize vector nếu (move_x, move_y) != (0, 0)
        # 2. self.x += direction.x * self.speed * dt
        # 3. self.y += direction.y * self.speed * dt
        # 4. Giảm fire_timer nếu > 0
        pass

    def can_fire(self) -> bool:
        return self.fire_timer <= 0

    def reset_fire_timer(self) -> None:
        self.fire_timer = self.fire_rate

    def take_damage(self, amount: float) -> None:
        # Trừ HP, clamp về 0, set alive=False nếu hp<=0
        pass

    def add_xp(self, amount: int) -> bool:
        # Cộng XP, nếu đủ → level += 1, tính xp_to_next mới, trả về True
        # Công thức xp_to_next mới = int(xp_to_next * 1.4)
        pass

    def get_hp_ratio(self) -> float:
        return self.hp / self.max_hp

    def get_xp_ratio(self) -> float:
        return self.xp / self.xp_to_next
>>>>>>> 3e15ae77a0ed8863193acdf98696434a388c7c55
```

---

### `logic/entities/enemy.py`

```python
<<<<<<< HEAD
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
=======
import math
from logic.entities.status_effect import StatusEffect

class Enemy:
    RADIUS = 20
    BASE_HP = 50
    BASE_SPEED = 80
    XP_VALUE = 10

    def __init__(self, x: float, y: float):
        self.x = float(x)
        self.y = float(y)
        self.radius = Enemy.RADIUS
        self.max_hp = Enemy.BASE_HP
        self.hp = float(Enemy.BASE_HP)
        self.speed = Enemy.BASE_SPEED
        self.xp_value = Enemy.XP_VALUE
        self.alive = True
        self.status_effects: list[StatusEffect] = []

    def update(self, dt: float, player_x: float, player_y: float) -> None:
        # 1. Cập nhật và dọn status_effects hết hạn
        # 2. Tính slow_factor tổng hợp từ các effect loại 'slow'
        #    (lấy giá trị nhỏ nhất, mặc định 1.0)
        # 3. Tính hướng đến player (normalize), di chuyển với speed * slow_factor
        pass

    def take_damage(self, amount: float) -> None:
        # Trừ HP, set alive=False nếu hp<=0
        pass

    def add_status(self, effect: StatusEffect) -> None:
        # Nếu đã có effect cùng loại → refresh remaining (lấy max)
        # Nếu chưa có → append vào list
        pass

    def drop_xp(self):
        # Import XPOrb ở đây để tránh circular import
        # Trả về XPOrb(self.x, self.y, self.xp_value)
        pass

    def get_hp_ratio(self) -> float:
        return self.hp / self.max_hp
>>>>>>> 3e15ae77a0ed8863193acdf98696434a388c7c55
```

---

### `logic/entities/boss.py`

```python
<<<<<<< HEAD
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
=======
import math
from logic.entities.enemy import Enemy

class Boss(Enemy):
    """
    Boss kế thừa Enemy, có 3 skill riêng:
    1. Charge  : lao thẳng vào player tốc độ cao 1 giây
    2. AoE Slam: vùng damage tròn xung quanh boss trong AOE_DURATION giây
    3. Summon  : set cờ pending_summon=True → WaveManager spawn quái
    """
    RADIUS = 45
    BASE_HP = 1000
    BASE_SPEED = 50
    XP_VALUE = 500

    # Skill configs
    CHARGE_COOLDOWN = 8.0
    CHARGE_DURATION = 1.2
    CHARGE_SPEED = 350

    AOE_COOLDOWN = 12.0
    AOE_RADIUS = 120
    AOE_DAMAGE_PER_SEC = 40.0
    AOE_DURATION = 1.5

    SUMMON_COOLDOWN = 15.0
    SUMMON_COUNT = 4

    def __init__(self, x: float, y: float):
        super().__init__(x, y)
        self.radius = Boss.RADIUS
        self.max_hp = Boss.BASE_HP
        self.hp = float(Boss.BASE_HP)
        self.speed = Boss.BASE_SPEED
        self.xp_value = Boss.XP_VALUE

        # Charge state
        self.charge_cooldown_timer = 5.0   # đợi 5s trước lần đầu
        self.charge_timer = 0.0
        self.is_charging = False
        self.charge_target_x = 0.0
        self.charge_target_y = 0.0

        # AoE state
        self.aoe_cooldown_timer = 8.0
        self.aoe_active = False
        self.aoe_timer = 0.0

        # Summon state
        self.summon_cooldown_timer = 10.0
        self.pending_summon = False   # WaveManager đọc cờ này

    def update(self, dt: float, player_x: float, player_y: float) -> None:
        # 1. Cập nhật status_effects (giống Enemy)
        # 2. Tính slow_factor
        # 3. _update_charge(dt, player_x, player_y, slow_factor)
        # 4. _update_aoe(dt)
        # 5. _update_summon(dt)
        pass

    def _update_charge(self, dt, px, py, slow):
        # Nếu đang charge: lao về charge_target, đếm ngược charge_timer
        #   Khi hết timer hoặc đến nơi → is_charging = False, reset cooldown
        # Nếu không charge: đếm ngược cooldown, di chuyển bình thường về player
        #   Khi cooldown hết → bắt đầu charge (lưu vị trí player lúc này)
        pass

    def _update_aoe(self, dt):
        # Nếu aoe_active: đếm aoe_timer, khi hết → tắt, reset cooldown
        # Nếu không: đếm cooldown, khi hết → bật aoe_active
        pass

    def _update_summon(self, dt):
        # Đếm cooldown, khi hết → pending_summon = True, reset cooldown
        pass

    def check_aoe_hit(self, player_x: float, player_y: float) -> float:
        # Nếu aoe_active và player trong AOE_RADIUS → trả về AOE_DAMAGE_PER_SEC
        # Ngược lại trả về 0.0
        pass

    def check_charge_hit(self, player_x: float, player_y: float,
                         player_radius: float) -> float:
        # Nếu đang charge và khoảng cách <= radius+player_radius
        # Trả về damage (ví dụ 30), ngược lại 0
        pass
>>>>>>> 3e15ae77a0ed8863193acdf98696434a388c7c55
```

---

<<<<<<< HEAD
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
=======
### `logic/rune/elements/ice_rune.py`

```python
from logic.rune.rune_component import ElementRune
from logic.entities.status_effect import StatusEffect

class IceRune(ElementRune):
    """
    Rune Băng — làm chậm quái khi trúng đạn.
    Stack: chọn 2 lần → slow_factor giảm thêm (0.6 → 0.36).
    """
    SLOW_FACTOR = 0.6       # quái còn 60% tốc độ
    SLOW_DURATION = 3.0

    def on_hit(self, bullet, enemy, context: dict) -> None:
        # Tạo StatusEffect loại 'slow'
        # slow_factor = SLOW_FACTOR ** bullet.element_stack (stack mạnh hơn)
        # duration = SLOW_DURATION
        pass

    def get_display_name(self) -> str: return "Rune Băng"
    def get_description(self) -> str:
        return f"Làm chậm quái {int((1-self.SLOW_FACTOR)*100)}% trong {self.SLOW_DURATION}s"
    def get_color(self) -> tuple: return (100, 200, 255)
>>>>>>> 3e15ae77a0ed8863193acdf98696434a388c7c55
```

---

<<<<<<< HEAD
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
=======
### `logic/rune/elements/poison_rune.py`

```python
from logic.rune.rune_component import ElementRune
from logic.entities.status_effect import StatusEffect

class PoisonRune(ElementRune):
    """
    Rune Độc — rút máu từ từ.
    Stack: chọn 2 lần → poison_damage nhân đôi.
    """
    POISON_DAMAGE = 5.0     # HP/giây
    POISON_DURATION = 5.0

    def on_hit(self, bullet, enemy, context: dict) -> None:
        # Tạo StatusEffect loại 'poison'
        # damage_per_sec = POISON_DAMAGE * bullet.element_stack
        # duration = POISON_DURATION
        pass

    def get_display_name(self) -> str: return "Rune Độc"
    def get_description(self) -> str:
        return f"Độc {self.POISON_DAMAGE} HP/s trong {self.POISON_DURATION}s"
    def get_color(self) -> tuple: return (120, 255, 80)
```

---

### `logic/rune/modifiers/spiral_modifier.py`

```python
import math
from logic.rune.rune_component import ModifierRune

class SpiralModifier(ModifierRune):
    """
    Rune Xoắn Ốc — quay vận tốc đạn mỗi frame.
    Stack: chọn 2 lần → ROTATE_SPEED nhân đôi.
    """
    ROTATE_SPEED = 180.0   # độ/giây

    def __init__(self):
        super().__init__()
        self.stack = 1   # tăng khi player chọn lại

    def on_update(self, bullet, dt: float) -> None:
        # Mỗi frame: xoay vector (vx, vy) một góc nhỏ
        # angle_rad = math.radians(ROTATE_SPEED * self.stack * dt)
        # vx_new = vx*cos - vy*sin
        # vy_new = vx*sin + vy*cos
        # Cập nhật bullet.vx, bullet.vy
        pass

    def on_fire(self, bullet, context: dict) -> list:
        return []

    def get_display_name(self) -> str: return "Rune Xoắn Ốc"
    def get_description(self) -> str: return "Đạn bay theo quỹ đạo xoắn ốc"
    def get_color(self) -> tuple: return (200, 150, 255)
```

---

### `logic/rune/modifiers/bounce_modifier.py`

```python
import math
from logic.rune.rune_component import ModifierRune

class BounceModifier(ModifierRune):
    """
    Rune Nảy — đạn trúng quái rồi nảy sang quái gần nhất.
    Stack: chọn 2 lần → bounce_max tăng thêm MAX_BOUNCE.
    """
    MAX_BOUNCE = 2
    BOUNCE_SPEED = 420.0

    def __init__(self):
        super().__init__()
        self.stack = 1

    def on_hit(self, bullet, enemy, context: dict) -> None:
        # 1. Tính bounce_max = MAX_BOUNCE * self.stack
        # 2. Nếu bullet.bounce_count < bounce_max:
        #    a. Tìm quái gần nhất trong context['enemies'] (trừ enemy vừa trúng)
        #    b. Nếu tìm thấy: bullet.redirect(vx, vy về quái đó)
        #       bullet.bounce_count += 1
        #    c. Nếu không tìm thấy: không làm gì (bullet tự chết)
        pass

    def on_update(self, bullet, dt: float) -> None:
        # Sau khi redirect, bullet.bounce_redirect = True → game loop không kill
        # Sau 1 frame, bounce_redirect được reset trong bullet.on_hit
        pass

    def on_fire(self, bullet, context: dict) -> list:
        return []

    def get_display_name(self) -> str: return "Rune Nảy"
    def get_description(self) -> str: return f"Đạn nảy tối đa {self.MAX_BOUNCE} lần"
    def get_color(self) -> tuple: return (255, 220, 50)
```

---

### `logic/rune/modifiers/split_modifier.py`

```python
import math
from logic.rune.rune_component import ModifierRune

class SplitModifier(ModifierRune):
    """
    Rune Tách — khi bắn tạo thêm 2 viên đạn lệch ±SPLIT_ANGLE độ.
    Stack: chọn 2 lần → tạo thêm 4 viên thay vì 2.
    """
    SPLIT_ANGLE = 20.0   # độ lệch mỗi bên

    def __init__(self):
        super().__init__()
        self.stack = 1

    def on_fire(self, bullet, context: dict) -> list:
        # Tạo thêm (2 * self.stack) viên đạn mới:
        # Mỗi cặp lệch ±SPLIT_ANGLE * i so với hướng gốc
        # Clone bullet (vị trí giống, rune_tree giống, chỉ đổi vx/vy)
        # Trả về list[Bullet] mới
        pass

    def on_update(self, bullet, dt: float) -> None:
        pass

    def get_display_name(self) -> str: return "Rune Tách"
    def get_description(self) -> str: return "Bắn tạo thêm 2 viên đạn"
    def get_color(self) -> tuple: return (255, 180, 100)
>>>>>>> 3e15ae77a0ed8863193acdf98696434a388c7c55
```

---

### `logic/wave/wave_manager.py`

```python
<<<<<<< HEAD
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
=======
import random
import math

class WaveManager:
    """
    Quản lý spawn quái và boss.
    - Spawn theo thời gian: mỗi SPAWN_INTERVAL giây spawn 1 nhóm quái
    - Random spawn nhỏ: mỗi RANDOM_INTERVAL giây spawn 1 quái ngẫu nhiên
    - Boss: sau BOSS_WAVE waves hoặc BOSS_TIME giây
    """
    SPAWN_INTERVAL = 8.0     # giây giữa 2 đợt spawn chính
    SPAWN_COUNT_BASE = 3     # quái mỗi đợt ban đầu
    RANDOM_INTERVAL = 3.0    # giây random spawn nhỏ

    BOSS_WAVE = 4            # boss xuất hiện sau wave này
    BOSS_TIME = 7 * 60       # hoặc sau 7 phút

    WORLD_SPAWN_RADIUS = 700  # spawn ngoài vùng nhìn của player

    def __init__(self):
        self.wave = 0
        self.time_elapsed = 0.0
        self.spawn_timer = self.SPAWN_INTERVAL
        self.random_timer = self.RANDOM_INTERVAL
        self.boss_spawned = False
        self.boss_alive = False
        self.enemies: list = []   # game loop gán vào
        self.boss = None

    def update(self, dt: float, player_x: float, player_y: float,
               enemy_list: list, boss_ref) -> dict:
        """
        Trả về dict events:
        {
          'spawn_enemies': list[tuple(x,y)],   # vị trí spawn quái mới
          'spawn_boss': bool,                   # có spawn boss không
          'summon_enemies': int,                # số quái boss triệu hồi
        }
        """
        # 1. Cộng time_elapsed
        # 2. Đếm spawn_timer, khi hết → spawn nhóm quái, wave += 1
        #    số quái mỗi wave = SPAWN_COUNT_BASE + wave (tăng dần)
        # 3. Đếm random_timer, khi hết → spawn 1 quái ngẫu nhiên
        # 4. Kiểm tra boss trigger (wave >= BOSS_WAVE hoặc time >= BOSS_TIME)
        # 5. Nếu boss tồn tại và pending_summon=True → spawn summon
        # Trả về events dict
        pass

    def _random_spawn_pos(self, player_x: float, player_y: float) -> tuple:
        # Sinh vị trí spawn ngẫu nhiên xung quanh player (ngoài WORLD_SPAWN_RADIUS)
        # angle = random, x = player_x + cos(angle)*WORLD_SPAWN_RADIUS, ...
        pass

    def get_wave_info(self) -> str:
        if self.boss_spawned:
            return "BOSS"
        return f"Wave {self.wave}"
>>>>>>> 3e15ae77a0ed8863193acdf98696434a388c7c55
```

---

### `logic/leveling/level_manager.py`

```python
<<<<<<< HEAD
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
=======
import random

# Import tất cả Rune để tạo pool lựa chọn
from logic.rune.elements.fire_rune import FireRune
from logic.rune.elements.ice_rune import IceRune
from logic.rune.elements.poison_rune import PoisonRune
from logic.rune.modifiers.spiral_modifier import SpiralModifier
from logic.rune.modifiers.bounce_modifier import BounceModifier
from logic.rune.modifiers.split_modifier import SplitModifier

ALL_RUNES = [FireRune, IceRune, PoisonRune,
             SpiralModifier, BounceModifier, SplitModifier]

class LevelManager:
    """
    Quản lý việc chọn Rune khi lên cấp.
    - Tạo pool 3 Rune ngẫu nhiên để player chọn
    - Áp dụng Rune được chọn vào RuneTree của player
    """
    CHOICES_COUNT = 3   # số lựa chọn mỗi lần lên cấp

    def __init__(self):
        self.pending_level_up = False
        self.current_choices: list = []   # list RuneComponent instances

    def trigger_level_up(self) -> None:
        # Set pending_level_up = True
        # Tạo current_choices: chọn CHOICES_COUNT Rune ngẫu nhiên từ ALL_RUNES
        # Instantiate chúng (gọi constructor)
        pass

    def apply_choice(self, index: int, player) -> None:
        """
        Áp dụng Rune người chơi chọn vào player.rune_tree.
        index: 0, 1, hoặc 2
        """
        # rune = current_choices[index]
        # Nếu là ElementRune:
        #   Nếu player.rune_tree.element là cùng loại → element_stack += 1
        #   Ngược lại → player.rune_tree.set_element(rune)
        # Nếu là ModifierRune:
        #   Kiểm tra đã có modifier cùng loại chưa, nếu có → stack += 1
        #   Ngược lại → player.rune_tree.add_modifier(rune)
        # Set pending_level_up = False
        pass
>>>>>>> 3e15ae77a0ed8863193acdf98696434a388c7c55
```

---

<<<<<<< HEAD
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
=======
## PHẦN 2 — UI (import pygame được phép)

---

### `ui/input_handler.py`

```python
import pygame

class InputHandler:
    """Đọc input từ keyboard + mouse, trả về game commands."""

    def get_move_direction(self) -> tuple:
        # Đọc pygame.key.get_pressed()
        # W→(0,-1), S→(0,1), A→(-1,0), D→(1,0), kết hợp chéo
        # Trả về (move_x, move_y) chưa normalize
        pass

    def get_mouse_world_pos(self, camera_x: float, camera_y: float) -> tuple:
        # pygame.mouse.get_pos() → (screen_x, screen_y)
        # Chuyển sang world coords: world_x = screen_x + camera_x - SCREEN_W/2
        # Trả về (world_x, world_y)
        pass

    def is_firing(self) -> bool:
        # Trả về True nếu pygame.mouse.get_pressed()[0] (chuột trái)
        pass

    def process_events(self) -> str | None:
        # Duyệt pygame.event.get()
        # QUIT → trả về 'quit'
        # ESC → trả về 'pause'
        # Ngược lại → None
        pass
>>>>>>> 3e15ae77a0ed8863193acdf98696434a388c7c55
```

---

### `ui/renderer.py`

```python
<<<<<<< HEAD
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
=======
import pygame

SCREEN_W, SCREEN_H = 1280, 720

class Renderer:
    """
    Vẽ toàn bộ game world.
    Mỗi entity vẽ bằng colored shape mặc định.
    Nếu có sprite trong sprite_cache → dùng sprite.
    Camera: camera_x/y là world offset để player ở center màn hình.
    """

    # Màu mặc định
    COLOR_BG       = (30, 30, 30)
    COLOR_PLAYER   = (80, 180, 255)
    COLOR_ENEMY    = (220, 60, 60)
    COLOR_BOSS     = (180, 0, 200)
    COLOR_BULLET   = (255, 255, 100)
    COLOR_XP_ORB   = (100, 255, 150)
    COLOR_BURN     = (255, 120, 0)
    COLOR_SLOW     = (100, 200, 255)
    COLOR_POISON   = (120, 255, 80)

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.sprite_cache: dict[str, pygame.Surface] = {}

    def load_sprite(self, name: str, path: str, size: tuple) -> None:
        # Load ảnh từ path, scale về size, lưu vào sprite_cache[name]
        pass

    def world_to_screen(self, wx, wy, cam_x, cam_y) -> tuple:
        # sx = wx - cam_x + SCREEN_W/2
        # sy = wy - cam_y + SCREEN_H/2
        # Trả về (int(sx), int(sy))
        pass

    def draw_background(self, cam_x: float, cam_y: float) -> None:
        # Fill màu nền, vẽ grid đơn giản để thấy camera di chuyển
        pass

    def draw_player(self, player, cam_x, cam_y) -> None:
        # Vẽ circle màu COLOR_PLAYER tại vị trí player (convert world→screen)
        # Nếu có sprite 'player' trong cache → blit thay thế
        pass

    def draw_enemy(self, enemy, cam_x, cam_y) -> None:
        # Vẽ circle màu COLOR_ENEMY
        # Vẽ HP bar nhỏ phía trên enemy
        # Vẽ halo màu tương ứng nếu có status effect
        pass

    def draw_boss(self, boss, cam_x, cam_y) -> None:
        # Tương tự enemy nhưng to hơn + màu COLOR_BOSS
        # Nếu aoe_active → vẽ vòng tròn AOE_RADIUS màu đỏ mờ
        pass

    def draw_bullet(self, bullet, cam_x, cam_y) -> None:
        # Vẽ circle nhỏ màu COLOR_BULLET
        pass

    def draw_xp_orb(self, orb, cam_x, cam_y) -> None:
        # Vẽ hình thoi/circle nhỏ màu COLOR_XP_ORB
        pass

    def draw_all(self, player, enemies, boss, bullets, xp_orbs,
                 cam_x, cam_y) -> None:
        # Gọi draw_background → xp_orbs → enemies → boss → bullets → player
        pass
>>>>>>> 3e15ae77a0ed8863193acdf98696434a388c7c55
```

---

### `ui/hud.py`

```python
<<<<<<< HEAD
class HUD:
    def draw(self, player, wave_info):
        # HP bar (10,10) 220×20 màu đỏ
        # XP bar (10, 36) 220×14 màu xanh lá + "Lv.X"
        # Wave info góc phải trên
        # Chiêu active + Rune list: tên + màu + stack
        # Notification nếu inventory > 0: "[Tab] Mở Rune Builder (N rune chờ)"
=======
import pygame

SCREEN_W, SCREEN_H = 1280, 720

class HUD:
    """Vẽ giao diện: HP bar, XP bar, level, wave, rune tree hiện tại."""

    def __init__(self, screen: pygame.Surface, font: pygame.font.Font):
        self.screen = screen
        self.font = font

    def draw(self, player, wave_info: str) -> None:
        # HP bar: góc trái trên (10, 10), rộng 200, cao 20, màu đỏ
        # XP bar: bên dưới HP bar, màu xanh lá
        # Level: text "Lv.X" bên cạnh XP bar
        # Wave: text góc phải trên
        # Rune list: liệt kê các Rune trong player.rune_tree (màu của từng rune)
        pass
>>>>>>> 3e15ae77a0ed8863193acdf98696434a388c7c55
```

---

<<<<<<< HEAD
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
=======
### `ui/screens/main_menu.py`

```python
import pygame

SCREEN_W, SCREEN_H = 1280, 720

class MainMenu:
    """Màn hình chính: tiêu đề + nút Start."""

    def __init__(self, screen: pygame.Surface, font_big, font_small):
        self.screen = screen
        self.font_big = font_big
        self.font_small = font_small

    def draw(self) -> None:
        # Vẽ tiêu đề "RUNE CRAFT" ở giữa màn hình
        # Vẽ "Nhấn ENTER để bắt đầu" phía dưới
        pass

    def handle_event(self, event: pygame.event.Event) -> str | None:
        # ENTER / SPACE → trả về 'start'
        # QUIT → trả về 'quit'
        pass
>>>>>>> 3e15ae77a0ed8863193acdf98696434a388c7c55
```

---

<<<<<<< HEAD
## Combo Rune tham khảo

| Chiêu | L1 | L2 | R1 | R2 | Hiệu ứng |
|-------|----|----|----|----|----------|
| Chiêu 1 | Spiral | Fire | — | — | Đạn thường xoắn, trúng gây burn |
| Chiêu 2 | Bounce | Ice | — | — | Đạn thường nảy, trúng gây chill |
| Chiêu 3 | Split | Wind | — | — | Đạn tách, trúng knockback |
| Chiêu 1 | Spiral | Fire | Bounce | Ice | Đạn xoắn + nảy, trúng burn + chill |
=======
### `ui/screens/level_up_screen.py`

```python
import pygame

SCREEN_W, SCREEN_H = 1280, 720

class LevelUpScreen:
    """
    Màn hình lên cấp: hiển thị 3 Rune lựa chọn.
    Dừng game loop cho đến khi player chọn.
    """

    CARD_W, CARD_H = 200, 280
    CARD_GAP = 40

    def __init__(self, screen: pygame.Surface, font_big, font_small):
        self.screen = screen
        self.font_big = font_big
        self.font_small = font_small

    def draw(self, choices: list) -> None:
        # Vẽ overlay tối nền
        # Vẽ 3 card cạnh nhau ở giữa màn hình
        # Mỗi card: màu rune + tên + mô tả
        # Vẽ số 1/2/3 gợi ý phím bấm
        pass

    def handle_event(self, event: pygame.event.Event) -> int | None:
        # Phím 1 → trả về 0
        # Phím 2 → trả về 1
        # Phím 3 → trả về 2
        # Click vào card → trả về index tương ứng
        pass
```

---

### `ui/screens/game_over_screen.py`

```python
import pygame

SCREEN_W, SCREEN_H = 1280, 720

class GameOverScreen:
    def __init__(self, screen, font_big, font_small):
        self.screen = screen
        self.font_big = font_big
        self.font_small = font_small

    def draw(self, wave: int, time_survived: float) -> None:
        # "GAME OVER" lớn ở giữa
        # "Wave đạt được: X" + "Thời gian: X:XX"
        # "R để chơi lại / ESC thoát"
        pass

    def handle_event(self, event) -> str | None:
        # R → 'restart', ESC → 'quit'
        pass
```

---

### `ui/screens/win_screen.py`

```python
import pygame

SCREEN_W, SCREEN_H = 1280, 720

class WinScreen:
    def __init__(self, screen, font_big, font_small):
        self.screen = screen
        self.font_big = font_big
        self.font_small = font_small

    def draw(self, time_survived: float) -> None:
        # "CHIẾN THẮNG!" lớn ở giữa màu vàng
        # "Boss đã bị tiêu diệt!" + thời gian
        # "R để chơi lại / ESC thoát"
        pass

    def handle_event(self, event) -> str | None:
        # R → 'restart', ESC → 'quit'
        pass
```

---

### `ui/game_loop.py`

```python
import pygame
from logic.entities.player import Player
from logic.entities.enemy import Enemy
from logic.entities.boss import Boss
from logic.entities.bullet import Bullet
from logic.entities.xp_orb import XPOrb
from logic.wave.wave_manager import WaveManager
from logic.leveling.level_manager import LevelManager
from ui.renderer import Renderer, SCREEN_W, SCREEN_H
from ui.hud import HUD
from ui.input_handler import InputHandler
from ui.screens.main_menu import MainMenu
from ui.screens.level_up_screen import LevelUpScreen
from ui.screens.game_over_screen import GameOverScreen
from ui.screens.win_screen import WinScreen

FPS = 60
WORLD_CENTER_X = 0.0   # player spawn
WORLD_CENTER_Y = 0.0

class GameLoop:
    """
    State machine chính:
    MENU → PLAYING → LEVEL_UP → (PLAYING) → GAME_OVER | WIN
    """
    STATE_MENU      = 'menu'
    STATE_PLAYING   = 'playing'
    STATE_LEVEL_UP  = 'level_up'
    STATE_GAME_OVER = 'game_over'
    STATE_WIN       = 'win'

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Rune Craft Roguelike")
        self.clock = pygame.time.Clock()

        font_big   = pygame.font.SysFont(None, 64)
        font_small = pygame.font.SysFont(None, 28)

        self.renderer    = Renderer(self.screen)
        self.hud         = HUD(self.screen, font_small)
        self.input       = InputHandler()
        self.menu        = MainMenu(self.screen, font_big, font_small)
        self.levelup_scr = LevelUpScreen(self.screen, font_big, font_small)
        self.gameover    = GameOverScreen(self.screen, font_big, font_small)
        self.win_scr     = WinScreen(self.screen, font_big, font_small)

        self.state = self.STATE_MENU
        self._init_game_objects()

    def _init_game_objects(self):
        """Khởi tạo/reset toàn bộ objects cho 1 ván chơi mới."""
        self.player   = Player(WORLD_CENTER_X, WORLD_CENTER_Y)
        self.enemies: list[Enemy] = []
        self.boss: Boss | None = None
        self.bullets: list[Bullet] = []
        self.xp_orbs: list[XPOrb] = []
        self.wave_mgr  = WaveManager()
        self.level_mgr = LevelManager()
        self.time_played = 0.0

    def run(self) -> None:
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0

            # Xử lý event chung (QUIT)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                result = self._handle_event(event)
                if result == 'quit':
                    running = False

            self._update(dt)
            self._draw()
            pygame.display.flip()

        pygame.quit()

    def _handle_event(self, event) -> str | None:
        """Chuyển event đến màn hình hiện tại."""
        # STATE_MENU      → menu.handle_event
        # STATE_LEVEL_UP  → levelup_scr.handle_event → apply_choice
        # STATE_GAME_OVER → gameover.handle_event → restart hoặc quit
        # STATE_WIN       → win_scr.handle_event
        pass

    def _update(self, dt: float) -> None:
        """Cập nhật logic chỉ khi đang PLAYING."""
        if self.state != self.STATE_PLAYING:
            return

        self.time_played += dt

        # 1. Input → di chuyển player
        mx, my = self.input.get_move_direction()
        self.player.update(dt, mx, my)

        # 2. Bắn đạn nếu click và can_fire()
        if self.input.is_firing() and self.player.can_fire():
            wx, wy = self.input.get_mouse_world_pos(
                self._camera_x(), self._camera_y())
            self._spawn_bullet(wx, wy)
            self.player.reset_fire_timer()

        # 3. Update enemies + boss
        for e in self.enemies:
            e.update(dt, self.player.x, self.player.y)
        if self.boss:
            self.boss.update(dt, self.player.x, self.player.y)

        # 4. Update bullets (áp dụng rune on_update)
        for b in self.bullets:
            b.update(dt)

        # 5. Collision: bullet ↔ enemy/boss
        self._handle_bullet_collisions()

        # 6. Collision: player ↔ enemy (damage player)
        self._handle_enemy_player_collision(dt)

        # 7. Boss AoE damage
        if self.boss and self.boss.aoe_active:
            dmg = self.boss.check_aoe_hit(self.player.x, self.player.y)
            if dmg:
                self.player.take_damage(dmg * dt)

        # 8. XP orbs
        for orb in self.xp_orbs:
            if orb.check_collect(self.player.x, self.player.y):
                leveled = self.player.add_xp(orb.value)
                if leveled:
                    self.level_mgr.trigger_level_up()
                    self.state = self.STATE_LEVEL_UP

        # 9. Wave manager
        events = self.wave_mgr.update(
            dt, self.player.x, self.player.y, self.enemies, self.boss)
        self._process_wave_events(events)

        # 10. Dọn dẹp dead objects
        self._cleanup()

        # 11. Kiểm tra game over / win
        if not self.player.alive:
            self.state = self.STATE_GAME_OVER
        if self.boss and not self.boss.alive:
            self.state = self.STATE_WIN

    def _spawn_bullet(self, target_x: float, target_y: float) -> None:
        # Tạo Bullet(player.x, player.y, target_x, target_y, player.damage, player.rune_tree)
        # Gọi rune_tree.on_fire() → nhận thêm bullet phụ (Split)
        # Thêm vào self.bullets
        pass

    def _handle_bullet_collisions(self) -> None:
        # Với mỗi bullet còn alive, kiểm tra va chạm với enemies + boss
        # Va chạm: khoảng cách <= bullet.radius + target.radius
        # Gọi bullet.on_hit(target, context)
        # Trừ HP target (bullet.damage)
        # Nếu target chết → drop XP orb
        pass

    def _handle_enemy_player_collision(self, dt: float) -> None:
        # Nếu khoảng cách player ↔ enemy <= radii → player nhận 15 damage/s
        pass

    def _process_wave_events(self, events: dict) -> None:
        # Xử lý events từ WaveManager
        # spawn_enemies: tạo Enemy tại mỗi vị trí
        # spawn_boss: tạo Boss, lưu vào self.boss
        # summon_enemies: tạo N Enemy gần boss
        pass

    def _cleanup(self) -> None:
        # Xóa bullets, enemies, xp_orbs có alive=False
        pass

    def _camera_x(self) -> float:
        return self.player.x   # player luôn ở center

    def _camera_y(self) -> float:
        return self.player.y

    def _draw(self) -> None:
        if self.state == self.STATE_MENU:
            self.menu.draw()
        elif self.state == self.STATE_PLAYING:
            self.renderer.draw_all(
                self.player, self.enemies, self.boss,
                self.bullets, self.xp_orbs,
                self._camera_x(), self._camera_y())
            self.hud.draw(self.player, self.wave_mgr.get_wave_info())
        elif self.state == self.STATE_LEVEL_UP:
            self.renderer.draw_all(
                self.player, self.enemies, self.boss,
                self.bullets, self.xp_orbs,
                self._camera_x(), self._camera_y())
            self.hud.draw(self.player, self.wave_mgr.get_wave_info())
            self.levelup_scr.draw(self.level_mgr.current_choices)
        elif self.state == self.STATE_GAME_OVER:
            self.gameover.draw(self.wave_mgr.wave, self.time_played)
        elif self.state == self.STATE_WIN:
            self.win_scr.draw(self.time_played)
```

---

### `main.py`

```python
from ui.game_loop import GameLoop

if __name__ == "__main__":
    game = GameLoop()
    game.run()
```

---

## Prompt mẫu cho Gemini

Dùng từng section trên, copy vào Gemini kèm đoạn:

> "Hãy implement đầy đủ các method có comment `pass` trong đoạn code Python sau.
> Không thay đổi tên class/method/attribute. Giữ nguyên import.
> Thêm comment tiếng Việt giải thích logic."

Ưu tiên implement theo thứ tự: `status_effect` → `xp_orb` → `bullet` → `player` → `enemy` → `boss` → Elements → Modifiers → Managers → UI screens → `game_loop`.
>>>>>>> 3e15ae77a0ed8863193acdf98696434a388c7c55
