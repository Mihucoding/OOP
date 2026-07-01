import math
import os
import random
import pygame

from logic.entities.player       import Player
from logic.entities.enemy        import Enemy
from logic.entities.ranged_enemy import RangedEnemy
from logic.entities.fast_enemy   import FastEnemy
from logic.entities.tank_enemy   import TankEnemy
from logic.entities.boss         import Boss
from logic.entities.bullet       import Bullet
from logic.entities.enemy_bullet import EnemyBullet
from logic.entities.attack_effect import (
    AirBurstEffect,
    AoEBurst,
    FireBreathJet,
    ImpactEffect,
    _HitProxy,
)
from logic.entities.xp_orb       import XPOrb
from logic.entities.sheep        import Sheep
from logic.entities.meat         import Meat
from logic.wave.wave_manager     import WaveManager
from logic.leveling.level_manager import LevelManager
from ui.renderer                  import Renderer, SCREEN_W, SCREEN_H, WINDOW_W, WINDOW_H
from ui.hud                       import HUD
from ui.input_handler             import InputHandler
from ui.vfx_manager               import vfx_lib
from ui.screens.main_menu         import MainMenu
from ui.screens.level_up_screen   import LevelUpScreen
from ui.screens.game_over_screen  import GameOverScreen
from ui.screens.win_screen        import WinScreen
from ui.screens.rune_builder_screen import RuneBuilderScreen
from ui.screens.skill_select_screen import SkillSelectScreen
from ui import rune_ui_config as rune_cfg

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
PLAYER_MAP_EDGE_RADIUS = 72.0


