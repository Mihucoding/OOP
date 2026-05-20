import math
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

        font_big   = pygame.font.SysFont(None, 64)
        font_small = pygame.font.SysFont(None, 28)

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

    # ── Khởi tạo / reset ──────────────────────────────────────────────────────

    def _init_game_objects(self):
        self.player        = Player(WORLD_CENTER_X, WORLD_CENTER_Y)
        self.enemies: list[Enemy]             = []
        self.boss:    Boss | None             = None
        self.bullets: list[Bullet]            = []
        self.enemy_bullets: list[EnemyBullet] = []
        self.xp_orbs: list[XPOrb]             = []
        self.wave_mgr       = WaveManager()
        self.level_mgr      = LevelManager()
        self.time_played    = 0.0
        self.ultimate_flash = None   # dict với cx/cy/radius/color/duration

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
        self.player.update(dt, mx, my)

        # 2. Bắn đạn player
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

        # 13. Dọn dẹp
        self._cleanup()

        # 14. Kiểm tra kết thúc
        if not self.player.alive:
            self.state = self.STATE_GAME_OVER
        if self.boss and not self.boss.alive:
            self.state = self.STATE_WIN

    # ── Helpers ───────────────────────────────────────────────────────────────

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

        context = {'enemies': self.enemies, 'bullets': self.bullets}
        extra   = rune_tree.on_fire(bullet, context)
        self.bullets.append(bullet)
        self.bullets.extend(extra)

    def _handle_bullet_collisions(self) -> None:
        context = {'enemies': self.enemies, 'bullets': self.bullets}
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
        context = {'enemies': self.enemies, 'bullets': self.bullets}
        info    = ult.activate(self.player, self.enemies, self.boss, context)
        self.player.reset_ultimate()
        self.ultimate_flash = info   # renderer dùng để vẽ AoE ring

    def _cleanup(self) -> None:
        self.bullets       = [b  for b  in self.bullets       if b.alive]
        self.enemies       = [e  for e  in self.enemies        if e.alive]
        self.xp_orbs       = [o  for o  in self.xp_orbs        if o.alive]
        self.enemy_bullets = [eb for eb in self.enemy_bullets  if eb.alive]

    def _camera_x(self) -> float: return self.player.x
    def _camera_y(self) -> float: return self.player.y

    # ── Vẽ ────────────────────────────────────────────────────────────────────

    def _draw(self) -> None:
        if self.state == self.STATE_MENU:
            self.menu.draw()

        elif self.state in (self.STATE_PLAYING, self.STATE_LEVEL_UP):
            self.renderer.draw_all(
                self.player, self.enemies, self.boss,
                self.bullets, self.xp_orbs, self.enemy_bullets,
                self._camera_x(), self._camera_y(),
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
