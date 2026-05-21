"""
weapons.py — 3 loai vu khi: Fire / Ice / Lightning
"""
import math
import random
import pygame
from config import *


# ─────────────────────────────────────────────
#  WEAPON PROJECTILE
# ─────────────────────────────────────────────
class WeaponProjectile:
    """Dan cua vu khi weapon (doc lap voi SpellManager)."""

    def __init__(self, x, y, tx, ty, speed, radius, damage, color, status_effects=None, length=0, spell_manager=None, core_tree=None, trigger_spawn=True):
        self.x = float(x)
        self.y = float(y)
        self.radius = radius
        self.damage = damage
        self.color = color
        self.status_effects = status_effects or []
        self.alive = True
        self.lifetime = 3.0
        self.length = length # For Ice "long line"
        self.pierce = False
        self.hit_enemies = set() # Track enemies hit by this specific projectile
        self.spell_manager = spell_manager
        self.core_tree = core_tree
        self.speed = speed

        dx, dy = tx - x, ty - y
        dist = math.hypot(dx, dy)
        if dist == 0:
            self.vx, self.vy = 0.0, -speed
            self.dir_x, self.dir_y = 0.0, -1.0
            self.angle = -math.pi/2
        else:
            self.dir_x, self.dir_y = dx / dist, dy / dist
            self.vx = self.dir_x * speed
            self.vy = self.dir_y * speed
            self.angle = math.atan2(dy, dx)
            
        # Hook on_spawn (Skip if trigger_spawn is False to prevent infinite recursion with SplitRune)
        if self.core_tree and trigger_spawn:
            self.core_tree.on_spawn(self, self.spell_manager)

    def update(self, dt):
        if self.core_tree:
            self.core_tree.on_update(self, dt, self.spell_manager)
            # Re-apply velocity if direction changed
            self.vx = self.dir_x * self.speed
            self.vy = self.dir_y * self.speed

        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False

    def check_collision(self, target):
        return math.hypot(target.x - self.x, target.y - self.y) < target.radius + self.radius

    def draw(self, screen, cx, cy):
        sx, sy = int(self.x - cx), int(self.y - cy)
        if self.length > 0:
            # Draw as a long ice shard/line
            end_x = sx - int(math.cos(self.angle) * self.length)
            end_y = sy - int(math.sin(self.angle) * self.length)
            pygame.draw.line(screen, self.color, (sx, sy), (end_x, end_y), self.radius * 2)
            pygame.draw.circle(screen, (200, 240, 255), (sx, sy), self.radius)
        else:
            pygame.draw.circle(screen, self.color, (sx, sy), self.radius)
            # Vien sang
            bright = tuple(min(255, c + 80) for c in self.color)
            pygame.draw.circle(screen, bright, (sx, sy), self.radius, 2)


# ─────────────────────────────────────────────
#  FIRE WEAPON
# ─────────────────────────────────────────────
class FireWeapon:
    FIRE_RATE = 0.35
    SPEED = 520
    RADIUS = 8
    BASE_DMG = 8.0 # Reduced from previous high value

    def __init__(self, base_damage):
        self.base_damage = self.BASE_DMG
        self.fire_timer = 0.0
        self.pending_shots = []

    def update(self, dt, mouse_held, just_released, world_mx, world_my, player, all_enemies):
        self.fire_timer = max(0.0, self.fire_timer - dt)
        self.pending_shots = []

        if mouse_held and self.fire_timer <= 0:
            self.fire_timer = self.FIRE_RATE
            from status_effect import StatusEffect
            # Mỗi viên trúng sẽ thêm 1 stack (logic trong entities.py)
            self.pending_shots.append(WeaponProjectile(
                player.x, player.y, world_mx, world_my,
                self.SPEED, self.RADIUS, self.base_damage,
                (200, 100, 10),
                [StatusEffect('burn', self.base_damage * 0.4, 3.0)],
                spell_manager=player.spell_manager,
                core_tree=player.spell_manager.core_tree
            ))

    def draw_preview(self, screen, cx, cy, player):
        pass

    def draw_effects(self, screen, cx, cy):
        pass

    def draw_hud(self, screen, font, x, y):
        ratio = 1.0 - (self.fire_timer / self.FIRE_RATE) if self.FIRE_RATE > 0 else 1.0
        pygame.draw.rect(screen, (60, 10, 0), (x, y, 130, 10))
        pygame.draw.rect(screen, (255, 90, 10), (x, y, int(130 * ratio), 10))
        pygame.draw.rect(screen, (255, 180, 60), (x, y, 130, 10), 1)
        lbl = font.render("FIRE RATE", True, (255, 180, 60))
        screen.blit(lbl, (x, y - 16))


