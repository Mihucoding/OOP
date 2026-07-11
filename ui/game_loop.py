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
from logic.entities.bullet          import Bullet
from logic.entities.wind_boomerang  import WindBoomerang
from logic.entities.enemy_bullet    import EnemyBullet
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
CAMERA_FOLLOW_SPEED = 9.5

# Tầm bay đạn Fire = Bullet.BASE_SPEED (400) * lifetime. Giảm lifetime -> đạn
# tự huỷ sớm hơn, bay gần lại (400 * 1.5 = 600px thay vì mặc định 1200px).
FIRE_BULLET_LIFETIME = 1.5
PLAYER_MAP_EDGE_RADIUS = 72.0


class GameLoop:
    """
    State machine chính:
    MENU → PLAYING ⇄ RUNE_BUILDER → LEVEL_UP → GAME_OVER | WIN
    """
    STATE_MENU           = 'menu'
    STATE_ELEMENT_SELECT = 'skill_select'
    STATE_PLAYING        = 'playing'
    STATE_LEVEL_UP       = 'level_up'
    STATE_RUNE_BUILDER   = 'rune_builder'
    STATE_GAME_OVER      = 'game_over'
    STATE_WIN            = 'win'

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
        self.builder        = RuneBuilderScreen(self.screen, font_big, font_small)
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
        self.spiral_orbit_angle = 0.0   # góc xoay vortex của lightning beam khi có TwistOfFateModifier
        self._lightning_channel_active = False  # rising-edge: FuriousOutburst chỉ nổ lúc BẮT ĐẦU giữ chuột
        if not hasattr(self, "noclip_mode"):
            self.noclip_mode = False
        self.player.noclip_mode = self.noclip_mode
        if not hasattr(self, "cheat_mode"):
            self.cheat_mode = False
        self.player.cheat_mode = self.cheat_mode
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
            self.cheat_mode = True
            self.player.cheat_mode = True
            print(f"[CHEAT] Noclip mode toggled: {self.noclip_mode}")
            return None

        if event.type == pygame.KEYDOWN and event.key == pygame.K_F8:
            self._cheat_add_all_runes()
            self.cheat_mode = True
            self.player.cheat_mode = True
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
                self._init_game_objects()
                self.skill_select.reset()
                self.state = self.STATE_ELEMENT_SELECT
            elif result == 'quit':
                return 'quit'

        elif self.state == self.STATE_ELEMENT_SELECT:
            result = self.skill_select.handle_event(event)
            if result == 'quit':
                return 'quit'
            elif isinstance(result, tuple) and result[0] == 'confirm':
                # Mỗi hệ đã chọn → 1 chiêu với lõi khóa cứng + layout cây riêng
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
                self._init_game_objects()
                self.skill_select.reset()
                self.state = self.STATE_ELEMENT_SELECT
            elif result == 'quit':
                return 'quit'

        elif self.state == self.STATE_WIN:
            result = self.win_scr.handle_event(event)
            if result == 'restart':
                self._init_game_objects()
                self.skill_select.reset()
                self.state = self.STATE_ELEMENT_SELECT
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
                if visual_type == 'wind_boomerang':
                    self._spawn_wind_boomerang(wx, wy)
                else:
                    self._spawn_bullet(wx, wy)
                self.player.reset_fire_timer()
        self._update_fire_breath(dt, visual_type, wx, wy)
        if not channeled_lightning:
            self._clear_primary_lightning_beam()
            self._lightning_channel_active = False   # rising-edge cho FuriousOutburst
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
        bullet_context = {
            'enemies': self.enemies,
            'bullets': self.bullets,
            'effects': self.effects,
            'active_effects': self.active_effects,
        }
        for b in self.bullets:
            # Đạn orbit quanh PLAYER (Self-Centered gắn thẳng root) không có
            # _orbit_target — bám tâm player mỗi frame như cũ.
            has_source = hasattr(b, '_orbit_target')
            if hasattr(b, 'player_x') and not has_source:
                b.player_x = self.player.x
                b.player_y = self.player.y
            # Tia kiếm Flash of Swords LUÔN GẮN LIỀN vào NGUỒN (boomerang/đạn)
            # đã spawn ra nó — bám vị trí nguồn mỗi frame. Nguồn chết (hết
            # pierce/hết đời) thì tia kiếm biến mất NGAY theo, không tồn tại
            # tách rời khỏi đạn.
            tgt = getattr(b, '_orbit_target', None)
            if has_source and tgt is not None:
                if getattr(tgt, 'alive', False):
                    b.player_x, b.player_y = tgt.x, tgt.y
                else:
                    b.alive = False
            b.update(dt, bullet_context)
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

        # 9b. Boss Charge — cú đấm nặng 1 lần/lượt (không nhân dt, xem check_charge_hit)
        if self.boss and self.boss.is_charging:
            dmg = self.boss.check_charge_hit(self.player.x, self.player.y, self.player.radius)
            if dmg:
                self.player.take_damage(dmg)

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
        """Kiểm tra spell có TwistOfFateModifier không (Ice/Lightning dùng nó
        làm công tắc chuyển sang đòn xoáy vòng/vòng cung — thay cho
        SpiralModifier cũ)."""
        from logic.rune.modifiers.twist_of_fate_modifier import TwistOfFateModifier
        for modifier in spell.rune_tree.modifiers:
            if isinstance(modifier, TwistOfFateModifier):
                return True
        return False

    def _find_modifier(self, spell, cls):
        """Tìm modifier kiểu `cls` bất kỳ đâu trong cây (kể cả lồng trong con).
        Dùng cho Lightning/Ice — 2 hệ không sinh Bullet nên không tự chạy
        on_fire/on_update, phải game_loop tự dò rune trong cây rồi gọi thẳng."""
        def visit(modifier):
            if isinstance(modifier, cls):
                return modifier
            for child in modifier.get_children():
                found = visit(child)
                if found is not None:
                    return found
            return None
        for modifier in spell.rune_tree.modifiers:
            found = visit(modifier)
            if found is not None:
                return found
        return None

    def _find_triggerable_modifiers(self, spell) -> list:
        """Mọi modifier có `trigger_once()` trong cây (rune loại Trigger, VD
        FuriousOutburst/RollingStone) — dùng cho Lightning/Ice/Wind, 3 hệ
        không tự chạy on_fire/on_update nên không tự trigger được. Thêm rune
        Trigger mới không cần sửa lại chỗ gọi (chỉ cần có hàm trigger_once)."""
        found = []
        def visit(modifier):
            if hasattr(modifier, 'trigger_once'):
                found.append(modifier)
            for child in modifier.get_children():
                visit(child)
        for modifier in spell.rune_tree.modifiers:
            visit(modifier)
        return found

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
            attack = ice_rune.build_spiral_charge_attack(
                self.player.x,
                self.player.y,
                target_x,
                target_y,
                self.ice_charge["held"],
            )
            attacks = [attack]
        else:
            attack = ice_rune.build_charge_attack(
                self.player.x,
                self.player.y,
                target_x,
                target_y,
                self.ice_charge["held"],
            )
            attacks = [attack]

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

        context = {'bullets': self.bullets, 'active_effects': self.active_effects}

        # Spike sạc-thả không có "quãng đường bay" → rune Trigger ĐƠN GIẢN
        # (RollingStone/FuriousOutburst/DestructivePath...) chỉ nổ đúng 1 lần
        # mỗi lần thả tay. Trigger THAM GIA cast graph (IS_CAST_GRAPH_TRIGGER,
        # VD Perfect Storm) tách riêng bên dưới để tôn trọng Spawn Count/Damage
        # của Frenetic Energy/Stars Aligned gắn vào nó — tránh nổ 2 lần.
        for trig in self._find_triggerable_modifiers(spell):
            if getattr(trig, 'IS_CAST_GRAPH_TRIGGER', False):
                continue
            spawned = trig.trigger_once(self.player.x, self.player.y, self.player.damage, context)
            if spawned is not None:
                self.bullets.append(spawned)

        # Cast graph (Frenetic Energy/Stars Aligned/Perfect Storm...) — neo vào
        # Trigger gần nhất hoặc Spell gốc, cùng luật với Fire/Wind (xem
        # RuneTree.resolve_cast_graph). Spike sạc-thả không có Bullet object
        # nên tính thủ công ở đây: Spawn Count → thêm gai quạt quanh player;
        # Damage → nhân thêm vào damage_mult có sẵn của từng gai. (Không co
        # giãn hình học/width gai theo Size — corners đã build sẵn theo width
        # cố định — chỉ Trigger con của nó mới nhận size_mult, VD bán kính
        # VortexZone của Perfect Storm.)
        root_params, trigger_params, trigger_reference, order = spell.rune_tree.resolve_cast_graph()

        base_attack = self.ice_charge.get("attack")
        held_time   = self.ice_charge.get("held", 0.0)
        base_angle  = math.atan2(base_attack["dir_y"], base_attack["dir_x"]) if base_attack else 0.0
        # Mỗi rune giữ ĐÚNG batch riêng VÀ đúng ĐỘI HÌNH riêng của nó:
        #   'line' (Stars Aligned) → gai DÀN HÀNG SONG SONG: lệch vị trí vuông
        #     góc hướng bắn, CÙNG hướng (không toả góc).
        #   'cone' (Frenetic Energy) → gai TOẢ QUẠT quanh hướng bắn.
        if base_attack is not None and not attacks[0].get("is_spiral"):
            for count, pattern, spread in root_params.batches:
                if pattern == 'line':
                    perp = base_angle + math.pi / 2
                    for i in range(count):
                        centered = i - (count - 1) / 2.0
                        ox = self.player.x + math.cos(perp) * spread * centered
                        oy = self.player.y + math.sin(perp) * spread * centered
                        attacks.append(self._build_ice_attack_at(ice_rune, ox, oy, base_angle, held_time))
                else:
                    fan_total = spread if spread > 0 else 50.0
                    fan_step  = fan_total / max(1, count)
                    for i in range(count):
                        offset_deg = (i - (count - 1) / 2.0) * fan_step
                        attacks.append(self._build_split_ice_attack(ice_rune, base_attack, offset_deg, held_time))

        # Flash of Swords trên Ice: lưỡi kiếm xuất hiện & gắn ở ĐIỂM CUỐI gai
        # băng (end_x/end_y) thay vì quanh player — spike không "bay" nên mũi
        # gai là "điểm rơi" tự nhiên nhất để neo kiếm vào.
        from logic.rune.modifiers.flash_of_swords_trigger import FlashOfSwordsTrigger
        if base_attack is not None:
            self._cap_ice_attack_at_first_enemy(base_attack)   # kiếm neo ở điểm chạm
            fos_origin = (base_attack["end_x"], base_attack["end_y"])
        else:
            fos_origin = (self.player.x, self.player.y)

        root_damage = self.player.damage * root_params.damage_mult
        firings = spell.rune_tree.resolve_trigger_firings(
            root_damage, root_params.spawn_count, trigger_params, trigger_reference, order)
        for node, base_dmg, params in firings:
            ox_c, oy_c = fos_origin if isinstance(node, FlashOfSwordsTrigger) \
                else (self.player.x, self.player.y)
            batches = spell.rune_tree._orbit_even_batches(node, params.batches)
            positions = spell.rune_tree.resolve_batch_positions(
                ox_c, oy_c, base_angle, batches)
            for tx, ty, jitter_deg in positions:
                spawned = node.trigger_once(tx, ty, base_dmg, context,
                                            angle_jitter_deg=jitter_deg,
                                            speed_mult=params.speed_mult, size_mult=params.size_mult,
                                            duration_mult=params.duration_mult, source=None)
                if spawned is not None:
                    self.bullets.append(spawned)

        for attack in attacks:
            damage = self.player.damage * attack["damage_mult"] * root_params.damage_mult
            
            if attack.get("is_spiral"):
                hits = ice_rune.targets_in_ice_spiral(attack, self.enemies)
            else:
                # Gai thẳng: dừng ở địch gần nhất (cắt cả hitbox lẫn hình gai).
                self._cap_ice_attack_at_first_enemy(attack)
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

    def _build_ice_attack_at(self, ice_rune, start_x: float, start_y: float,
                             angle: float, held_time: float) -> dict:
        """Dựng 1 gai băng bắt đầu tại (start_x, start_y) theo hướng `angle`
        (radian) — dùng cho đội hình DÀN HÀNG SONG SONG (Stars Aligned): các
        gai lệch vị trí nhưng CÙNG hướng, không toả góc."""
        target_x = start_x + math.cos(angle) * 100
        target_y = start_y + math.sin(angle) * 100
        return ice_rune.build_charge_attack(start_x, start_y, target_x, target_y, held_time)

    def _build_split_ice_attack(self, ice_rune, base_attack: dict, angle_offset: float, held_time: float) -> dict:
        base_angle = math.atan2(base_attack["dir_y"], base_attack["dir_x"])
        angle = base_angle + math.radians(angle_offset)
        target_x = self.player.x + math.cos(angle) * 100
        target_y = self.player.y + math.sin(angle) * 100
        # Không cắt theo viewport nữa: spike đạt đủ độ dài theo mức sạc ở
        # MỌI hướng (trước đây bắn dọc bị cắt ngắn vì màn hình thấp hơn rộng).
        return ice_rune.build_charge_attack(
            self.player.x,
            self.player.y,
            target_x,
            target_y,
            held_time,
        )


    def _cap_ice_attack_at_first_enemy(self, attack: dict) -> None:
        """Cắt gai băng lại tại địch GẦN NHẤT dọc trục gai (không cho xuyên
        hết): sửa end_x/end_y/length/corners tại chỗ để cả hitbox lẫn hình gai
        dừng ở điểm chạm. Không địch nào chắn đường → giữ nguyên (vươn full)."""
        sx, sy = attack["start_x"], attack["start_y"]
        dx, dy = attack["dir_x"], attack["dir_y"]   # đã chuẩn hoá trong build_charge_attack
        length = attack["length"]
        half_w = attack["width"] / 2
        nearest = None
        for enemy in self._living_targets():
            proj = (enemy.x - sx) * dx + (enemy.y - sy) * dy
            if proj < 0.0 or proj > length:
                continue
            cx = sx + dx * proj
            cy = sy + dy * proj
            if math.hypot(enemy.x - cx, enemy.y - cy) <= half_w + enemy.radius:
                if nearest is None or proj < nearest:
                    nearest = proj
        if nearest is None:
            return
        new_len = max(8.0, nearest)
        ex = sx + dx * new_len
        ey = sy + dy * new_len
        perp_x, perp_y = -dy, dx
        attack["end_x"] = ex
        attack["end_y"] = ey
        attack["length"] = new_len
        attack["corners"] = [
            (sx + perp_x * half_w, sy + perp_y * half_w),
            (ex + perp_x * half_w, ey + perp_y * half_w),
            (ex - perp_x * half_w, ey - perp_y * half_w),
            (sx - perp_x * half_w, sy - perp_y * half_w),
        ]

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
        # chain_damage/max_targets: chỉ còn dùng cho biến thể Spiral ring
        # (_execute_lightning_spiral_ring). Tia thẳng đã bỏ chain (đơn mục tiêu).
        chain_damage = primary_damage * 0.45
        max_targets = 1 + min(4, 2 + stack)
        cast_lock = 0.10

        # Cast graph (Frenetic Energy/Stars Aligned/Perfect Storm...) — neo vào
        # Trigger gần nhất hoặc Spell gốc, cùng luật với Fire/Wind/Ice (xem
        # RuneTree.resolve_cast_graph). Beam tức thời không có Bullet object
        # nên tính thủ công: Spawn Count → thêm chùm tia song song (cộng vào
        # split_angles bên dưới); Damage → nhân thêm vào primary/chain damage.
        root_params, trigger_params, trigger_reference, order = spell.rune_tree.resolve_cast_graph()
        primary_damage *= root_params.damage_mult
        chain_damage   *= root_params.damage_mult
        primary_hit_damage *= root_params.damage_mult

        context = {'bullets': self.bullets, 'active_effects': self.active_effects}

        # Beam tức thời không có "quãng đường bay" → rune Trigger ĐƠN GIẢN
        # (RollingStone/FuriousOutburst/DestructivePath...) chỉ nổ đúng 1 lần
        # lúc BẮT ĐẦU giữ chuột (rising edge), giữ lâu không nổ thêm. Trigger
        # THAM GIA cast graph (IS_CAST_GRAPH_TRIGGER, VD Perfect Storm) tách
        # riêng bên dưới để tôn trọng Spawn Count/Damage gắn vào nó.
        if not self._lightning_channel_active:
            self._lightning_channel_active = True
            for trig in self._find_triggerable_modifiers(spell):
                if getattr(trig, 'IS_CAST_GRAPH_TRIGGER', False):
                    continue
                spawned = trig.trigger_once(self.player.x, self.player.y, primary_hit_damage, context)
                if spawned is not None:
                    self.bullets.append(spawned)

            # Flash of Swords trên Lightning: lưỡi kiếm neo ở ĐIỂM CHẠM địch
            # gần nhất trên tia (tia dừng ở đó); không trúng ai → cuối tầm tia.
            from logic.rune.modifiers.flash_of_swords_trigger import FlashOfSwordsTrigger
            aim_x, aim_y = self._lightning_aim_direction(target_x, target_y)
            b_sx, b_sy = self._lightning_cast_origin(aim_x, aim_y)
            b_ex = b_sx + aim_x * LIGHTNING_BEAM_RANGE
            b_ey = b_sy + aim_y * LIGHTNING_BEAM_RANGE
            aim_hits = self._targets_in_lightning_beam(b_sx, b_sy, b_ex, b_ey)
            if aim_hits:
                t0 = aim_hits[0]
                sdx, sdy = b_ex - b_sx, b_ey - b_sy
                sl = sdx * sdx + sdy * sdy
                p = max(0.0, min(1.0, ((t0.x - b_sx) * sdx + (t0.y - b_sy) * sdy) / sl))
                fos_origin = (b_sx + sdx * p, b_sy + sdy * p)
            else:
                fos_origin = (b_ex, b_ey)

            firings = spell.rune_tree.resolve_trigger_firings(
                primary_hit_damage, root_params.spawn_count, trigger_params, trigger_reference, order)
            base_angle = math.atan2(target_y - self.player.y, target_x - self.player.x)
            for node, base_dmg, params in firings:
                ox_c, oy_c = fos_origin if isinstance(node, FlashOfSwordsTrigger) \
                    else (self.player.x, self.player.y)
                batches = spell.rune_tree._orbit_even_batches(node, params.batches)
                positions = spell.rune_tree.resolve_batch_positions(
                    ox_c, oy_c, base_angle, batches)
                for tx, ty, jitter_deg in positions:
                    spawned = node.trigger_once(tx, ty, base_dmg, context,
                                                angle_jitter_deg=jitter_deg,
                                                speed_mult=params.speed_mult, size_mult=params.size_mult,
                                                duration_mult=params.duration_mult, source=None)
                    if spawned is not None:
                        self.bullets.append(spawned)

        self.player.cast_lock_timer = cast_lock
        self.player.attack_timer = 0.18

        alive_before = {id(enemy) for enemy in self.enemies if enemy.alive}
        boss_alive_before = self.boss is not None and self.boss.alive

        has_spiral = self._has_spiral_modifier(spell)
        if has_spiral:
            return self._execute_lightning_spiral_ring(
                target_x, target_y, primary_damage, chain_damage,
                max_targets, alive_before, boss_alive_before)

        # ── Normal lightning beam ────────────────────────────────────────────
        aim_x, aim_y = self._lightning_aim_direction(target_x, target_y)

        if aim_x < 0:
            self.player.facing_dir = -1
        elif aim_x > 0:
            self.player.facing_dir = 1

        # Mỗi rune giữ ĐÚNG batch riêng VÀ đúng ĐỘI HÌNH riêng của nó. Mỗi beam
        # mô tả bằng (kind, value):
        #   ('fan',  angle_deg) → toả góc quanh player (Frenetic cone).
        #   ('line', offset_px) → SONG SONG: lệch gốc vuông góc, CÙNG hướng
        #     (Stars Aligned) — không toả góc nữa.
        beams = [('fan', 0.0)]
        for count, pattern, spread in root_params.batches:
            if pattern == 'line':
                for i in range(count):
                    beams.append(('line', spread * (i - (count - 1) / 2.0)))
            else:
                fan_total = spread if spread > 0 else 50.0
                fan_step  = fan_total / max(1, count)
                for i in range(count):
                    beams.append(('fan', (i - (count - 1) / 2.0) * fan_step))
        self._trim_primary_lightning_beams(len(beams))
        for beam_id, (kind, value) in enumerate(beams):
            if kind == 'line':
                dir_x, dir_y = aim_x, aim_y
                ox, oy = self._lightning_cast_origin(aim_x, aim_y)
                start_x = ox + (-aim_y) * value
                start_y = oy + aim_x * value
            else:
                dir_x, dir_y = self._rotated_direction(aim_x, aim_y, value)
                start_x, start_y = self._lightning_cast_origin(dir_x, dir_y)
            end_x = start_x + dir_x * LIGHTNING_BEAM_RANGE
            end_y = start_y + dir_y * LIGHTNING_BEAM_RANGE

            # Tia dừng ở địch GẦN NHẤT: không chain, không xuyên. Cắt cả damage
            # lẫn hình tia tại điểm chạm con đầu tiên trên đường tia.
            beam_hits = self._targets_in_lightning_beam(start_x, start_y, end_x, end_y)
            if beam_hits:
                target = beam_hits[0]
                seg_dx, seg_dy = end_x - start_x, end_y - start_y
                seg_len_sq = seg_dx * seg_dx + seg_dy * seg_dy
                proj = ((target.x - start_x) * seg_dx + (target.y - start_y) * seg_dy) / seg_len_sq
                proj = max(0.0, min(1.0, proj))
                end_x = start_x + seg_dx * proj
                end_y = start_y + seg_dy * proj
                target.take_damage(primary_damage)

            self._set_primary_lightning_beam(start_x, start_y, end_x, end_y, beam_id=beam_id, vortex=False)

        self._drop_xp_from_ultimate_kills(alive_before, boss_alive_before)
        return True

    def _execute_lightning_spiral_ring(
        self,
        target_x: float,
        target_y: float,
        primary_damage: float,
        chain_damage: float,
        max_targets: int,
        alive_before: set,
        boss_alive_before: bool,
    ) -> bool:
        """Vòng cung tĩnh (Vortex Ring) khi Lightning có TwistOfFateModifier — thay
        vì bắn tia thẳng, tia sét khép thành vòng cung/vòng tròn bao quanh
        player. Trước đây tách thành class `LightningSpiralAttack` riêng dưới
        `logic/abilities/`, nhưng nó chỉ gọi từ ĐÚNG 1 chỗ và thao tác thẳng
        lên state của GameLoop (không phải logic thuần) — vi phạm quy tắc
        `logic/` không được phụ thuộc `ui/`, nên đưa lại thành method ở đây."""
        # Bán kính thu nhỏ lại để bao sát người hơn (như yêu cầu "thu nhỏ bán kính")
        radius = LIGHTNING_BEAM_RANGE * 0.55

        # 1. Tính toán quỹ đạo vòng cung tĩnh
        cx, cy = self.player.x, self.player.y
        aim_x, aim_y = self._lightning_aim_direction(target_x, target_y)
        orbit_angle = math.atan2(aim_y, aim_x)

        # Khoảng hở GAP trong renderer là 0.7. Góc bắt đầu vòng cung là orbit_angle + 0.35.
        start_angle = orbit_angle + 0.35

        # Điểm bắt đầu vòng cung để tia thẳng nối vào (link point)
        link_x = cx + math.cos(start_angle) * radius
        link_y = cy + math.sin(start_angle) * radius

        # Điểm tâm khoảng hở để UI biết cách xoay vòng cung
        gap_x = cx + math.cos(orbit_angle) * radius
        gap_y = cy + math.sin(orbit_angle) * radius

        # Xóa các beam cũ. Ta cần 2 beam: 1 tia thẳng, 1 vòng cung.
        self._trim_primary_lightning_beams(2)

        # Tia 1: Tia thẳng xuất phát từ nhân vật nối khít vào điểm BẮT ĐẦU của đường tròn
        self._set_primary_lightning_beam(cx, cy, link_x, link_y, beam_id=0, vortex=False)

        # Tia 2: Vòng cung khép kín bao quanh nhân vật
        self._set_primary_lightning_beam(cx, cy, gap_x, gap_y, beam_id=1, vortex=True)

        if aim_x < 0:
            self.player.facing_dir = -1
        elif aim_x > 0:
            self.player.facing_dir = 1

        # 2. Xử lý sát thương (Tìm quái trong bán kính orbit)
        ring_hits = self._targets_in_vortex(cx, cy, radius)
        for i, target in enumerate(ring_hits[:max_targets]):
            dmg = primary_damage if i == 0 else chain_damage
            target.take_damage(dmg)

        # 3. Rớt XP nếu quái chết
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
        if bullet.visual_type == 'fire_bolt':
            bullet.LIFETIME = FIRE_BULLET_LIFETIME   # giảm tầm bay đạn Fire

        context = {
            'enemies': self.enemies,
            'bullets': self.bullets,
            'effects': self.effects,
            'active_effects': self.active_effects,
        }
        extra   = rune_tree.on_fire(bullet, context)
        for b in extra:
            # Bản sao từ Spawn Count (Frenetic/Stars Aligned) chưa có
            # visual_type riêng -> kế thừa hình dạng đạn chính. Đạn do TRIGGER
            # tạo ra (Flash of Swords, RollingStone, FuriousOutburst...) đã tự
            # set visual_type riêng trong trigger_once() -> KHÔNG ghi đè, nếu
            # không tia kiếm sẽ hiện lại thành hình viên đạn thường.
            if not hasattr(b, 'visual_type'):
                b.visual_type = bullet.visual_type
            if not hasattr(b, 'is_crit'):
                b.is_crit = is_crit
            if b.visual_type == 'fire_bolt':
                b.LIFETIME = FIRE_BULLET_LIFETIME   # bản sao Fire cũng bay gần lại
        self.bullets.append(bullet)
        self.bullets.extend(extra)

    def _handle_bullet_collisions(self) -> None:
        context = {
            'enemies': self.enemies,
            'bullets': self.bullets,
            'effects': self.effects,
            'active_effects': self.active_effects,
        }
        for bullet in self.bullets:
            if not bullet.alive:
                continue
            pierce   = getattr(bullet, 'pierce', False)
            hit_ids  = getattr(bullet, '_hit_ids', None)
            for enemy in self.enemies:
                if not enemy.alive:
                    continue
                if pierce and hit_ids is not None and id(enemy) in hit_ids:
                    continue
                dist = math.hypot(bullet.x - enemy.x, bullet.y - enemy.y)
                if dist <= bullet.radius + enemy.radius:
                    result = bullet.on_hit(enemy, context)
                    if result is False:
                        continue
                    enemy.take_damage(bullet.damage)
                    if not bullet.alive:
                        self._spawn_impact(bullet)
                        break
                    elif pierce:
                        self._spawn_wind_hit(bullet)
                    else:
                        break
            if not bullet.alive:
                continue
            if self.boss and self.boss.alive:
                hit_ids = getattr(bullet, '_hit_ids', None)
                if pierce and hit_ids is not None and id(self.boss) in hit_ids:
                    continue
                dist = math.hypot(bullet.x - self.boss.x, bullet.y - self.boss.y)
                if dist <= bullet.radius + self.boss.radius:
                    result = bullet.on_hit(self.boss, context)
                    if result is not False:
                        self.boss.take_damage(bullet.damage)
                        if not bullet.alive:
                            self._spawn_impact(bullet)
                        elif pierce:
                            self._spawn_wind_hit(bullet)

    def _spawn_wind_boomerang(self, target_x: float, target_y: float) -> None:
        import random as _rnd
        spell     = self.player.get_active_spell()
        rune_tree = spell.rune_tree
        damage    = self.player.damage
        is_crit   = _rnd.random() < self.player.get_crit_chance()
        if is_crit:
            damage *= 2.0

        boomerang = WindBoomerang(
            self.player.x, self.player.y,
            target_x, target_y,
            damage, rune_tree,
        )
        boomerang.is_crit = is_crit

        # Boomerang giờ đi qua rune_tree.on_fire() y hệt Bullet của Fire — mọi
        # cast-graph rune (Frenetic Energy/Stars Aligned/Perfect Storm...) đều
        # chạy chung 1 đường, không cần code Trigger thủ công riêng cho Wind
        # nữa (RuneTree tự nhân bản đúng class WindBoomerang).
        context = {
            'enemies': self.enemies,
            'bullets': self.bullets,
            'effects': self.effects,
            'active_effects': self.active_effects,
        }
        extra = rune_tree.on_fire(boomerang, context)
        for b in extra:
            b.is_crit = is_crit
        self.bullets.append(boomerang)
        self.bullets.extend(extra)

    def _spawn_wind_hit(self, bullet) -> None:
        self.effects.append({
            'kind': 'wind_hit',
            'x': bullet.x,
            'y': bullet.y,
            'duration': 0.38,
            'age': 0.0,
        })

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
            'active_effects': self.active_effects,
        }
        for effect in self.active_effects:
            if not effect.alive:
                continue
            if hasattr(effect, 'apply_pull'):
                effect.apply_pull(self.enemies, self.boss)
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
        if self.boss and self.boss.alive and not self.boss.is_charging:
            # Lúc đang charge KHÔNG cộng thêm dame chạm thường — charge có
            # cú đấm riêng (check_charge_hit, 1 lần/lượt) để tránh cộng dồn
            # 2 loại dame cùng lúc khi player đứng trong đường charge.
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
            'active_effects': self.active_effects,
        }
        info    = ult.activate(self.player, self.enemies, self.boss, context)
        self.player.reset_ultimate()
        self.ultimate_flash = info   # renderer dùng để vẽ AoE ring

    def _cheat_add_all_runes(self) -> None:
        # Chỉ thêm modifier rune vào kho (element đã chọn lúc đầu game).
        from logic.leveling.level_manager import ALL_RUNES
        for rune_cls in ALL_RUNES:
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

        elif self.state == self.STATE_ELEMENT_SELECT:
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
