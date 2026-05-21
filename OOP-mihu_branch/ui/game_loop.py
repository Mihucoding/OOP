import math
import os
import random
import pygame

from logic.entities.player       import Player
from logic.entities.enemy        import Enemy
from logic.entities.ranged_enemy import RangedEnemy
from logic.entities.boss         import Boss
from logic.entities.bullet       import Bullet
from logic.entities.enemy_bullet import EnemyBullet
from logic.entities.xp_orb       import XPOrb
from logic.wave.wave_manager     import WaveManager
from logic.leveling.level_manager import LevelManager
from ui.renderer                  import Renderer, SCREEN_W, SCREEN_H
from ui.hud                       import HUD
from ui.input_handler             import InputHandler
from ui.screens.main_menu         import MainMenu
from ui.screens.level_up_screen   import LevelUpScreen
from ui.screens.game_over_screen  import GameOverScreen
from ui.screens.win_screen        import WinScreen
from ui.screens.rune_builder_screen import RuneBuilderScreen

FPS            = 60
WORLD_CENTER_X = 0.0
WORLD_CENTER_Y = 0.0
CONTACT_DAMAGE = 15.0   # HP/s khi quái chạm player
LIGHTNING_OVERLOAD_FILL_RATE = 0.36
LIGHTNING_OVERLOAD_DECAY_RATE = 0.42
LIGHTNING_OVERLOAD_READY_AT = 0.20
LIGHTNING_OVERLOAD_FX_INTERVAL = 0.10
LIGHTNING_OVERLOAD_FX_RADIUS = 42.0
LIGHTNING_BEAM_RANGE = 160.0
LIGHTNING_BEAM_HIT_RADIUS = 24.0
LIGHTNING_CHAIN_RADIUS = 280.0
CAMERA_FOLLOW_SPEED = 9.5