# ─────────────────────────────────────────────
#  ICE WEAPON
# ─────────────────────────────────────────────
class IceWeapon:
    MAX_CHARGE = 2.5
    SPEED = 450
    BASE_RADIUS = 6
    MAX_LENGTH = 120

    def __init__(self, base_damage):
        self.base_damage = base_damage
        self.charge_time = 0.0
        self.is_charging = False
        self.pending_shots = []

    def get_charge_ratio(self):
        return min(self.charge_time / self.MAX_CHARGE, 1.0)

    def update(self, dt, mouse_held, just_released, world_mx, world_my, player, all_enemies):
        self.pending_shots = []

        if mouse_held:
            self.is_charging = True
            self.charge_time = min(self.charge_time + dt, self.MAX_CHARGE)

        if just_released and self.is_charging:
            ratio = self.get_charge_ratio()
            # Băng dài ra theo charge
            length = 20 + int(self.MAX_LENGTH * ratio)
            damage = self.base_damage * (1.2 + ratio * 3.0)
            from status_effect import StatusEffect
            self.pending_shots.append(IcePath(
                player.x, player.y, world_mx, world_my,
                self.SPEED, self.BASE_RADIUS, damage,
                length=length,
                spell_manager=player.spell_manager,
                core_tree=player.spell_manager.core_tree
            ))
            self.charge_time = 0.0
            self.is_charging = False

        if not mouse_held:
            self.is_charging = False

    def draw_preview(self, screen, cx, cy, player):
        if not self.is_charging or self.charge_time < 0.1:
            return
        ratio = self.get_charge_ratio()
        length = 20 + int(self.MAX_LENGTH * ratio)
        sx, sy = int(player.x - cx), int(player.y - cy)
        
        # Draw a rectangular path preview
        mx, my = pygame.mouse.get_pos()
        ang = math.atan2(my - sy, mx - sx)
        
        # Rectangle points
        w = self.BASE_RADIUS * 2
        p1 = (sx + math.cos(ang+math.pi/2)*w, sy + math.sin(ang+math.pi/2)*w)
        p2 = (sx + math.cos(ang-math.pi/2)*w, sy + math.sin(ang-math.pi/2)*w)
        p3 = (p2[0] + math.cos(ang)*length, p2[1] + math.sin(ang)*length)
        p4 = (p1[0] + math.cos(ang)*length, p1[1] + math.sin(ang)*length)
        
        pygame.draw.polygon(screen, (50, 150, 255, 80), [p1, p2, p3, p4])
        pygame.draw.polygon(screen, (200, 240, 255), [p1, p2, p3, p4], 2)

    def draw_effects(self, screen, cx, cy):
        pass

    def draw_hud(self, screen, font, x, y):
        ratio = self.get_charge_ratio()
        pygame.draw.rect(screen, (0, 30, 70), (x, y, 130, 10))
        pygame.draw.rect(screen, (100, 200, 255), (x, y, int(130 * ratio), 10))
        pygame.draw.rect(screen, (200, 255, 255), (x, y, 130, 10), 1)
        txt = "ICE CHARGE"
        lbl = font.render(txt, True, (150, 220, 255))
        screen.blit(lbl, (x, y - 16))


