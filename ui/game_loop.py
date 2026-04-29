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