class GameLoop:
    """
    State machine chính:
    MENU → PLAYING ⇄ RUNE_BUILDER → LEVEL_UP → GAME_OVER | WIN
    """
    STATE_MENU         = 'menu'
    STATE_SKILL_SELECT = 'skill_select'  # chọn 2 hệ trước khi vào game
    STATE_PLAYING      = 'playing'
    STATE_LEVEL_UP     = 'level_up'
    STATE_RUNE_BUILDER = 'rune_builder'  # Tab → mở Rune Builder toàn màn hình
    STATE_GAME_OVER    = 'game_over'
    STATE_WIN          = 'win'

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        self.game_surface = pygame.Surface((SCREEN_W, SCREEN_H)).convert()
        pygame.display.set_caption("Rune Craft Roguelike")
        self._load_custom_cursor()
        self.clock = pygame.time.Clock()

        font_big   = self._load_font(36)
        font_small = self._load_font(14)
        
        self.font_big = font_big
        self.font_small = font_small

        self.renderer    = Renderer(self.game_surface)
        self.hud         = HUD(self.screen, font_small)
        vfx_lib.load_all()
        pygame.event.pump()
        pygame.event.clear()
        self.input       = InputHandler()
        self.menu        = MainMenu(self.screen, font_big, font_small)
        self.levelup_scr = LevelUpScreen(self.screen, font_big, font_small)
        self.gameover    = GameOverScreen(self.screen, font_big, font_small)
        self.win_scr     = WinScreen(self.screen, font_big, font_small)
        self.builder     = RuneBuilderScreen(self.screen, font_big, font_small)
        self.skill_select = SkillSelectScreen(self.screen, font_big, font_small)

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

    def _load_custom_cursor(self) -> None:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cursor_path = os.path.join(
            root_dir,
            "assets",
            "map",
            "Tiny Swords (Free Pack)",
            "UI Elements",
            "UI Elements",
            "Cursors",
            "Cursor_01.png",
        )
        try:
            cursor = pygame.image.load(cursor_path).convert_alpha()
            cursor = pygame.transform.scale(cursor, (32, 32))
            pygame.mouse.set_cursor(pygame.cursors.Cursor((0, 0), cursor))
        except Exception:
            pass

    # ── Khởi tạo / reset ──────────────────────────────────────────────────────

    def _begin_skill_select(self):
        """Khởi tạo ván mới rồi vào màn chọn 2 hệ (trước khi Playing)."""
        self._init_game_objects()
        self.skill_select.reset()
        self.state = self.STATE_SKILL_SELECT

    def _init_game_objects(self):
        self.player        = Player(WORLD_CENTER_X, WORLD_CENTER_Y)
        self.enemies: list[Enemy]             = []
        self.boss:    Boss | None             = None
        self.bullets: list[Bullet]            = []
        self.enemy_bullets: list[EnemyBullet] = []
        self.xp_orbs: list[XPOrb]             = []
        self.effects: list[dict]               = []
        self.active_effects: list              = []
        self.wave_mgr       = WaveManager()
        self.level_mgr      = LevelManager()
        self.time_played    = 0.0
        self.ultimate_flash = None   # dict với cx/cy/radius/color/duration
        self.overload_fx_timer = 0.0
        self.ice_charge = None
        self._wind_charging    = False
        self._wind_charge_time = 0.0
        self._rmb_held         = False
        self._last_rmb_down    = -999.0
        self._breath_fuel      = self.BREATH_MAX_FUEL
        self._fire_jet         = None
        self.spiral_orbit_angle = 0.0   # góc xoay vortex của lightning beam khi có SpiralModifier
        if not hasattr(self, "noclip_mode"):
            self.noclip_mode = False
        self.player.noclip_mode = self.noclip_mode
        # Đảm bảo player spawn tại vị trí hợp lệ, không bị kẹt trong tile cản
        self._place_entity_on_valid_map_spot(self.player)
        self.camera_x = self.player.x
        self.camera_y = self.player.y
        self._clamp_camera_to_map()
        self._spawn_initial_sheep()
        self.wave_notif_timer = 0.0
        self.wave_notif_text = ""

    WIND_MAX_CHARGE = 3.0
    DOUBLE_TAP_TIME = 0.30
    BREATH_MAX_FUEL = 2.5
    BREATH_DPS_MULT = 1.6

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

    def _handle_event(self, event: pygame.event.Event) -> str | None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F9:
            self.noclip_mode = not self.noclip_mode
            self.player.noclip_mode = self.noclip_mode
            print(f"[CHEAT] Noclip mode toggled: {self.noclip_mode}")
            return None

        if event.type == pygame.KEYDOWN and event.key == pygame.K_F8:
            self._cheat_add_all_runes()
            print("[CHEAT] All runes added")
            return None

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_TAB):
                if self.state == self.STATE_PLAYING:
                    self.builder.set_background_snapshot(self.screen)
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
                old_x, old_y = self.player.x, self.player.y
                mx, my = self.input.get_move_direction()
                self.player.movement_ability.activate(self.player, mx, my)
                self._resolve_player_map_collision(old_x, old_y)

        # Chuột phải → kích hoạt ultimate
        if self.state == self.STATE_PLAYING:
            vt = self.player.get_active_spell().rune_tree.get_visual_type()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                wx, wy = self.input.get_mouse_world_pos(
                    self._camera_x(), self._camera_y(), self.renderer.zoom)
                now = self.time_played
                is_double = (now - self._last_rmb_down) < self.DOUBLE_TAP_TIME
                self._last_rmb_down = now
                if vt == 'fire_bolt':
                    if is_double:
                        self._fire_explosion(wx, wy)
                    elif self._breath_fuel > 0.0:
                        self._rmb_held = True
                elif vt == 'air_burst':
                    self._air_explosion()
                else:
                    self._activate_ultimate()
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 3:
                self._rmb_held = False
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if vt == 'air_burst' and self._wind_charging:
                    wx, wy = self.input.get_mouse_world_pos(
                        self._camera_x(), self._camera_y(), self.renderer.zoom)
                    self._release_air_burst(wx, wy)

        # Rune Builder — nhường event cho builder xử lý
        if self.state == self.STATE_RUNE_BUILDER:
            if self.builder.handle_event(event, self.player):
                self.state = self.STATE_PLAYING
            return None

        # Các state khác
        if self.state == self.STATE_MENU:
            result = self.menu.handle_event(event)
            if result == 'start':
                self._begin_skill_select()
            elif result == 'quit':
                return 'quit'

        elif self.state == self.STATE_SKILL_SELECT:
            result = self.skill_select.handle_event(event)
            if result == 'quit':
                return 'quit'
            elif isinstance(result, tuple) and result[0] == 'confirm':
                runes = [rune_cfg.make_element_rune(k) for k in result[1]]
                self.player.setup_spells(runes)
                self.state = self.STATE_PLAYING

        elif self.state == self.STATE_LEVEL_UP:
            result = self.levelup_scr.handle_event(event)
            if result is not None:
                self.level_mgr.apply_choice(result, self.player)
                self.state = self.STATE_PLAYING

        elif self.state == self.STATE_GAME_OVER:
            result = self.gameover.handle_event(event)
            if result == 'restart':
                self._begin_skill_select()
            elif result == 'quit':
                return 'quit'

        elif self.state == self.STATE_WIN:
            result = self.win_scr.handle_event(event)
            if result == 'restart':
                self._begin_skill_select()
            elif result == 'quit':
                return 'quit'

        return None

    # ── Update ────────────────────────────────────────────────────────────────

    def _update(self, dt: float) -> None:
        if self.state != self.STATE_PLAYING:
            self._cancel_ice_charge()
            if getattr(self, '_fire_jet', None) is not None:
                self._stop_fire_breath()
            return

        self.time_played += dt

        # 1. Di chuyển player
        mx, my = self.input.get_move_direction()
        moving_input = math.hypot(mx, my) > 0
        old_x, old_y = self.player.x, self.player.y
        self.player.update(dt, mx, my)
        self._resolve_player_map_collision(old_x, old_y)
        self._update_camera(dt)

        # 2. Bắn đạn player
        channeled_lightning = False
        firing = self.input.is_firing()
        spell = self.player.get_active_spell()
        visual_type = spell.rune_tree.get_visual_type()
        wx, wy = self.input.get_mouse_world_pos(
            self._camera_x(), self._camera_y(), self.renderer.zoom)
        ice_rune = self._get_ice_rune(spell)
        if ice_rune is not None:
            self._update_ice_charge(dt, wx, wy, firing, ice_rune, spell)
        else:
            self._cancel_ice_charge()

        if visual_type == 'air_burst' and ice_rune is None:
            if firing:
                self._wind_charging = True
                self._wind_charge_time = min(
                    self.WIND_MAX_CHARGE, self._wind_charge_time + dt)
        else:
            self._wind_charging = False
            self._wind_charge_time = 0.0

        if firing and ice_rune is None and visual_type != 'air_burst':
            if self._get_lightning_rune(spell):
                channeled_lightning = self._channel_lightning_attack(wx, wy, dt)
            elif self.player.can_fire():
                self._spawn_bullet(wx, wy)
                self.player.reset_fire_timer()
        self._update_fire_breath(dt, visual_type, wx, wy)
        if not channeled_lightning:
            self._clear_primary_lightning_beam()
        self._update_lightning_overload(dt, channeled_lightning)
        self._emit_lightning_overload_effect(dt, moving_input)

        # 3. Update enemies + boss
        for e in self.enemies:
            old_x, old_y = e.x, e.y
            e.update(dt, self.player.x, self.player.y)
            self._resolve_entity_map_collision(e, old_x, old_y)
        if self.boss:
            old_x, old_y = self.boss.x, self.boss.y
            self.boss.update(dt, self.player.x, self.player.y)
            self._resolve_entity_map_collision(self.boss, old_x, old_y)

        # 4. RangedEnemy bắn đạn
        for e in self.enemies:
            if isinstance(e, RangedEnemy) and e.alive and e.can_fire():
                bullet = EnemyBullet(e.x, e.y, self.player.x, self.player.y)
                bullet.damage = getattr(e, "damage", bullet.damage)
                self.enemy_bullets.append(bullet)
                e.reset_fire_timer()

        # 5. Update đạn
        for b  in self.bullets:       b.update(dt)
        for eb in self.enemy_bullets: eb.update(dt)

        # 6. Va chạm đạn player ↔ enemy/boss
        self._handle_bullet_collisions()
        for effect in self.active_effects:
            effect.update(dt)
        self._handle_effect_collisions()

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
                if isinstance(orb, Meat):
                    self.player.meat_count = getattr(self.player, "meat_count", 0) + 1
                else:
                    leveled = self.player.add_xp(orb.value)
                    if leveled:
                        self.level_mgr.trigger_level_up(self.wave_mgr.wave,
                                                         self.player)
                        self.state = self.STATE_LEVEL_UP

        # Định kỳ kiểm tra và duy trì số lượng cừu
        self.sheep_check_timer = getattr(self, "sheep_check_timer", 0.0) + dt
        if self.sheep_check_timer >= 4.0:
            self.sheep_check_timer = 0.0
            sheep_count = sum(1 for e in self.enemies if isinstance(e, Sheep) and e.alive)
            if sheep_count < 6:
                self._spawn_sheep_randomly()

        # 11. Wave manager
        events = self.wave_mgr.update(
            dt, self.player.x, self.player.y, self.enemies, self.boss)
        self._process_wave_events(events)

        # 12. Tick ultimate flash & Wave Notif
        if self.ultimate_flash:
            self.ultimate_flash['duration'] -= dt
            if self.ultimate_flash['duration'] <= 0:
                self.ultimate_flash = None
        for effect in self.effects:
            effect['age'] = effect.get('age', 0.0) + dt
            
        if self.wave_notif_timer > 0:
            self.wave_notif_timer -= dt

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

    def _has_spiral_modifier(self, spell) -> bool:
        """Kiểm tra spell có SpiralModifier không."""
        from logic.rune.modifiers.spiral_modifier import SpiralModifier
        for modifier in spell.rune_tree.modifiers:
            if isinstance(modifier, SpiralModifier):
                return True
        return False

    def _get_ice_rune(self, spell):
        from logic.rune.elements.ice_rune import IceRune

        for rune in spell.rune_tree.elements:
            if isinstance(rune, IceRune):
                return rune
        return None

    def _update_ice_charge(self, dt: float, target_x: float, target_y: float, firing: bool, ice_rune, spell) -> None:
        if not firing:
            self._release_ice_charge()
            return

        if self.ice_charge is None:
            if not spell.can_fire():
                return
            self.ice_charge = {
                "rune": ice_rune,
                "spell": spell,
                "held": 0.0,
            }

        self.ice_charge["held"] = min(
            ice_rune.CHARGE_MAX_TIME,
            self.ice_charge.get("held", 0.0) + dt,
        )
        has_spiral = self._has_spiral_modifier(spell)
        if has_spiral:
            from logic.abilities.ice_attack import IceSpiralAttack
            spiral_attack = IceSpiralAttack()
            attack = spiral_attack.build_charge_attack(
                ice_rune,
                self.player.x,
                self.player.y,
                target_x,
                target_y,
                self.ice_charge["held"],
            )
            # Khi có Spiral, ta bỏ qua chia góc của Split (như thảo luận trước đó)
            attacks = [attack]
        else:
            attack = ice_rune.build_charge_attack(
                self.player.x,
                self.player.y,
                target_x,
                target_y,
                self.ice_charge["held"],
            )
            attacks = [
                self._build_split_ice_attack(ice_rune, attack, angle, self.ice_charge["held"])
                for angle in self._split_angles_for_spell(spell)
            ]

        self.ice_charge["attack"] = attack
        self.ice_charge["attacks"] = attacks
        self.ice_charge["ratio"] = attack["ratio"]
        if attack["dir_x"] < 0:
            self.player.facing_dir = -1
        elif attack["dir_x"] > 0:
            self.player.facing_dir = 1
        self.player.attack_timer = 0.12

    def _release_ice_charge(self) -> None:
        if not self.ice_charge:
            return

        ice_rune = self.ice_charge["rune"]
        spell = self.ice_charge["spell"]
        attacks = self.ice_charge.get("attacks") or []
        if not attacks:
            self.ice_charge = None
            return

        stack = getattr(ice_rune, "element_stack", 1)
        boss_alive_before = self.boss is not None and self.boss.alive
        enemy_alive_before = {id(enemy) for enemy in self.enemies if enemy.alive}
        damaged_targets = set()

        for attack in attacks:
            damage = self.player.damage * attack["damage_mult"]
            
            if attack.get("is_spiral"):
                from logic.abilities.ice_attack import IceSpiralAttack
                spiral_attack = IceSpiralAttack()
                hits = spiral_attack.targets_in_ice_spiral(attack, self.enemies)
            else:
                hits = self._targets_in_ice_hitbox(attack)
                
            for target in hits:
                if id(target) in damaged_targets:
                    continue
                damaged_targets.add(id(target))
                ice_rune.apply_charge_hit(target, damage, attack["ratio"], stack=stack)

            if attack.get("is_spiral"):
                self.effects.append({
                    "kind": "ice_spiral",
                    "cx": attack["start_x"],
                    "cy": attack["start_y"],
                    "radius": attack["radius"],
                    "aim_angle": attack["aim_angle"],
                    "arc_length_rad": attack["arc_length_rad"],
                    "duration": 0.48 + attack["ratio"] * 0.8,
                })
            else:
                self.effects.append({
                    "kind": "ice_spike",
                    "x": attack["start_x"],
                    "y": attack["start_y"],
                    "x2": attack["end_x"],
                    "y2": attack["end_y"],
                    "width": attack["width"] * 1.35,
                    "duration": 0.48 + attack["length"] / 80.0 * 0.045,
                })
        for enemy in self.enemies:
            if id(enemy) in enemy_alive_before and not enemy.alive:
                self.xp_orbs.extend(enemy.drop_xp(self.player.lucky))
        if boss_alive_before and self.boss and not self.boss.alive:
            self.xp_orbs.extend(self.boss.drop_xp(self.player.lucky))

        spell.reset_fire_timer()
        self.player.cast_lock_timer = 0.08
        self.player.attack_timer = 0.18
        self.ice_charge = None

    def _cancel_ice_charge(self) -> None:
        self.ice_charge = None

    def _build_split_ice_attack(self, ice_rune, base_attack: dict, angle_offset: float, held_time: float) -> dict:
        base_angle = math.atan2(base_attack["dir_y"], base_attack["dir_x"])
        angle = base_angle + math.radians(angle_offset)
        target_x = self.player.x + math.cos(angle) * 100
        target_y = self.player.y + math.sin(angle) * 100
        attack = ice_rune.build_charge_attack(
            self.player.x,
            self.player.y,
            target_x,
            target_y,
            held_time,
        )
        max_length = self._ice_camera_length_cap(attack)
        if max_length < attack["length"]:
            attack = ice_rune.build_charge_attack(
                self.player.x,
                self.player.y,
                target_x,
                target_y,
                held_time,
                max_length=max_length,
            )
        return attack

    def _split_angles_for_spell(self, spell) -> list[float]:
        split_angle = self._split_angle_for_spell(spell)
        if split_angle <= 0:
            return [0.0]
        return [0.0, -split_angle, split_angle]

    def _split_angle_for_spell(self, spell) -> float:
        from logic.rune.modifiers.split_modifier import SplitModifier

        stack = 0

        def visit(modifier) -> None:
            nonlocal stack
            if isinstance(modifier, SplitModifier):
                stack = max(stack, getattr(modifier, "stack", 1))
            for child in modifier.get_children():
                visit(child)

        for modifier in spell.rune_tree.modifiers:
            visit(modifier)
        if stack <= 0:
            return 0.0
        return SplitModifier.SPLIT_ANGLE

    def _ice_camera_length_cap(self, attack: dict) -> float:
        zoom = max(0.001, getattr(self.renderer, "zoom", 1.0))
        margin = attack["width"] / 2 + 18.0
        left = self._camera_x() - SCREEN_W / (2 * zoom) + margin
        right = self._camera_x() + SCREEN_W / (2 * zoom) - margin
        top = self._camera_y() - SCREEN_H / (2 * zoom) + margin
        bottom = self._camera_y() + SCREEN_H / (2 * zoom) - margin

        start_x = attack["start_x"]
        start_y = attack["start_y"]
        dir_x = attack["dir_x"]
        dir_y = attack["dir_y"]
        limits = []
        if dir_x > 0:
            limits.append((right - start_x) / dir_x)
        elif dir_x < 0:
            limits.append((left - start_x) / dir_x)
        if dir_y > 0:
            limits.append((bottom - start_y) / dir_y)
        elif dir_y < 0:
            limits.append((top - start_y) / dir_y)

        positive_limits = [value for value in limits if value > 0]
        if not positive_limits:
            return attack["length"]
        return min(attack["length"], max(32.0, min(positive_limits)))

    def _targets_in_ice_hitbox(self, attack: dict) -> list:
        sx, sy = attack["start_x"], attack["start_y"]
        ex, ey = attack["end_x"], attack["end_y"]
        dx = ex - sx
        dy = ey - sy
        length_sq = dx * dx + dy * dy
        if length_sq <= 0:
            return []

        targets = []
        for enemy in self._living_targets():
            proj = ((enemy.x - sx) * dx + (enemy.y - sy) * dy) / length_sq
            if proj < 0.0 or proj > 1.0:
                continue
            closest_x = sx + dx * proj
            closest_y = sy + dy * proj
            dist = math.hypot(enemy.x - closest_x, enemy.y - closest_y)
            if dist <= attack["width"] / 2 + enemy.radius:
                targets.append(enemy)
        return targets

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

        stack = getattr(lightning, 'element_stack', 1)
        primary_hit_damage = self.player.damage + lightning.BONUS_DAMAGE * stack
        primary_damage = (primary_hit_damage / max(spell.fire_rate, 0.08)) * dt
        chain_damage = primary_damage * 0.45
        max_targets = 1 + min(4, 2 + stack)
        cast_lock = 0.10

        self.player.cast_lock_timer = cast_lock
        self.player.attack_timer = 0.18

        alive_before = {id(enemy) for enemy in self.enemies if enemy.alive}
        boss_alive_before = self.boss is not None and self.boss.alive

        has_spiral = self._has_spiral_modifier(spell)
        if has_spiral:
            # ── Vortex ring được tách ra class riêng ─────────────────────────────
            from logic.abilities.lightning_attack import LightningSpiralAttack
            spiral_attack = LightningSpiralAttack()
            return spiral_attack.execute(
                game_loop=self,
                target_x=target_x,
                target_y=target_y,
                primary_damage=primary_damage,
                chain_damage=chain_damage,
                max_targets=max_targets,
                alive_before=alive_before,
                boss_alive_before=boss_alive_before,
            )

        # ── Normal lightning beam ────────────────────────────────────────────
        aim_x, aim_y = self._lightning_aim_direction(target_x, target_y)

        if aim_x < 0:
            self.player.facing_dir = -1
        elif aim_x > 0:
            self.player.facing_dir = 1

        split_angles = self._split_angles_for_spell(spell)
        self._trim_primary_lightning_beams(len(split_angles))
        for beam_id, angle_offset in enumerate(split_angles):
            dir_x, dir_y = self._rotated_direction(aim_x, aim_y, angle_offset)
            start_x, start_y = self._lightning_cast_origin(dir_x, dir_y)
            end_x = start_x + dir_x * LIGHTNING_BEAM_RANGE
            end_y = start_y + dir_y * LIGHTNING_BEAM_RANGE
            self._set_primary_lightning_beam(start_x, start_y, end_x, end_y, beam_id=beam_id, vortex=False)

            beam_hits = self._targets_in_lightning_beam(start_x, start_y, end_x, end_y)

            beam_hits = self._targets_in_lightning_beam(start_x, start_y, end_x, end_y)
            if not beam_hits:
                continue

            hit_targets = [beam_hits[0]]
            current = beam_hits[0]
            while len(hit_targets) < max_targets:
                next_target = self._nearest_chain_target(current, hit_targets, LIGHTNING_CHAIN_RADIUS)
                if next_target is None:
                    break
                hit_targets.append(next_target)
                current = next_target

            previous = hit_targets[0]
            previous.take_damage(primary_damage)
            for enemy in hit_targets[1:]:
                self.effects.append({
                    'kind': 'lightning_beam',
                    'x': previous.x,
                    'y': previous.y,
                    'x2': enemy.x,
                    'y2': enemy.y,
                    'duration': 0.12,
                    'loop_anim': True,
                    'frame_ms': 75,
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
        beam_id: int = 0,
        vortex: bool = False,
    ) -> None:
        for effect in self.effects:
            if (
                effect.get('kind') == 'lightning_beam'
                and effect.get('channel_primary')
                and effect.get('beam_id', 0) == beam_id
            ):
                effect['x'] = start_x
                effect['y'] = start_y
                effect['x2'] = end_x
                effect['y2'] = end_y
                effect['vortex'] = vortex
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
            'frame_ms': 75,
            'channel_primary': True,
            'beam_id': beam_id,
            'vortex': vortex,
        })

    def _clear_primary_lightning_beam(self) -> None:
        self.effects = [
            effect for effect in self.effects
            if not (
                effect.get('kind') == 'lightning_beam'
                and effect.get('channel_primary')
            )
        ]

    def _trim_primary_lightning_beams(self, active_count: int) -> None:
        self.effects = [
            effect for effect in self.effects
            if not (
                effect.get('kind') == 'lightning_beam'
                and effect.get('channel_primary')
                and effect.get('beam_id', 0) >= active_count
            )
        ]

    def _lightning_aim_direction(self, target_x: float, target_y: float) -> tuple[float, float]:
        dx = target_x - self.player.x
        dy = target_y - self.player.y
        dist = math.hypot(dx, dy)
        if dist <= 0:
            return (float(self.player.facing_dir), 0.0)
        return (dx / dist, dy / dist)

    def _rotated_direction(self, dir_x: float, dir_y: float, angle_degrees: float) -> tuple[float, float]:
        if angle_degrees == 0:
            return dir_x, dir_y
        angle = math.radians(angle_degrees)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return (
            dir_x * cos_a - dir_y * sin_a,
            dir_x * sin_a + dir_y * cos_a,
        )

    def _lightning_cast_origin(self, dir_x: float, dir_y: float) -> tuple[float, float]:
        return (
            self.player.x + dir_x * 30,
            self.player.y + dir_y * 30 - 6,
        )

    def _targets_in_vortex(
        self,
        cx: float,
        cy: float,
        radius: float,
    ) -> list:
        """Kiểm tra enemy trong bán kính orbit của vortex ring."""
        hits = []
        for enemy in self._living_targets():
            dist = math.hypot(enemy.x - cx, enemy.y - cy)
            if dist <= radius + enemy.radius:
                hits.append(enemy)
        return hits

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
        bullet.visual_type = rune_tree.get_visual_type()

        context = {
            'enemies': self.enemies,
            'bullets': self.bullets,
            'effects': self.effects,
        }
        extra   = rune_tree.on_fire(bullet, context)
        for b in extra:
            b.visual_type = bullet.visual_type
            b.is_crit = is_crit
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
                    if not bullet.alive:
                        self._spawn_impact(bullet)
                    break
            if bullet.alive and self.boss and self.boss.alive:
                dist = math.hypot(bullet.x - self.boss.x, bullet.y - self.boss.y)
                if dist <= bullet.radius + self.boss.radius:
                    bullet.on_hit(self.boss, context)
                    self.boss.take_damage(bullet.damage)
                    if not bullet.alive:
                        self._spawn_impact(bullet)

    def _spawn_impact(self, bullet) -> None:
        vt = getattr(bullet, 'visual_type', '')
        if vt == 'blood_ball':
            self.active_effects.append(ImpactEffect(bullet.x, bullet.y, 'blood_impact'))
        elif vt == 'fire_bolt':
            self.active_effects.append(
                ImpactEffect(bullet.x, bullet.y, 'fire_bolt_hit', lifetime=0.28))

    def _handle_effect_collisions(self) -> None:
        context = {
            'enemies': self.enemies,
            'bullets': self.bullets,
            'effects': self.effects,
        }
        for effect in self.active_effects:
            if not effect.alive:
                continue
            hits = effect.check_hits(self.enemies, self.boss)
            if not hits:
                continue
            for entity in hits:
                if not entity.alive:
                    continue
                entity.take_damage(effect.damage)
                if getattr(effect, 'rune_tree', None):
                    proxy = _HitProxy(effect)
                    proxy.x, proxy.y = entity.x, entity.y
                    effect.rune_tree.on_hit(proxy, entity, context)
                knockback = getattr(effect, 'knockback', 0.0)
                if knockback:
                    dx = entity.x - effect.x
                    dy = entity.y - effect.y
                    dist = math.hypot(dx, dy) or 1.0
                    entity.x += (dx / dist) * knockback
                    entity.y += (dy / dist) * knockback
                if getattr(effect, 'apply_stun', False):
                    from logic.entities.status_effect import StatusEffect
                    entity.add_status_effect(StatusEffect('stun', 0.0, 0.7, slow_factor=0.0))

    def _stop_fire_breath(self) -> None:
        if self._fire_jet is not None:
            self._fire_jet.alive = False
            self._fire_jet = None
        self._rmb_held = False

    def _update_fire_breath(self, dt: float, visual_type: str,
                            target_x: float, target_y: float) -> None:
        if (self._fire_jet is None and self.player.can_ultimate()
                and self._breath_fuel < self.BREATH_MAX_FUEL):
            self._breath_fuel = self.BREATH_MAX_FUEL

        breathing = (
            self._rmb_held
            and visual_type == 'fire_bolt'
            and self._breath_fuel > 0.0
        )
        if not breathing:
            if self._fire_jet is not None:
                self._stop_fire_breath()
            return

        self._breath_fuel = max(0.0, self._breath_fuel - dt)
        angle = math.atan2(target_y - self.player.y, target_x - self.player.x)
        damage = self.player.damage * self.BREATH_DPS_MULT * FireBreathJet.TICK
        rune_tree = self.player.get_active_spell().rune_tree
        if self._fire_jet is None or not self._fire_jet.alive:
            self._fire_jet = FireBreathJet(self.player.x, self.player.y, angle, damage, rune_tree)
            self.active_effects.append(self._fire_jet)
        else:
            self._fire_jet.aim(self.player.x, self.player.y, angle, damage)

        if self._breath_fuel <= 0.0:
            self._stop_fire_breath()
            self.player.reset_ultimate()

    def _fire_explosion(self, target_x: float, target_y: float) -> None:
        if not self.player.can_ultimate():
            return
        damage = self.player.damage * 5.0
        if random.random() < self.player.get_crit_chance():
            damage *= 2.0
        rune_tree = self.player.get_active_spell().rune_tree
        burst = AoEBurst(target_x, target_y, damage, 170.0,
                         'fire_explosion', rune_tree, life_scale=1.6)
        self.active_effects.append(burst)
        self._stop_fire_breath()
        self._breath_fuel = 0.0
        self.player.reset_ultimate()
        self.ultimate_flash = {
            'cx': target_x, 'cy': target_y, 'radius': 170,
            'color': (255, 110, 30), 'duration': 0.4, 'name': 'FireExplosion',
        }

    def _release_air_burst(self, target_x: float, target_y: float) -> None:
        ratio = self._wind_charge_time / self.WIND_MAX_CHARGE
        self._wind_charging = False
        self._wind_charge_time = 0.0
        rune_tree = self.player.get_active_spell().rune_tree
        angle = math.atan2(target_y - self.player.y, target_x - self.player.x)
        damage = self.player.damage * (0.8 + ratio * 1.8)
        if random.random() < self.player.get_crit_chance():
            damage *= 2.0
        self.active_effects.append(
            AirBurstEffect(self.player.x, self.player.y, angle, damage, ratio, rune_tree))

    def _air_explosion(self) -> None:
        if not self.player.can_ultimate():
            return
        rune_tree = self.player.get_active_spell().rune_tree
        damage = self.player.damage * 3.0
        if random.random() < self.player.get_crit_chance():
            damage *= 2.0
        burst = AoEBurst(self.player.x, self.player.y, damage, 230.0,
                         'air_explosion', rune_tree, life_scale=1.5)
        burst.knockback = 320.0
        self.active_effects.append(burst)
        self.player.reset_ultimate()
        self.ultimate_flash = {
            'cx': self.player.x, 'cy': self.player.y, 'radius': 230,
            'color': (150, 230, 150), 'duration': 0.4, 'name': 'AirExplosion',
        }

    def _resolve_player_map_collision(self, old_x: float, old_y: float) -> None:
        if getattr(self, "noclip_mode", False):
            return
        self._resolve_entity_map_collision(self.player, old_x, old_y, reset_velocity=True)

    def _is_map_blocked(self, x: float, y: float, radius: float) -> bool:
        return self._map_collides_circle(x, y, radius)

    def _map_collides_circle(
        self,
        x: float,
        y: float,
        radius: float,
        edge_radius: float | None = None,
    ) -> bool:
        world_map = getattr(self.renderer, "world_map", None)
        if world_map is None or not hasattr(world_map, "collides_circle"):
            return False
        if edge_radius is not None and self._map_bounds_blocked(x, y, edge_radius):
            return True
        return world_map.collides_circle(x, y, radius)

    def _map_bounds_blocked(self, x: float, y: float, radius: float) -> bool:
        world_map = getattr(self.renderer, "world_map", None)
        required_attrs = ("origin_x", "origin_y", "pixel_width", "pixel_height")
        if world_map is None or not all(hasattr(world_map, attr) for attr in required_attrs):
            return False

        return (
            x - radius < world_map.origin_x
            or y - radius < world_map.origin_y
            or x + radius > world_map.origin_x + world_map.pixel_width
            or y + radius > world_map.origin_y + world_map.pixel_height
        )

    def _entity_map_collision_radius(self, entity) -> float:
        return getattr(entity, "radius", 1.0)

    def _entity_map_edge_radius(self, entity, collision_radius: float) -> float | None:
        if entity is self.player:
            return max(collision_radius, PLAYER_MAP_EDGE_RADIUS)
        return None

    def _clamp_entity_to_map_bounds(self, entity, radius: float) -> tuple[bool, bool]:
        world_map = getattr(self.renderer, "world_map", None)
        required_attrs = ("origin_x", "origin_y", "pixel_width", "pixel_height")
        if world_map is None or not all(hasattr(world_map, attr) for attr in required_attrs):
            return False, False

        map_left = world_map.origin_x
        map_top = world_map.origin_y
        map_right = map_left + world_map.pixel_width
        map_bottom = map_top + world_map.pixel_height

        if world_map.pixel_width <= radius * 2:
            new_x = (map_left + map_right) / 2
        else:
            new_x = max(map_left + radius, min(map_right - radius, entity.x))

        if world_map.pixel_height <= radius * 2:
            new_y = (map_top + map_bottom) / 2
        else:
            new_y = max(map_top + radius, min(map_bottom - radius, entity.y))

        blocked_x = new_x != entity.x
        blocked_y = new_y != entity.y
        entity.x = new_x
        entity.y = new_y
        return blocked_x, blocked_y

    def _resolve_entity_map_collision(
        self,
        entity,
        old_x: float,
        old_y: float,
        reset_velocity: bool = False,
    ) -> None:
        world_map = getattr(self.renderer, "world_map", None)
        if world_map is None or not hasattr(world_map, "collides_circle"):
            return

        radius = self._entity_map_collision_radius(entity)
        edge_radius = self._entity_map_edge_radius(entity, radius)
        target_x, target_y = entity.x, entity.y
        if target_x == old_x and target_y == old_y:
            if edge_radius is not None:
                blocked_x, blocked_y = self._clamp_entity_to_map_bounds(entity, edge_radius)
                if reset_velocity:
                    if blocked_x:
                        entity.vel_x = 0.0
                        if hasattr(entity, "dash_vel_x"):
                            entity.dash_vel_x = 0.0
                    if blocked_y:
                        entity.vel_y = 0.0
                        if hasattr(entity, "dash_vel_y"):
                            entity.dash_vel_y = 0.0
                    if (blocked_x or blocked_y) and hasattr(entity, "dash_timer"):
                        entity.dash_timer = 0.0
            return

        step_len = max(1.0, max(radius, edge_radius or radius) * 0.5)
        steps = max(
            1,
            int(math.ceil(max(abs(target_x - old_x), abs(target_y - old_y)) / step_len)),
        )
        cur_x, cur_y = old_x, old_y
        blocked_x = False
        blocked_y = False

        for i in range(1, steps + 1):
            next_x = old_x + (target_x - old_x) * i / steps
            next_y = old_y + (target_y - old_y) * i / steps

            if self._map_collides_circle(next_x, cur_y, radius, edge_radius):
                blocked_x = True
            else:
                cur_x = next_x

            if self._map_collides_circle(cur_x, next_y, radius, edge_radius):
                blocked_y = True
            else:
                cur_y = next_y

        entity.x = cur_x
        entity.y = cur_y
        if edge_radius is not None:
            clamp_blocked_x, clamp_blocked_y = self._clamp_entity_to_map_bounds(entity, edge_radius)
            blocked_x = blocked_x or clamp_blocked_x
            blocked_y = blocked_y or clamp_blocked_y
        if reset_velocity:
            if blocked_x:
                entity.vel_x = 0.0
                if hasattr(entity, "dash_vel_x"):
                    entity.dash_vel_x = 0.0
            if blocked_y:
                entity.vel_y = 0.0
                if hasattr(entity, "dash_vel_y"):
                    entity.dash_vel_y = 0.0
            if (blocked_x or blocked_y) and hasattr(entity, "dash_timer"):
                entity.dash_timer = 0.0

    def _place_entity_on_valid_map_spot(self, entity) -> None:
        radius = getattr(entity, "radius", 1.0)
        if not self._is_map_blocked(entity.x, entity.y, radius):
            return

        base_x, base_y = entity.x, entity.y
        for distance in (64, 96, 128, 192, 256, 320, 448, 576, 704):
            for i in range(16):
                angle = (i / 16) * math.tau
                x = base_x + math.cos(angle) * distance
                y = base_y + math.sin(angle) * distance
                if not self._is_map_blocked(x, y, radius):
                    entity.x = x
                    entity.y = y
                    return

    def _handle_enemy_player_collision(self, dt: float) -> None:
        for enemy in self.enemies:
            if not enemy.alive:
                continue
                
            # Kiểm tra sát thương từ vũ khí (Hitbox của lunge attack, windup)
            if getattr(enemy, 'attack_hitbox', None):
                hx, hy, hr = enemy.attack_hitbox
                dist = math.hypot(self.player.x - hx, self.player.y - hy)
                if dist <= self.player.radius + hr:
                    self.player.take_damage(getattr(enemy, "damage", CONTACT_DAMAGE * 3.0))
                    enemy.attack_hitbox = None
                    
            dist = math.hypot(self.player.x - enemy.x, self.player.y - enemy.y)
            if dist <= self.player.radius + enemy.radius:
                self.player.take_damage(getattr(enemy, "damage", CONTACT_DAMAGE) * dt)
        if self.boss and self.boss.alive:
            dist = math.hypot(self.player.x - self.boss.x, self.player.y - self.boss.y)
            if dist <= self.player.radius + self.boss.radius:
                self.player.take_damage(getattr(self.boss, "damage", CONTACT_DAMAGE) * dt)

    def _process_wave_events(self, events: dict) -> None:
        if not events:
            return
            
        hp_mult = events.get('hp_mult', 1.0)
        speed_mult = events.get('speed_mult', 1.0)
        
        if events.get('new_wave_started'):
            self.wave_notif_timer = 3.0
            w = self.wave_mgr.wave
            if w == self.wave_mgr.BOSS_WAVE:
                self.wave_notif_text = "WARNING: BOSS INCOMING!"
            elif w == 10:
                self.wave_notif_text = f"WAVE {w} - TANK ENEMIES APPEAR!"
            elif w == 5:
                self.wave_notif_text = f"WAVE {w} - FAST ENEMIES APPEAR!"
            else:
                self.wave_notif_text = f"WAVE {w}"

        for item in events.get('spawn_enemies', []):
            x, y, enemy_type = item
            if enemy_type == 'ranged':
                enemy = RangedEnemy(x, y, hp_mult, speed_mult)
            elif enemy_type == 'fast':
                enemy = FastEnemy(x, y, hp_mult, speed_mult)
            elif enemy_type == 'tank':
                enemy = TankEnemy(x, y, hp_mult, speed_mult)
            else:
                enemy = Enemy(x, y, hp_mult, speed_mult)
            self._place_entity_on_valid_map_spot(enemy)
            self.enemies.append(enemy)
                
        if events.get('spawn_boss'):
            self.boss = Boss(self.player.x + 650, self.player.y, hp_mult, speed_mult)
            self._place_entity_on_valid_map_spot(self.boss)
            
        summon_count = events.get('summon_enemies', 0)
        if summon_count and self.boss:
            for i in range(summon_count):
                angle = (i / summon_count) * 2 * math.pi
                bx    = self.boss.x + math.cos(angle) * 150
                by    = self.boss.y + math.sin(angle) * 150
                enemy = Enemy(bx, by, hp_mult, speed_mult)
                self._place_entity_on_valid_map_spot(enemy)
                self.enemies.append(enemy)

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
        info    = ult.activate(self.player, self.enemies, self.boss, context)
        self.player.reset_ultimate()
        self.ultimate_flash = info   # renderer dùng để vẽ AoE ring

    def _cheat_add_all_runes(self) -> None:
        from logic.rune.elements.fire_rune import FireRune
        from logic.rune.elements.ice_rune import IceRune
        from logic.rune.elements.lightning_rune import LightningRune
        from logic.rune.elements.poison_rune import PoisonRune
        from logic.rune.elements.wind_rune import WindRune
        from logic.rune.elements.blood_rune import BloodRune
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
            BloodRune,
            SpiralModifier,
            BounceModifier,
            SplitModifier,
            HasteRune,
        )
        for rune_cls in rune_classes:
            self.player.add_to_inventory(rune_cls())

    def _drop_xp_from_ultimate_kills(self, alive_before: set, boss_alive_before: bool) -> None:
        for enemy in self.enemies:
            if (
                id(enemy) in alive_before
                and not enemy.alive
                and not getattr(enemy, 'xp_dropped', False)
            ):
                enemy.xp_dropped = True
                self.xp_orbs.extend(enemy.drop_xp(self.player.lucky))

        if (
            boss_alive_before
            and self.boss
            and not self.boss.alive
            and not getattr(self.boss, 'xp_dropped', False)
        ):
            self.boss.xp_dropped = True
            self.xp_orbs.extend(self.boss.drop_xp(self.player.lucky))

    def _cleanup(self) -> None:
        # Xử lý sinh XP/Thịt khi quái vật hoàn tất animation chết (alive = False)
        for enemy in self.enemies:
            if not enemy.alive and not getattr(enemy, 'xp_dropped', False):
                enemy.xp_dropped = True
                self.xp_orbs.extend(enemy.drop_xp(self.player.lucky))
                
        if self.boss and not self.boss.alive and not getattr(self.boss, 'xp_dropped', False):
            self.boss.xp_dropped = True
            self.xp_orbs.extend(self.boss.drop_xp(self.player.lucky))

        self.bullets       = [b  for b  in self.bullets       if b.alive]
        self.enemies       = [e  for e  in self.enemies        if e.alive]
        self.xp_orbs       = [o  for o  in self.xp_orbs        if o.alive]
        self.enemy_bullets = [eb for eb in self.enemy_bullets  if eb.alive]
        self.active_effects = [ef for ef in self.active_effects if ef.alive]
        self.effects       = [
            effect for effect in self.effects
            if effect.get('age', 0.0) < effect.get('duration', 0.0)
        ]

    def _update_camera(self, dt: float) -> None:
        follow = min(1.0, CAMERA_FOLLOW_SPEED * dt)
        self.camera_x += (self.player.x - self.camera_x) * follow
        self.camera_y += (self.player.y - self.camera_y) * follow
        self._clamp_camera_to_map()

    def _clamp_camera_to_map(self) -> None:
        world_map = getattr(self.renderer, "world_map", None)
        required_attrs = ("origin_x", "origin_y", "pixel_width", "pixel_height")
        if world_map is None or not all(hasattr(world_map, attr) for attr in required_attrs):
            return

        zoom = max(0.01, getattr(self.renderer, "zoom", 1.0))
        half_w = SCREEN_W / (2 * zoom)
        half_h = SCREEN_H / (2 * zoom)

        map_left = world_map.origin_x
        map_top = world_map.origin_y
        map_right = map_left + world_map.pixel_width
        map_bottom = map_top + world_map.pixel_height

        if world_map.pixel_width <= half_w * 2:
            self.camera_x = (map_left + map_right) / 2
        else:
            min_x = map_left + half_w
            max_x = map_right - half_w
            self.camera_x = max(min_x, min(max_x, self.camera_x))

        if world_map.pixel_height <= half_h * 2:
            self.camera_y = (map_top + map_bottom) / 2
        else:
            min_y = map_top + half_h
            max_y = map_bottom - half_h
            self.camera_y = max(min_y, min(max_y, self.camera_y))

    def _camera_x(self) -> float: return self.camera_x
    def _camera_y(self) -> float: return self.camera_y

    def _spawn_initial_sheep(self) -> None:
        import random as _rnd
        for _ in range(8):
            angle = _rnd.uniform(0, math.tau)
            dist = _rnd.uniform(150, 900)
            sx = self.player.x + math.cos(angle) * dist
            sy = self.player.y + math.sin(angle) * dist
            sheep = Sheep(sx, sy)
            self._place_entity_on_valid_map_spot(sheep)
            self.enemies.append(sheep)

    def _spawn_sheep_randomly(self) -> None:
        import random as _rnd
        angle = _rnd.uniform(0, math.tau)
        dist = _rnd.uniform(800, 1200)
        sx = self.player.x + math.cos(angle) * dist
        sy = self.player.y + math.sin(angle) * dist
        sheep = Sheep(sx, sy)
        self._place_entity_on_valid_map_spot(sheep)
        self.enemies.append(sheep)

    # ── Vẽ ────────────────────────────────────────────────────────────────────

    def _draw(self) -> None:
        if self.state == self.STATE_MENU:
            self.menu.draw()

        elif self.state == self.STATE_SKILL_SELECT:
            self.skill_select.draw(self._dt)

        elif self.state in (self.STATE_PLAYING, self.STATE_LEVEL_UP):
            self.renderer.draw_all(
                self.player, self.enemies, self.boss,
                self.bullets, self.xp_orbs, self.enemy_bullets,
                self._camera_x(), self._camera_y(),
                effects=self.effects,
                ultimate_flash=self.ultimate_flash,
                ice_charge=self.ice_charge,
                active_effects=self.active_effects,
                dt=self._dt)
            if self._wind_charging:
                self.renderer.draw_wind_charge(
                    self.player,
                    self._wind_charge_time / self.WIND_MAX_CHARGE,
                    self._camera_x(), self._camera_y())
            self._present_game_surface()
            self.hud.draw(self.player, self.wave_mgr.get_wave_info())
            
            if self.wave_notif_timer > 0:
                alpha = min(255, max(0, int((self.wave_notif_timer / 3.0) * 255 * 2)))
                notif_surf = self.font_big.render(self.wave_notif_text, True, (255, 255, 0))
                notif_surf.set_alpha(alpha)
                self.screen.blit(notif_surf, (WINDOW_W//2 - notif_surf.get_width()//2, WINDOW_H//4))

            if self.state == self.STATE_LEVEL_UP:
                self.levelup_scr.draw(self.level_mgr.current_choices)

        elif self.state == self.STATE_RUNE_BUILDER:
            # Toàn màn hình Rune Builder (game tạm dừng)
            self.builder.draw(self.player, self._dt)

        elif self.state == self.STATE_GAME_OVER:
            self.gameover.draw(self.wave_mgr.wave, self.time_played)

        elif self.state == self.STATE_WIN:
            self.win_scr.draw(self.time_played)

    def _present_game_surface(self) -> None:
        pygame.transform.scale(self.game_surface, (WINDOW_W, WINDOW_H), self.screen)