# ─────────────────────────────────────────────
#  LIGHTNING WEAPON
# ─────────────────────────────────────────────
class LightningWeapon:
    ZAP_INTERVAL    = 0.15
    RANGE           = 280
    FILL_RATE       = 0.4
    DRAIN_RATE      = 0.2
    OVERLOAD_CD     = 2.5

    def __init__(self, base_damage):
        self.base_damage = base_damage
        self.zap_timer = 0.0
        self.overload_meter = 0.0
        self.is_overloaded = False
        self.overload_cd_timer = 0.0
        self.zap_segs = []
        self.sparks   = []
        self.pending_damage = []
        self.pending_shots  = []

    def update(self, dt, mouse_held, just_released, world_mx, world_my, player, all_enemies):
        self.pending_damage = []
        self.pending_shots  = []
        
        self.zap_segs = [(x1,y1,x2,y2,c,l-dt) for (x1,y1,x2,y2,c,l) in self.zap_segs if l>0]
        for s in self.sparks:
            s[0] += s[2]*dt; s[1] += s[3]*dt; s[4] -= dt
        self.sparks = [s for s in self.sparks if s[4]>0]

        if self.is_overloaded:
            self.overload_cd_timer -= dt
            self.overload_meter = max(0.0, self.overload_meter - dt / self.OVERLOAD_CD)
            if self.overload_cd_timer <= 0:
                self.is_overloaded = False
                self.overload_meter = 0.0
            return

        if mouse_held:
            self.overload_meter = min(1.0, self.overload_meter + self.FILL_RATE * dt)
            if self.overload_meter >= 1.0:
                self.is_overloaded = True
                self.overload_cd_timer = self.OVERLOAD_CD
                return
            
            self.zap_timer -= dt
            if self.zap_timer <= 0:
                self.zap_timer = self.ZAP_INTERVAL
                self._manual_zap(player, world_mx, world_my, all_enemies)
        else:
            self.overload_meter = max(0.0, self.overload_meter - self.DRAIN_RATE * dt)

    def _manual_zap(self, player, mx, my, all_enemies):
        # No auto-aim: Zap in mouse direction up to RANGE
        ang = math.atan2(my - player.y, mx - player.x)
        tx = player.x + math.cos(ang) * self.RANGE
        ty = player.y + math.sin(ang) * self.RANGE
        
        # Check collision with enemies along this short line
        hit_enemy = None
        min_dist = self.RANGE
        
        for e in all_enemies:
            if not e.alive: continue
            # Simple line-to-point distance check
            dist = self._dist_point_to_segment(e.x, e.y, player.x, player.y, tx, ty)
            if dist < e.radius + 10:
                d_to_p = math.hypot(e.x - player.x, e.y - player.y)
                if d_to_p < min_dist:
                    min_dist = d_to_p
                    hit_enemy = e
        
        if hit_enemy:
            self._bolt(player.x, player.y, hit_enemy.x, hit_enemy.y, (255, 255, 100))
            self.pending_damage.append((hit_enemy, self.base_damage * 0.8))
            # Apply stun (logic in entities.py will use slow_factor=0.0)
            from status_effect import StatusEffect
            hit_enemy.add_status(StatusEffect('stun', 0.0, 0.4, slow_factor=0.0))
        else:
            # Visual only bolt if nothing hit
            self._bolt(player.x, player.y, tx, ty, (200, 200, 255))

    def _dist_point_to_segment(self, px, py, x1, y1, x2, y2):
        dx, dy = x2 - x1, y2 - y1
        if dx == 0 and dy == 0:
            return math.hypot(px - x1, py - y1)
        t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
        t = max(0, min(1, t))
        nearest_x = x1 + t * dx
        nearest_y = y1 + t * dy
        return math.hypot(px - nearest_x, py - nearest_y)

    def emit_move_spark(self, px, py):
        for _ in range(2):
            ang = random.uniform(0, math.pi * 2)
            spd = random.uniform(30, 80)
            self.sparks.append([px, py, math.cos(ang)*spd, math.sin(ang)*spd, 0.3, (255,255,100)])

    def _bolt(self, x1, y1, x2, y2, color, segs=5): # Shorter bolts
        dx = (x2-x1)/segs
        dy = (y2-y1)/segs
        pts = [(x1,y1)]
        for i in range(1, segs):
            off = random.uniform(-4, 4) # Jittery
            pts.append((x1+dx*i - dy*off/10, y1+dy*i + dx*off/10))
        pts.append((x2,y2))
        for i in range(len(pts)-1):
            self.zap_segs.append((*pts[i], *pts[i+1], color, 0.1))

    def draw_preview(self, screen, cx, cy, player):
        if self.is_overloaded:
            sx, sy = int(player.x-cx), int(player.y-cy)
            pygame.draw.circle(screen, (255,255,0), (sx,sy), player.radius+10, 2)

    def draw_effects(self, screen, cx, cy):
        for (x1,y1,x2,y2,color,life) in self.zap_segs:
            a = max(0.0, min(life/0.1, 1.0))
            c = tuple(int(v*a) for v in color)
            pygame.draw.line(screen, c, (int(x1-cx), int(y1-cy)), (int(x2-cx), int(y2-cy)), 2)
        for s in self.sparks:
            pygame.draw.circle(screen, s[5], (int(s[0]-cx), int(s[1]-cy)), 2)

    def draw_hud(self, screen, font, x, y):
        color = (255,50,50) if self.is_overloaded else (255,220,50)
        pygame.draw.rect(screen, (40,40,0), (x, y, 130, 10))
        pygame.draw.rect(screen, color, (x, y, int(130*self.overload_meter), 10))
        pygame.draw.rect(screen, (255,255,150), (x, y, 130, 10), 1)
        lbl = font.render("LIGHTNING" if not self.is_overloaded else "OVERHEAT", True, color)
        screen.blit(lbl, (x, y-16))