class GameLoop:
    """
    State machine chính:
    MENU → PLAYING ⇄ RUNE_BUILDER → LEVEL_UP → GAME_OVER | WIN
    """
    STATE_MENU         = 'menu'
    STATE_PLAYING      = 'playing'
    STATE_LEVEL_UP     = 'level_up'
    STATE_RUNE_BUILDER = 'rune_builder'  # Tab → mở Rune Builder toàn màn hình
    STATE_GAME_OVER    = 'game_over'
    STATE_WIN          = 'win'

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Rune Craft Roguelike")
        self.clock = pygame.time.Clock()

        font_big   = self._load_font(36)
        font_small = self._load_font(14)

        self.renderer    = Renderer(self.screen)
        self.hud         = HUD(self.screen, font_small)
        self.input       = InputHandler()
        self.menu        = MainMenu(self.screen, font_big, font_small)
        self.levelup_scr = LevelUpScreen(self.screen, font_big, font_small)
        self.gameover    = GameOverScreen(self.screen, font_big, font_small)
        self.win_scr     = WinScreen(self.screen, font_big, font_small)
        self.builder     = RuneBuilderScreen(self.screen, font_big, font_small)

        self.state = self.STATE_MENU
        self._dt   = 0.0   # dt frame hiện tại (dùng cho builder timer)
        self._init_game_objects()

    def _load_font(self, size: int) -> pygame.font.Font:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        font_path = os.path.join(root_dir, "assets", "fonts", "pixel_font.ttf")
        try:
            return pygame.font.Font(font_path, size)
        except Exception:
            return pygame.font.SysFont(None, size)

    # ── Khởi tạo / reset ──────────────────────────────────────────────────────

    def _init_game_objects(self):
        self.player        = Player(WORLD_CENTER_X, WORLD_CENTER_Y)
        self.enemies: list[Enemy]             = []
        self.boss:    Boss | None             = None
        self.bullets: list[Bullet]            = []
        self.enemy_bullets: list[EnemyBullet] = []
        self.xp_orbs: list[XPOrb]             = []
        self.effects: list[dict]               = []
        self.wave_mgr       = WaveManager()
        self.level_mgr      = LevelManager()
        self.time_played    = 0.0
        self.ultimate_flash = None   # dict với cx/cy/radius/color/duration
        self.overload_fx_timer = 0.0
        self.camera_x = self.player.x
        self.camera_y = self.player.y

    # ── Vòng lặp chính ────────────────────────────────────────────────────────

    def run(self) -> None:
        running = True
        while running:
            self._dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                result = self._handle_event(event)
                if result == 'quit':
                    running = False

            self._update(self._dt)
            self._draw()
            pygame.display.flip()

        pygame.quit()

    # ── Xử lý sự kiện ─────────────────────────────────────────────────────────

    def _handle_event(self, event) -> str | None:
        # F8 cheat: thêm toàn bộ rune hiện có vào inventory
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F8:
            self._cheat_add_all_runes()
            return None

        # Tab toggle Rune Builder (khi đang chơi)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
            if self.state == self.STATE_PLAYING:
                self.state = self.STATE_RUNE_BUILDER
                return None
            elif self.state == self.STATE_RUNE_BUILDER:
                self.builder._close(self.player)
                self.state = self.STATE_PLAYING
                return None

        # Q/E chuyển chiêu nhanh khi đang chơi
        if event.type == pygame.KEYDOWN and self.state == self.STATE_PLAYING:
            if event.key == pygame.K_q:
                idx = (self.player.active_spell_index - 1) % len(self.player.spells)
                self.player.set_active_spell(idx)
            elif event.key == pygame.K_e:
                idx = (self.player.active_spell_index + 1) % len(self.player.spells)
                self.player.set_active_spell(idx)
            elif event.key == pygame.K_SPACE:
                mx, my = self.input.get_move_direction()
                self.player.movement_ability.activate(self.player, mx, my)

        # Chuột phải → kích hoạt ultimate
        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 3
                and self.state == self.STATE_PLAYING):
            self._activate_ultimate()

        # Rune Builder — nhường event cho builder xử lý
        if self.state == self.STATE_RUNE_BUILDER:
            if self.builder.handle_event(event, self.player):
                self.state = self.STATE_PLAYING
            return None

        # Các state khác
        if self.state == self.STATE_MENU:
            result = self.menu.handle_event(event)
            if result == 'start':
                self._init_game_objects()
                self.state = self.STATE_PLAYING
            elif result == 'quit':
                return 'quit'

        elif self.state == self.STATE_LEVEL_UP:
            result = self.levelup_scr.handle_event(event)
            if result is not None:
                self.level_mgr.apply_choice(result, self.player)
                self.state = self.STATE_PLAYING

        elif self.state == self.STATE_GAME_OVER:
            result = self.gameover.handle_event(event)
            if result == 'restart':
                self._init_game_objects()
                self.state = self.STATE_PLAYING
            elif result == 'quit':
                return 'quit'

        elif self.state == self.STATE_WIN:
            result = self.win_scr.handle_event(event)
            if result == 'restart':
                self._init_game_objects()
                self.state = self.STATE_PLAYING
            elif result == 'quit':
                return 'quit'

        return None

    # ── Update ────────────────────────────────────────────────────────────────

    def _update(self, dt: float) -> None:
        if self.state != self.STATE_PLAYING:
            return

        self.time_played += dt

        # 1. Di chuyển player
        mx, my = self.input.get_move_direction()
        moving_input = math.hypot(mx, my) > 0
        self.player.update(dt, mx, my)
        self._update_camera(dt)

        # 2. Bắn đạn player
        channeled_lightning = False
        if self.input.is_firing():
            wx, wy = self.input.get_mouse_world_pos(
                self._camera_x(), self._camera_y(), self.renderer.zoom)
            spell = self.player.get_active_spell()
            if self._get_lightning_rune(spell):
                channeled_lightning = self._channel_lightning_attack(wx, wy, dt)
            elif self.player.can_fire():
                self._spawn_bullet(wx, wy)
                self.player.reset_fire_timer()
        if not channeled_lightning:
            self._clear_primary_lightning_beam()
        self._update_lightning_overload(dt, channeled_lightning)
        self._emit_lightning_overload_effect(dt, moving_input)

        # 3. Update enemies + boss
        for e in self.enemies:
            e.update(dt, self.player.x, self.player.y)
        if self.boss:
            self.boss.update(dt, self.player.x, self.player.y)

        # 4. RangedEnemy bắn đạn
        for e in self.enemies:
            if isinstance(e, RangedEnemy) and e.alive and e.can_fire():
                self.enemy_bullets.append(
                    EnemyBullet(e.x, e.y, self.player.x, self.player.y))
                e.reset_fire_timer()

        # 5. Update đạn
        for b  in self.bullets:       b.update(dt)
        for eb in self.enemy_bullets: eb.update(dt)

        # 6. Va chạm đạn player ↔ enemy/boss
        self._handle_bullet_collisions()

        # 7. Đạn quái ↔ player
        for eb in self.enemy_bullets:
            if not eb.alive:
                continue
            dist = math.hypot(self.player.x - eb.x, self.player.y - eb.y)
            if dist <= self.player.radius + eb.radius:
                self.player.take_damage(eb.damage)
                eb.alive = False

        # 8. Quái chạm player
        self._handle_enemy_player_collision(dt)

        # 9. Boss AoE
        if self.boss and self.boss.aoe_active:
            dmg = self.boss.check_aoe_hit(self.player.x, self.player.y)
            if dmg:
                self.player.take_damage(dmg * dt)

        # 10. XP orb — update magnet/scatter rồi collect
        for orb in self.xp_orbs:
            orb.update(dt, self.player.x, self.player.y,
                       extra_magnet=self.player.xp_range)
            if orb.check_collect(self.player.x, self.player.y):
                leveled = self.player.add_xp(orb.value)
                if leveled:
                    self.level_mgr.trigger_level_up(self.wave_mgr.wave,
                                                     self.player)
                    self.state = self.STATE_LEVEL_UP

        # 11. Wave manager
        events = self.wave_mgr.update(
            dt, self.player.x, self.player.y, self.enemies, self.boss)
        self._process_wave_events(events)

        # 12. Tick ultimate flash
        if self.ultimate_flash:
            self.ultimate_flash['duration'] -= dt
            if self.ultimate_flash['duration'] <= 0:
                self.ultimate_flash = None
        for effect in self.effects:
            effect['age'] = effect.get('age', 0.0) + dt

        # 13. Dọn dẹp
        self._cleanup()

        # 14. Kiểm tra kết thúc
        if not self.player.alive:
            self.state = self.STATE_GAME_OVER
        if self.boss and not self.boss.alive:
            self.state = self.STATE_WIN

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _get_lightning_rune(self, spell):
        from logic.rune.elements.lightning_rune import LightningRune

        for rune in spell.rune_tree.elements:
            if isinstance(rune, LightningRune):
                return rune
        return None

    def _update_lightning_overload(self, dt: float, channeled: bool) -> None:
        spell = self.player.get_active_spell()
        has_lightning = self._get_lightning_rune(spell) is not None
        overload = getattr(self.player, 'lightning_overload', 0.0)

        if not has_lightning:
            self.player.lightning_overloaded = False
            self.player.lightning_overload = max(
                0.0, overload - LIGHTNING_OVERLOAD_DECAY_RATE * 1.5 * dt)
            return

        if channeled:
            overload = min(1.0, overload + LIGHTNING_OVERLOAD_FILL_RATE * dt)
            if overload >= 1.0:
                self.player.lightning_overloaded = True
        else:
            overload = max(0.0, overload - LIGHTNING_OVERLOAD_DECAY_RATE * dt)

        if self.player.lightning_overloaded and overload <= LIGHTNING_OVERLOAD_READY_AT:
            self.player.lightning_overloaded = False
        self.player.lightning_overload = overload

    def _emit_lightning_overload_effect(self, dt: float, moving: bool) -> None:
        self.overload_fx_timer = max(0.0, self.overload_fx_timer - dt)
        spell = self.player.get_active_spell()
        if (
            not moving
            or not getattr(self.player, 'lightning_overloaded', False)
            or self._get_lightning_rune(spell) is None
        ):
            return

        if self.overload_fx_timer > 0:
            return

        angle = random.random() * math.tau
        radius = random.uniform(8.0, LIGHTNING_OVERLOAD_FX_RADIUS)
        self.effects.append({
            'kind': 'lightning_overload',
            'x': self.player.x + math.cos(angle) * radius,
            'y': self.player.y + math.sin(angle) * radius,
            'duration': 0.30,
        })
        self.overload_fx_timer = LIGHTNING_OVERLOAD_FX_INTERVAL

    def _channel_lightning_attack(self, target_x: float, target_y: float, dt: float) -> bool:
        spell = self.player.get_active_spell()
        lightning = self._get_lightning_rune(spell)
        if lightning is None:
            return False
        if getattr(self.player, 'lightning_overloaded', False):
            return False

        dir_x, dir_y = self._lightning_aim_direction(target_x, target_y)
        start_x, start_y = self._lightning_cast_origin(dir_x, dir_y)
        end_x = start_x + dir_x * LIGHTNING_BEAM_RANGE
        end_y = start_y + dir_y * LIGHTNING_BEAM_RANGE

        stack = getattr(lightning, 'element_stack', 1)
        primary_hit_damage = self.player.damage + lightning.BONUS_DAMAGE * stack
        primary_damage = (primary_hit_damage / max(spell.fire_rate, 0.08)) * dt
        chain_damage = primary_damage * 0.45
        max_targets = 1 + min(4, 2 + stack)
        cast_lock = 0.10

        self.player.cast_lock_timer = cast_lock
        self.player.attack_timer = 0.18
        if dir_x < 0:
            self.player.facing_dir = -1
        elif dir_x > 0:
            self.player.facing_dir = 1

        self._set_primary_lightning_beam(start_x, start_y, end_x, end_y)

        beam_hits = self._targets_in_lightning_beam(start_x, start_y, end_x, end_y)
        if not beam_hits:
            return True

        hit_targets = [beam_hits[0]]
        current = beam_hits[0]
        while len(hit_targets) < max_targets:
            next_target = self._nearest_chain_target(current, hit_targets, LIGHTNING_CHAIN_RADIUS)
            if next_target is None:
                break
            hit_targets.append(next_target)
            current = next_target

        alive_before = {id(enemy) for enemy in self.enemies if enemy.alive}
        boss_alive_before = self.boss is not None and self.boss.alive
        previous = hit_targets[0]
        previous.take_damage(primary_damage)
        for enemy in hit_targets[1:]:
            self.effects.append({
                'kind': 'lightning_beam',
                'x': previous.x,
                'y': previous.y,
                'x2': enemy.x,
                'y2': enemy.y,
                'duration': 0.075,
            })
            enemy.take_damage(chain_damage)
            previous = enemy

        self._drop_xp_from_ultimate_kills(alive_before, boss_alive_before)
        return True

    def _set_primary_lightning_beam(
        self,
        start_x: float,
        start_y: float,
        end_x: float,
        end_y: float,
    ) -> None:
        for effect in self.effects:
            if effect.get('kind') == 'lightning_beam' and effect.get('channel_primary'):
                effect['x'] = start_x
                effect['y'] = start_y
                effect['x2'] = end_x
                effect['y2'] = end_y
                return

        self.effects.append({
            'kind': 'lightning_beam',
            'x': start_x,
            'y': start_y,
            'x2': end_x,
            'y2': end_y,
            'duration': 9999.0,
            'fixed_size': True,
            'loop_anim': True,
            'frame_ms': 45,
            'channel_primary': True,
        })

    def _clear_primary_lightning_beam(self) -> None:
        self.effects = [
            effect for effect in self.effects
            if not (
                effect.get('kind') == 'lightning_beam'
                and effect.get('channel_primary')
            )
        ]

    def _lightning_aim_direction(self, target_x: float, target_y: float) -> tuple[float, float]:
        dx = target_x - self.player.x
        dy = target_y - self.player.y
        dist = math.hypot(dx, dy)
        if dist <= 0:
            return (float(self.player.facing_dir), 0.0)
        return (dx / dist, dy / dist)

    def _lightning_cast_origin(self, dir_x: float, dir_y: float) -> tuple[float, float]:
        return (
            self.player.x + dir_x * 30,
            self.player.y + dir_y * 30 - 6,
        )

    def _targets_in_lightning_beam(
        self,
        start_x: float,
        start_y: float,
        end_x: float,
        end_y: float,
    ) -> list:
        seg_dx = end_x - start_x
        seg_dy = end_y - start_y
        seg_len_sq = seg_dx * seg_dx + seg_dy * seg_dy
        if seg_len_sq <= 0:
            return []

        hits = []
        for enemy in self._living_targets():
            proj = (
                (enemy.x - start_x) * seg_dx
                + (enemy.y - start_y) * seg_dy
            ) / seg_len_sq
            if proj < 0.0 or proj > 1.0:
                continue
            closest_x = start_x + seg_dx * proj
            closest_y = start_y + seg_dy * proj
            dist = math.hypot(enemy.x - closest_x, enemy.y - closest_y)
            if dist <= enemy.radius + LIGHTNING_BEAM_HIT_RADIUS:
                hits.append((proj, enemy))

        hits.sort(key=lambda item: item[0])
        return [enemy for _, enemy in hits]

    def _nearest_chain_target(self, source, already_hit: list, chain_radius: float):
        already_ids = {id(enemy) for enemy in already_hit}
        candidates = [
            enemy for enemy in self._living_targets()
            if id(enemy) not in already_ids
            and math.hypot(enemy.x - source.x, enemy.y - source.y) <= chain_radius
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda enemy: math.hypot(enemy.x - source.x, enemy.y - source.y))

    def _living_targets(self) -> list:
        targets = [enemy for enemy in self.enemies if enemy.alive]
        if self.boss and self.boss.alive:
            targets.append(self.boss)
        return targets

    def _spawn_bullet(self, target_x: float, target_y: float) -> None:
        import random as _rnd
        spell     = self.player.get_active_spell()
        rune_tree = spell.rune_tree

        # Crit check dựa theo lucky
        damage = self.player.damage
        is_crit = _rnd.random() < self.player.get_crit_chance()
        if is_crit:
            damage *= 2.0

        bullet = Bullet(
            self.player.x, self.player.y,
            target_x, target_y,
            damage,
            rune_tree,
        )
        bullet.is_crit = is_crit   # renderer dùng để flash màu
        self.player.attack_timer = 0.18

        context = {
            'enemies': self.enemies,
            'bullets': self.bullets,
            'effects': self.effects,
        }
        extra   = rune_tree.on_fire(bullet, context)
        self.bullets.append(bullet)
        self.bullets.extend(extra)

    def _handle_bullet_collisions(self) -> None:
        context = {
            'enemies': self.enemies,
            'bullets': self.bullets,
            'effects': self.effects,
        }
        for bullet in self.bullets:
            if not bullet.alive:
                continue
            for enemy in self.enemies:
                if not enemy.alive:
                    continue
                dist = math.hypot(bullet.x - enemy.x, bullet.y - enemy.y)
                if dist <= bullet.radius + enemy.radius:
                    bullet.on_hit(enemy, context)
                    enemy.take_damage(bullet.damage)
                    if not enemy.alive:
                        self.xp_orbs.extend(enemy.drop_xp(self.player.lucky))
                    break
            if bullet.alive and self.boss and self.boss.alive:
                dist = math.hypot(bullet.x - self.boss.x, bullet.y - self.boss.y)
                if dist <= bullet.radius + self.boss.radius:
                    bullet.on_hit(self.boss, context)
                    self.boss.take_damage(bullet.damage)
                    if not self.boss.alive:
                        self.xp_orbs.extend(self.boss.drop_xp(self.player.lucky))

    def _handle_enemy_player_collision(self, dt: float) -> None:
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            dist = math.hypot(self.player.x - enemy.x, self.player.y - enemy.y)
            if dist <= self.player.radius + enemy.radius:
                self.player.take_damage(CONTACT_DAMAGE * dt)
        if self.boss and self.boss.alive:
            dist = math.hypot(self.player.x - self.boss.x, self.player.y - self.boss.y)
            if dist <= self.player.radius + self.boss.radius:
                self.player.take_damage(CONTACT_DAMAGE * dt)

    def _process_wave_events(self, events: dict) -> None:
        if not events:
            return
        for item in events.get('spawn_enemies', []):
            x, y, enemy_type = item
            self.enemies.append(
                RangedEnemy(x, y) if enemy_type == 'ranged' else Enemy(x, y))
        if events.get('spawn_boss'):
            self.boss = Boss(self.player.x + 650, self.player.y)
        summon_count = events.get('summon_enemies', 0)
        if summon_count and self.boss:
            for i in range(summon_count):
                angle = (i / summon_count) * 2 * math.pi
                bx    = self.boss.x + math.cos(angle) * 150
                by    = self.boss.y + math.sin(angle) * 150
                self.enemies.append(Enemy(bx, by))

    def _activate_ultimate(self) -> None:
        if not self.player.can_ultimate():
            return
        from logic.abilities.ultimate.ultimate_base import get_ultimate_for_spell
        spell   = self.player.get_active_spell()
        ult     = get_ultimate_for_spell(spell)
        context = {
            'enemies': self.enemies,
            'bullets': self.bullets,
            'effects': self.effects,
        }
        alive_before = {id(enemy) for enemy in self.enemies if enemy.alive}
        boss_alive_before = self.boss is not None and self.boss.alive
        info    = ult.activate(self.player, self.enemies, self.boss, context)
        self._drop_xp_from_ultimate_kills(alive_before, boss_alive_before)
        self.player.reset_ultimate()
        self.ultimate_flash = info   # renderer dùng để vẽ AoE ring

    def _drop_xp_from_ultimate_kills(self, alive_before: set, boss_alive_before: bool) -> None:
        for enemy in self.enemies:
            if id(enemy) in alive_before and not enemy.alive:
                self.xp_orbs.extend(enemy.drop_xp(self.player.lucky))
        if boss_alive_before and self.boss and not self.boss.alive:
            self.xp_orbs.extend(self.boss.drop_xp(self.player.lucky))

    def _cheat_add_all_runes(self) -> None:
        from logic.rune.elements.fire_rune import FireRune
        from logic.rune.elements.ice_rune import IceRune
        from logic.rune.elements.lightning_rune import LightningRune
        from logic.rune.elements.poison_rune import PoisonRune
        from logic.rune.elements.wind_rune import WindRune
        from logic.rune.modifiers.bounce_modifier import BounceModifier
        from logic.rune.modifiers.haste_rune import HasteRune
        from logic.rune.modifiers.spiral_modifier import SpiralModifier
        from logic.rune.modifiers.split_modifier import SplitModifier

        rune_classes = (
            FireRune,
            IceRune,
            LightningRune,
            PoisonRune,
            WindRune,
            SpiralModifier,
            BounceModifier,
            SplitModifier,
            HasteRune,
        )
        for rune_cls in rune_classes:
            self.player.add_to_inventory(rune_cls())

    def _cleanup(self) -> None:
        self.bullets       = [b  for b  in self.bullets       if b.alive]
        self.enemies       = [e  for e  in self.enemies        if e.alive]
        self.xp_orbs       = [o  for o  in self.xp_orbs        if o.alive]
        self.enemy_bullets = [eb for eb in self.enemy_bullets  if eb.alive]
        self.effects       = [
            effect for effect in self.effects
            if effect.get('age', 0.0) < effect.get('duration', 0.0)
        ]

    def _update_camera(self, dt: float) -> None:
        follow = min(1.0, CAMERA_FOLLOW_SPEED * dt)
        self.camera_x += (self.player.x - self.camera_x) * follow
        self.camera_y += (self.player.y - self.camera_y) * follow

    def _camera_x(self) -> float: return self.camera_x
    def _camera_y(self) -> float: return self.camera_y

    # ── Vẽ ────────────────────────────────────────────────────────────────────

    def _draw(self) -> None:
        if self.state == self.STATE_MENU:
            self.menu.draw()

        elif self.state in (self.STATE_PLAYING, self.STATE_LEVEL_UP):
            self.renderer.draw_all(
                self.player, self.enemies, self.boss,
                self.bullets, self.xp_orbs, self.enemy_bullets,
                self._camera_x(), self._camera_y(),
                effects=self.effects,
                ultimate_flash=self.ultimate_flash)
            self.hud.draw(self.player, self.wave_mgr.get_wave_info())
            if self.state == self.STATE_LEVEL_UP:
                self.levelup_scr.draw(self.level_mgr.current_choices)

        elif self.state == self.STATE_RUNE_BUILDER:
            # Toàn màn hình Rune Builder (game tạm dừng)
            self.builder.draw(self.player, self._dt)

        elif self.state == self.STATE_GAME_OVER:
            self.gameover.draw(self.wave_mgr.wave, self.time_played)

        elif self.state == self.STATE_WIN:
            self.win_scr.draw(self.time_played)