# ─────────────────────────────────────────────
#  WIND WEAPON (Boomerang/Piercing)
# ─────────────────────────────────────────────
class WindProjectile(WeaponProjectile):
    def __init__(self, x, y, tx, ty, speed, radius, damage, player, max_range=350, spell_manager=None, core_tree=None, trigger_spawn=True):
        super().__init__(x, y, tx, ty, speed, radius, damage, (180, 255, 180), spell_manager=spell_manager, core_tree=core_tree, trigger_spawn=trigger_spawn)
        self.player = player
        self.max_range = max_range
        self.pierce = True
        self.returning = False
        self.dist_traveled = 0.0
        self.start_x = x
        self.start_y = y
        self.lifetime = 5.0 # Longer lifetime for boomerang
        self.rotation = 0.0

    def update(self, dt):
        self.rotation += 500 * dt # Spin the disc
        
        if not self.returning:
            # Fly out
            dx = self.vx * dt
            dy = self.vy * dt
            self.x += dx
            self.y += dy
            self.dist_traveled += math.hypot(dx, dy)
            
            if self.dist_traveled >= self.max_range:
                self.returning = True
                # Clear hit list on return to allow hitting same enemies again?
                # The request says "hoạt động như 1 boomerang", usually hits on way out and way back.
                self.hit_enemies.clear() 
        else:
            # Return to player
            dx = self.player.x - self.x
            dy = self.player.y - self.y
            dist = math.hypot(dx, dy)
            if dist < 20: # Caught by player
                self.alive = False
            else:
                spd = math.hypot(self.vx, self.vy) * 1.2 # Slightly faster on return
                self.x += (dx / dist) * spd * dt
                self.y += (dy / dist) * spd * dt
                
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, screen, cx, cy):
        sx, sy = int(self.x - cx), int(self.y - cy)
        # Draw as a spinning disc
        pygame.draw.circle(screen, (100, 255, 150), (sx, sy), self.radius)
        pygame.draw.circle(screen, (200, 255, 200), (sx, sy), self.radius, 2)
        
        # Inner "blades" or detail
        for i in range(3):
            ang = math.radians(self.rotation + i * 120)
            ex = sx + math.cos(ang) * (self.radius - 2)
            ey = sy + math.sin(ang) * (self.radius - 2)
            pygame.draw.line(screen, (255, 255, 255), (sx, sy), (ex, ey), 2)

class WindWeapon:
    FIRE_RATE = 0.6
    SPEED = 550
    RADIUS = 12
    BASE_DMG = 15.0

    def __init__(self, base_damage):
        self.base_damage = self.BASE_DMG
        self.fire_timer = 0.0
        self.pending_shots = []

    def update(self, dt, mouse_held, just_released, world_mx, world_my, player, all_enemies):
        self.fire_timer = max(0.0, self.fire_timer - dt)
        self.pending_shots = []

        if mouse_held and self.fire_timer <= 0:
            self.fire_timer = self.FIRE_RATE
            self.pending_shots.append(WindProjectile(
                player.x, player.y, world_mx, world_my,
                self.SPEED, self.RADIUS, self.base_damage,
                player, max_range=350,
                spell_manager=player.spell_manager,
                core_tree=player.spell_manager.core_tree
            ))

    def draw_preview(self, screen, cx, cy, player):
        pass

    def draw_effects(self, screen, cx, cy):
        pass

    def draw_hud(self, screen, font, x, y):
        ratio = 1.0 - (self.fire_timer / self.FIRE_RATE) if self.FIRE_RATE > 0 else 1.0
        pygame.draw.rect(screen, (10, 40, 10), (x, y, 130, 10))
        pygame.draw.rect(screen, (100, 255, 100), (x, y, int(130 * ratio), 10))
        pygame.draw.rect(screen, (200, 255, 200), (x, y, 130, 10), 1)
        lbl = font.render("WIND RECHARGE", True, (150, 255, 150))
        screen.blit(lbl, (x, y - 16))


class IcePath(WeaponProjectile):
    def __init__(self, x, y, tx, ty, speed, radius, damage, length, **kwargs):
        super().__init__(x, y, tx, ty, speed, radius, damage, (150, 220, 255))
        self.length = length
        self.pierce = True
        self.lifetime = 1.2 # Short lived path
        from status_effect import StatusEffect
        self.status_effects = [StatusEffect('chill', 2.0, 4.0, slow_factor=0.6)]
        self.growth = 0.0
        self.spell_manager = kwargs.get('spell_manager', None)
        self.core_tree = kwargs.get('core_tree', None)
    def update(self, dt):
        # The path "grows" or rises stationary from the ground
        self.growth = min(1.0, self.growth + dt * 4.0)
        # NO MOVEMENT: self.x += self.vx * dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False

    def check_collision(self, target):
        # Line-segment collision: from (x, y) forward by length
        # (x, y) is the player position
        x1, y1 = self.x, self.y
        x2 = x1 + math.cos(self.angle) * self.length
        y2 = y1 + math.sin(self.angle) * self.length
        
        # Point (target.x, target.y) to segment (x1, y1) -> (x2, y2)
        dx, dy = x2 - x1, y2 - y1
        if dx == 0 and dy == 0:
            dist = math.hypot(target.x - x1, target.y - y1)
        else:
            t = ((target.x - x1) * dx + (target.y - y1) * dy) / (dx * dx + dy * dy)
            t = max(0, min(1, t))
            nx = x1 + t * dx
            ny = y1 + t * dy
            dist = math.hypot(target.x - nx, target.y - ny)
            
        return dist < target.radius + self.radius

    def draw(self, screen, cx, cy):
        sx, sy = int(self.x - cx), int(self.y - cy)
        ang = self.angle
        
        # Draw as a rectangular "ice block" path
        # It rises from the ground (alpha and width growth)
        alpha = int(255 * self.growth)
        w = self.radius * 2 * self.growth
        l = self.length
        
        # Rectangle points
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)
        cos_p = math.cos(ang + math.pi/2)
        sin_p = math.sin(ang + math.pi/2)
        
        p1 = (sx + cos_p*w, sy + sin_p*w)
        p2 = (sx - cos_p*w, sy - sin_p*w)
        p3 = (p2[0] + cos_a*l, p2[1] + sin_a*l)
        p4 = (p1[0] + cos_a*l, p1[1] + sin_a*l)
        
        surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(surf, (150, 230, 255, alpha), [p1, p2, p3, p4])
        pygame.draw.polygon(surf, (255, 255, 255, alpha), [p1, p2, p3, p4], 2)
        screen.blit(surf, (0, 0))
        
        # Crystals popping up
        if self.growth > 0.5:
            for i in range(3):
                dist = (i/3) * l
                cx_p = sx + cos_a * dist
                cy_p = sy + sin_a * dist
                pygame.draw.circle(screen, (200, 255, 255), (int(cx_p), int(cy_p)), int(w/2))
