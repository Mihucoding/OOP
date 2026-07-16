import math
import os
import random
import pygame

from logic.entities.player       import Player
from logic.entities.enemy        import Enemy
from logic.entities.ranged_enemy import RangedEnemy
from logic.entities.fast_enemy   import FastEnemy
from logic.entities.tank_enemy   import TankEnemy
from logic.entities.dummy_enemy   import DummyEnemy
from logic.entities.boss         import Boss
from logic.entities.bullet          import Bullet
from logic.entities.wind_boomerang  import WindBoomerang
from logic.entities.enemy_bullet    import EnemyBullet
from logic.entities.attack_effect import (
    AoEBurst,
    FireBreathJet,
    ImpactEffect,
    _HitProxy,
)
from logic.entities.xp_orb       import XPOrb
from logic.wave.wave_manager     import WaveManager
from logic.leveling.level_manager import LevelManager
from ui.renderer                  import Renderer, SCREEN_W, SCREEN_H, WINDOW_W, WINDOW_H, ZOOM
from ui.audio                     import AudioManager
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
from logic.rune.elements.lightning_rune import LightningRune

FPS            = 60
WORLD_CENTER_X = 0.0
WORLD_CENTER_Y = 0.0
CONTACT_DAMAGE = 15.0   # HP/s khi quái chạm player
# Quy đổi từ chỉ số hiển thị trên thẻ Lightning (LightningRune.LENGTH/DURATION)
# — đổi thẻ là đổi luôn gameplay thật, không cần sửa 2 chỗ.
LIGHTNING_OVERLOAD_FILL_RATE = 1.0 / LightningRune.DURATION
LIGHTNING_OVERLOAD_DECAY_RATE = 0.42
LIGHTNING_OVERLOAD_READY_AT = 0.20
LIGHTNING_OVERLOAD_FX_INTERVAL = 0.10
LIGHTNING_OVERLOAD_FX_RADIUS = 42.0
LIGHTNING_BEAM_RANGE = LightningRune.LENGTH * LightningRune.LENGTH_TO_PX
LIGHTNING_BEAM_HIT_RADIUS = 24.0
CAMERA_FOLLOW_SPEED = 9.5

# Tầm bay đạn Fire = Bullet.BASE_SPEED (400) * lifetime. Giảm lifetime -> đạn
# tự huỷ sớm hơn, bay gần lại (400 * 0.65 = 260px) — Fire là hệ đánh nhanh
# tầm gần (đổi lại bằng SpellBuild.FIRE_BASE_FIRE_RATE thấp hơn hẳn).
FIRE_BULLET_LIFETIME = 0.65
PLAYER_MAP_EDGE_RADIUS = 72.0

# Animation vung tay bắn lửa (SATYR hàng 4, 7 khung) — khớp với
# renderer._get_player_frame_ms("cast_fire"). Bắn đúng lúc khung 4 (vệt vàng
# rõ nhất), đứng im hết animation rồi mới đi tiếp được.
FIRE_CAST_FRAME_MS      = 40.0
FIRE_CAST_FRAME_COUNT   = 7
FIRE_CAST_RELEASE_FRAME = 4
FIRE_CAST_TOTAL_MS      = FIRE_CAST_FRAME_MS * FIRE_CAST_FRAME_COUNT

# Animation charge điện (SATYR hàng 10, 10 khung) — khớp với
# renderer.CAST_LIGHTNING_FRAME_MS. Tia chỉ THỰC SỰ xuất hiện (damage + vẽ
# beam) khi charge tới khung RELEASE_FRAME (miệng đã hé đủ) — giữ chuột trước
# đó chỉ đứng im vung tay, chưa có tia nào cả.
LIGHTNING_CAST_FRAME_MS      = 35.0
LIGHTNING_CAST_RELEASE_FRAME = 7


class _LiveAnchor:
    """Điểm neo 'sống' — game_loop cập nhật x/y của nó MỖI FRAME trong lúc
    channel Lightning, theo đúng điểm chạm hiện tại của tia (đổi hướng khi
    người chơi đảo chuột). Dùng làm `source` cho Flash of Swords khi bắn từ
    Ice/Lightning (không có Bullet nguồn thật) để tia kiếm bám tia điện thay
    vì đứng im tại điểm chạm lúc vừa charge xong."""
    __slots__ = ('x', 'y', 'alive')

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.alive = True


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
        """
        Khởi tạo hệ thống Pygame và các thành phần cốt lõi của GameLoop.
        Quá trình khởi tạo bao gồm:
        - Khởi tạo Pygame và thiết lập kích thước cửa sổ (WINDOW_W x WINDOW_H).
        - Tạo `game_surface` (bộ đệm hình ảnh ảo) lớn hơn cửa sổ thật dựa trên tỷ lệ ZOOM, để vẽ mọi thứ ở pixel gốc rồi thu nhỏ 1 lần.
        - Khởi tạo đồng hồ `clock` để kiểm soát tốc độ khung hình (FPS).
        - Tải font chữ và con trỏ chuột tùy chỉnh.
        - Tạo các lớp quản lý giao diện (Renderer, HUD, MainMenu, LevelUpScreen, v.v.).
        - Khởi tạo `_init_game_objects()` để nạp các thực thể logic ban đầu.
        - Đặt trạng thái ban đầu (`self.state`) là Menu chính.

        👉 BƯỚC TIẾP THEO (Bước 3): Đọc hàm `_init_game_objects` ngay bên dưới để xem game reset lại thế giới như thế nào.
        """
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        # game_surface to hơn SCREEN_W x SCREEN_H theo đúng tỉ lệ ZOOM (camera
        # lùi xa) — mọi thứ vẽ ở kích thước gốc (native pixel) lên buffer to
        # này, rồi _present_game_surface scale NGUYÊN buffer xuống window 1
        # lần duy nhất, thay vì scale từng sprite riêng (tránh viền nham
        # nhở/mờ ở tỉ lệ lẻ). Xem ui/renderer.py: ZOOM, world_to_screen().
        buffer_w = round(SCREEN_W / ZOOM)
        buffer_h = round(SCREEN_H / ZOOM)
        self.game_surface = pygame.Surface((buffer_w, buffer_h)).convert()
        pygame.display.set_caption("Rune Craft Roguelike")
        self._load_custom_cursor()
        self.clock = pygame.time.Clock()
        self.audio = AudioManager()

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
        self.game_mode = 'normal'   # 'normal' | 'creative' (set khi rời menu)
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
        """
        Khởi tạo hoặc đặt lại (reset) toàn bộ các thực thể (entities) trong trò chơi.
        Hàm này được gọi khi mới vào game hoặc khi người chơi chọn "Chơi Lại" (Restart).
        Các đối tượng được khởi tạo bao gồm:
        - `self.player`: Nhân vật người chơi (vị trí gốc ở giữa bản đồ).
        - Các danh sách: `enemies`, `bullets`, `enemy_bullets`, `xp_orbs`, `effects`.
        - `WaveManager` (chịu trách nhiệm đẻ quái theo đợt) và `LevelManager` (quản lý XP/Cấp độ).
        - Nếu ở chế độ 'creative' (test), tự động bật god mode và tắt chế độ sinh quái (wave tự động).

        👉 BƯỚC TIẾP THEO (Bước 4): Mọi thứ đã sẵn sàng. Trò chơi bắt đầu chạy. Hãy tìm hàm `run` để xem vòng lặp vô tận.
        """
        self.player        = Player(WORLD_CENTER_X, WORLD_CENTER_Y)
        self.enemies: list[Enemy]             = []
        self.boss:    Boss | None             = None
        self.bullets: list[Bullet]            = []
        self.enemy_bullets: list[EnemyBullet] = []
        self.xp_orbs: list[XPOrb]             = []
        self.effects: list[dict]               = []
        self.active_effects: list              = []
        self.damage_numbers: list[dict]        = []   # số dmg bay lên khi quái trúng đòn
        self._footstep_timer    = 0.0     # đếm nhịp phát tiếng bước chân
        self._fire_cast_active  = False   # đang vung tay bắn lửa (đứng im)?
        self._fire_cast_elapsed = 0.0     # ms đã trôi qua trong lượt vung tay
        self._fire_cast_fired   = False   # đã bắn đạn ở khung release chưa
        self._fire_cast_target  = (0.0, 0.0)
        self.wave_mgr       = WaveManager()
        self.level_mgr      = LevelManager()
        self.time_played    = 0.0
        self.ultimate_flash = None   # dict với cx/cy/radius/color/duration
        self.overload_fx_timer = 0.0
        self.ice_charge = None
        self._rmb_held         = False
        self._last_rmb_down    = -999.0
        self._breath_fuel      = self.BREATH_MAX_FUEL
        self._fire_jet         = None
        self.spiral_orbit_angle = 0.0   # góc xoay vortex của lightning beam khi có TwistOfFateModifier
        self._lightning_channel_active = False  # rising-edge: đang giữ chuột channel Lightning
        self._lightning_windup_elapsed = 0.0    # giây kể từ lúc BẮT ĐẦU giữ chuột (đợi hết charge mới có tia)
        self._lightning_cast_fired     = False  # đã bắn tia + trigger 1-lần-mỗi-channel chưa
        self._lightning_fos_anchor     = None   # _LiveAnchor cho Flash of Swords bám tia mỗi frame
        if not hasattr(self, "noclip_mode"):
            self.noclip_mode = False
        self.player.noclip_mode = self.noclip_mode
        if not hasattr(self, "cheat_mode"):
            self.cheat_mode = False
        self.player.cheat_mode = self.cheat_mode

        # ── Creative / Test mode ─────────────────────────────────────────────
        self.creative_mode   = (self.game_mode == 'creative')
        self.wave_auto       = not self.creative_mode   # creative: tắt wave tự động
        self.show_creative_help = True                  # panel hướng dẫn (F1 bật/tắt)
        self._combo_index    = -1                        # tổ hợp rune đang nạp (-1 = chưa)
        self._combo_picker_open  = False                 # bảng chọn tổ hợp rune (phím C)
        self._combo_picker_rects: list = []              # [(rect, idx)] để bắt click
        self.player.god_mode = self.creative_mode        # bất tử mặc định trong creative
        # Đảm bảo player spawn tại vị trí hợp lệ, không bị kẹt trong tile cản
        self._place_entity_on_valid_map_spot(self.player)
        self.camera_x = self.player.x
        self.camera_y = self.player.y
        self._clamp_camera_to_map()
        self.wave_notif_timer = 0.0
        self.wave_notif_text = ""

    DOUBLE_TAP_TIME = 0.30
    BREATH_MAX_FUEL = 2.5
    BREATH_DPS_MULT = 1.6
    FOOTSTEP_INTERVAL = 0.32   # giây giữa 2 tiếng bước chân khi di chuyển

    # ── Vòng lặp chính ────────────────────────────────────────────────────────

    def run(self) -> None:
        """
        Vòng lặp chính của trò chơi (Main Game Loop).
        Hoạt động liên tục với tốc độ FPS được định sẵn (60 khung hình/giây).
        Quy trình mỗi khung hình (frame):
        1. Tính toán delta time (`dt`) - thời gian trôi qua giữa 2 frame (dùng để nhân với tốc độ di chuyển).
        2. Bắt các sự kiện chuột/bàn phím qua `pygame.event.get()` và gọi `_handle_event()`.
        3. Cập nhật logic trò chơi bằng cách gọi `self._update(dt)`.
        4. Vẽ mọi thứ lên màn hình bằng cách gọi `self._draw()`.
        5. Đẩy frame vừa vẽ ra cửa sổ bằng `pygame.display.flip()`.

        👉 BƯỚC TIẾP THEO (Bước 5): Mọi frame đều bắt đầu bằng việc đọc phím bấm. Hãy xem hàm `_handle_event` ngay bên dưới.
        """
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
        """
        Xử lý sự kiện bàn phím và chuột tương ứng với trạng thái (state) hiện tại của game.
        
        Tùy thuộc vào `self.state`, sự kiện có thể được nhường (delegate) cho các màn hình khác:
        - STATE_PLAYING: Xử lý các phím chuyển chiêu (Q/E), lướt (Space), đổi chế độ cheat (F8/F9), kích hoạt ultimate (Chuột phải), bật màn hình Builder (Tab/Esc).
        - STATE_RUNE_BUILDER: Nhường cho `self.builder.handle_event()`.
        - STATE_MENU: Nhường cho `self.menu.handle_event()`.
        - STATE_ELEMENT_SELECT, STATE_LEVEL_UP, STATE_GAME_OVER, STATE_WIN: Nhường tương ứng.
        
        Trả về 'quit' nếu người chơi đóng cửa sổ.

        👉 BƯỚC TIẾP THEO (Bước 6): Quá trình bắt phím cụ thể diễn ra trong InputHandler. Hãy mở file [ui/input_handler.py](file:///c:/Users/acer/Downloads/OOP-mihu_branch/ui/input_handler.py) và xem hàm `get_move_direction`.
        """
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

        # ── Phím tắt Creative / Test mode ────────────────────────────────────
        if (getattr(self, 'creative_mode', False)
                and self.state == self.STATE_PLAYING
                and event.type == pygame.KEYDOWN):
            if self._handle_creative_key(event.key):
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

        # Bảng chọn tổ hợp rune đang mở → click chọn dòng, nuốt mọi click chuột
        # (không cho bắn/ultimate lúc đang thao tác trên bảng)
        if (self.state == self.STATE_PLAYING and getattr(self, 'creative_mode', False)
                and self._combo_picker_open and event.type == pygame.MOUSEBUTTONDOWN):
            if event.button == 1:
                self._combo_picker_click(event.pos)
            return None

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
                else:
                    self._activate_ultimate()
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 3:
                self._rmb_held = False

        # Rune Builder — nhường event cho builder xử lý
        if self.state == self.STATE_RUNE_BUILDER:
            if self.builder.handle_event(event, self.player):
                self.state = self.STATE_PLAYING
            return None

        # Các state khác
        if self.state == self.STATE_MENU:
            result = self.menu.handle_event(event)
            if result in ('start_normal', 'start_creative'):
                self.game_mode = 'creative' if result == 'start_creative' else 'normal'
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
        """
        Cập nhật toàn bộ logic vật lý, toán học, và xử lý va chạm của trò chơi.
        Hàm này CHỈ CHẠY khi `self.state == STATE_PLAYING`.
        
        Thứ tự thực hiện:
        1. Cộng dồn thời gian chơi (`time_played`).
        2. Di chuyển người chơi dựa trên InputHandler.
        3. Kiểm tra người chơi bắn đạn (Chuột trái) và sinh đạn tương ứng.
        4. Cập nhật vị trí của toàn bộ Quái vật (Enemy) và Boss đuổi theo người chơi.
        5. Cập nhật vị trí và quỹ đạo của Đạn (đạn người chơi và đạn quái).
        6. Kiểm tra va chạm: Đạn trúng quái, Quái chạm người chơi, Đạn quái chạm người chơi.
        7. Cập nhật hạt kinh nghiệm (XP Orbs) và kiểm tra hút kinh nghiệm. Nếu đủ XP -> Đổi state sang LEVEL_UP.
        8. Gọi WaveManager để sinh thêm quái mới (nếu đang ở chế độ thường).
        9. Kiểm tra điều kiện Thắng/Thua (HP = 0 -> GAME_OVER, Boss chết -> WIN).

        👉 BƯỚC TIẾP THEO (Bước 8): Khi update, việc đầu tiên là di chuyển nhân vật. Hãy mở file [logic/entities/player.py](file:///c:/Users/acer/Downloads/OOP-mihu_branch/logic/entities/player.py) và đọc hàm `update`.
        """
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
        self._update_footsteps(dt, old_x, old_y)

        # 2. Bắn đạn player (khoá bắn khi đang mở bảng chọn tổ hợp rune)
        channeled_lightning = False
        firing = self.input.is_firing() and not (
            self.creative_mode and self._combo_picker_open)
        spell = self.player.get_active_spell()
        visual_type = spell.rune_tree.get_visual_type()
        wx, wy = self.input.get_mouse_world_pos(
            self._camera_x(), self._camera_y(), self.renderer.zoom)
        ice_rune = self._get_ice_rune(spell)
        if ice_rune is not None:
            self._update_ice_charge(dt, wx, wy, firing, ice_rune, spell)
        else:
            self._cancel_ice_charge()

        # Fire: chỉ huỷ cast khi KHÔNG còn cầm hệ lửa nữa (đổi chiêu/đổi hệ) —
        # tap (click rồi nhả chuột ngay) vẫn phải bắn được, không bắt buộc giữ
        # chuột hết animation mới bắn. Cast đã bắt đầu (do 1 lần click) sẽ tự
        # chạy hết tới khung release dù chuột đã nhả trước đó.
        # Khoá bắn khi mở bảng chọn tổ hợp: huỷ cả cast lửa đang dở để không có
        # phát nào lọt ra khi đang thao tác trên bảng.
        picker_lock = self.creative_mode and self._combo_picker_open
        fire_bolt_ready = ice_rune is None and visual_type == 'fire_bolt' and not picker_lock
        if not fire_bolt_ready:
            self._cancel_fire_cast()

        if firing and ice_rune is None:
            if self._get_lightning_rune(spell):
                channeled_lightning = self._channel_lightning_attack(wx, wy, dt)
            elif visual_type == 'fire_bolt':
                self._update_fire_cast(dt, wx, wy)
            elif self.player.can_fire():
                if visual_type == 'wind_boomerang':
                    self._spawn_wind_boomerang(wx, wy)
                else:
                    self._spawn_bullet(wx, wy)
                    self.audio.play("fire_spray")
                self.player.reset_fire_timer()
        elif fire_bolt_ready and self._fire_cast_active:
            self._update_fire_cast(dt, wx, wy)
        self._update_fire_breath(dt, visual_type, wx, wy)
        if not channeled_lightning:
            self._clear_primary_lightning_beam()
            self._lightning_channel_active = False   # rising-edge cho FuriousOutburst
            self._lightning_cast_fired     = False
            self._lightning_fos_anchor     = None
            if self.player.cast_anim == 'lightning':
                self.player.cast_anim = None
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
            # nguồn riêng (_orbit_target là None hoặc không tồn tại) — bám
            # tâm player mỗi frame như cũ. Lưu ý: KHÔNG dùng hasattr() để
            # check, vì Flash of Swords luôn SET thuộc tính này (kể cả khi
            # source=None cho case Ice/Lightning) — hasattr sẽ luôn True và
            # vô tình bỏ qua nhánh bám-player bên dưới.
            tgt = getattr(b, '_orbit_target', None)
            if tgt is None:
                if hasattr(b, 'player_x'):
                    b.player_x = self.player.x
                    b.player_y = self.player.y
            else:
                # Tia kiếm Flash of Swords LUÔN GẮN LIỀN vào NGUỒN (boomerang/
                # đạn thật, hoặc anchor sống theo tia Ice/Lightning) đã spawn
                # ra nó — bám vị trí nguồn mỗi frame. Nguồn chết (hết pierce/
                # hết đời) thì tia kiếm biến mất NGAY theo, không tồn tại
                # tách rời khỏi đạn.
                if getattr(tgt, 'alive', False):
                    b.player_x, b.player_y = tgt.x, tgt.y
                else:
                    b.alive = False
            old_x, old_y = b.x, b.y
            b.update(dt, bullet_context)
            self._update_bullet_wall_bounce(b, old_x, old_y)
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
                leveled = self.player.add_xp(orb.value)
                # Creative: không mở màn lên cấp (nạp rune bằng phím thay vì thẻ)
                if leveled and not self.creative_mode:
                    self.level_mgr.trigger_level_up(self.wave_mgr.wave,
                                                     self.player)
                    self.state = self.STATE_LEVEL_UP

        # 11. Wave manager (creative: tắt spawn tự động, tự bấm phím spawn)
        if self.wave_auto:
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
        for dmg_num in self.damage_numbers:
            dmg_num['age'] += dt
            dmg_num['y']   += dmg_num['vy'] * dt

        if self.wave_notif_timer > 0:
            self.wave_notif_timer -= dt

        # 13. Dọn dẹp
        self._cleanup()

        # 14. Kiểm tra kết thúc (creative: không thắng/thua, cứ ở trong arena)
        if not self.creative_mode:
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
        return self._find_modifier_in_tree(spell.rune_tree, cls)

    def _find_modifier_in_tree(self, rune_tree, cls):
        """Giống _find_modifier nhưng nhận thẳng RuneTree — dùng cho Bullet/
        WindBoomerang (bullet.rune_tree là RuneTree, không phải SpellBuild)."""
        def visit(modifier):
            if isinstance(modifier, cls):
                return modifier
            for child in modifier.get_children():
                found = visit(child)
                if found is not None:
                    return found
            return None
        for modifier in rune_tree.modifiers:
            found = visit(modifier)
            if found is not None:
                return found
        return None

    def _find_all_modifiers_in_tree(self, rune_tree, cls) -> list:
        """Giống _find_modifier_in_tree nhưng trả về TẤT CẢ modifier kiểu
        `cls` tìm được (không dừng ở bản đầu tiên) — dùng khi rune loại đó
        có thể được gắn NHIỀU BẢN RIÊNG BIỆT (VD Hit-And-Run, tối đa
        MAX_COPIES_PER_RUNE=2 bản độc lập, mỗi bản stack=1 riêng — không gộp
        thành 1 node stack=2), mỗi bản cộng dồn hiệu ứng riêng của nó."""
        found = []
        def visit(modifier):
            if isinstance(modifier, cls):
                found.append(modifier)
            for child in modifier.get_children():
                visit(child)
        for modifier in rune_tree.modifiers:
            visit(modifier)
        return found

    def _hit_and_run_bounce_max(self, rune_tree) -> int:
        """Tổng số lượt phản xạ tường tối đa — cộng dồn MAX_BOUNCE*stack qua
        MỌI bản HitAndRunModifier có trong cây (có thể gắn 2 bản độc lập)."""
        from logic.rune.modifiers.hit_and_run_modifier import HitAndRunModifier
        mods = self._find_all_modifiers_in_tree(rune_tree, HitAndRunModifier)
        return sum(m.MAX_BOUNCE * m.stack for m in mods)

    def _find_destructive_path_modifiers(self, rune_tree) -> list:
        """Ice/Lightning không có Bullet để tự chạy on_update() nên không tự
        rải vệt lửa được — game_loop tự tìm rune này trong cây rồi gọi
        leave_trail_along() thủ công với 2 đầu mút gai/tia (xem
        DestructivePathModifier.leave_trail_along)."""
        from logic.rune.modifiers.destructive_path_modifier import DestructivePathModifier
        return self._find_all_modifiers_in_tree(rune_tree, DestructivePathModifier)

    def _find_triggerable_modifiers(self, spell) -> list:
        """Mọi modifier có `trigger_once()` trong cây (rune loại Trigger, VD
        FuriousOutburst/RollingStone) — dùng cho Lightning/Ice/Wind, 3 hệ
        không tự chạy on_fire/on_update nên không tự trigger được. Thêm rune
        Trigger mới không cần sửa lại chỗ gọi (chỉ cần có hàm trigger_once)."""
        found = []
        def visit(modifier):
            if hasattr(modifier, 'trigger_once'):
                found.append(modifier)
            # Trigger OWNS_SUBTREE (Furious Outburst/Rolling Stone): nhánh con áp
            # lên đạn phụ của nó (xử lý qua _attach_subtree_and_fire), KHÔNG tự
            # trigger độc lập ở tâm player → dừng đệ quy tại đây.
            if getattr(modifier, 'OWNS_SUBTREE', False):
                return
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

        self.audio.play("ice_barrage")

        stack = getattr(ice_rune, "element_stack", 1)
        boss_alive_before = self.boss is not None and self.boss.alive
        enemy_alive_before = {id(enemy) for enemy in self.enemies if enemy.alive}
        damaged_targets = set()

        context = {'bullets': self.bullets, 'active_effects': self.active_effects}

        base_attack = self.ice_charge.get("attack")
        held_time   = self.ice_charge.get("held", 0.0)
        base_angle  = math.atan2(base_attack["dir_y"], base_attack["dir_x"]) if base_attack else 0.0
        dir_x, dir_y = (base_attack["dir_x"], base_attack["dir_y"]) if base_attack else \
            (math.cos(base_angle), math.sin(base_angle))

        # Spike sạc-thả không có "quãng đường bay" → rune Trigger ĐƠN GIẢN
        # (RollingStone/FuriousOutburst...) chỉ nổ đúng 1 lần mỗi lần thả tay.
        # Trigger THAM GIA cast graph (IS_CAST_GRAPH_TRIGGER, VD Perfect Storm)
        # tách riêng bên dưới để tôn trọng Spawn Count/Damage của Frenetic
        # Energy/Stars Aligned gắn vào nó — tránh nổ 2 lần. DestructivePath
        # KHÔNG qua vòng lặp này nữa (không có trigger_once) — rải vệt lửa
        # dọc suốt chiều dài gai băng riêng ở dưới, xem trail_mods.
        for trig in self._find_triggerable_modifiers(spell):
            if getattr(trig, 'IS_CAST_GRAPH_TRIGGER', False):
                continue
            spawned = trig.trigger_once(self.player.x, self.player.y, self.player.damage, context,
                                        dir_x=dir_x, dir_y=dir_y)
            if spawned is not None:
                self.bullets.append(spawned)
                # Nhánh con (VD Flash of Swords) áp lên chính đạn phụ (cầu lửa/đá)
                if getattr(trig, 'OWNS_SUBTREE', False):
                    self.bullets.extend(trig._attach_subtree_and_fire(spawned, context))

        # Cast graph (Frenetic Energy/Stars Aligned/Perfect Storm...) — neo vào
        # Trigger gần nhất hoặc Spell gốc, cùng luật với Fire/Wind (xem
        # RuneTree.resolve_cast_graph). Spike sạc-thả không có Bullet object
        # nên tính thủ công ở đây: Spawn Count → thêm gai quạt quanh player;
        # Damage → nhân thêm vào damage_base (sát thương tuyệt đối) có sẵn của từng gai. (Không co
        # giãn hình học/width gai theo Size — corners đã build sẵn theo width
        # cố định — chỉ Trigger con của nó mới nhận size_mult, VD bán kính
        # VortexZone của Perfect Storm.)
        root_params, trigger_params, trigger_reference, order = spell.rune_tree.resolve_cast_graph()
        # Mỗi rune giữ ĐÚNG batch riêng VÀ đúng ĐỘI HÌNH riêng của nó — tính
        # qua resolve_batch_positions() (dùng chung với Fire/Wind/Lightning,
        # xem RuneTree.dispatch_trigger_firings/_lightning_batch_beams):
        #   'line' (Stars Aligned) → gai DÀN HÀNG SONG SONG: lệch vị trí vuông
        #     góc hướng bắn, CÙNG hướng (không toả góc).
        #   'cone' (Frenetic Energy) → CÙNG gốc, hướng lệch NGẪU NHIÊN trong
        #     jitter_deg quanh hướng bắn (giống hệt Bullet thật toả cone).
        if base_attack is not None and not attacks[0].get("is_spiral"):
            positions = spell.rune_tree.resolve_batch_positions(
                self.player.x, self.player.y, base_angle, root_params.batches)
            for ox, oy, jitter_deg in positions[1:]:   # [0] la ban goc, da co san trong attacks
                if ox != self.player.x or oy != self.player.y:
                    attacks.append(self._build_ice_attack_at(ice_rune, ox, oy, base_angle, held_time))
                else:
                    angle_offset_deg = random.uniform(-jitter_deg / 2, jitter_deg / 2) if jitter_deg > 0 else 0.0
                    attacks.append(self._build_split_ice_attack(ice_rune, base_attack, angle_offset_deg, held_time))

        # Flash of Swords trên Ice: lưỡi kiếm xuất hiện & gắn ở ĐIỂM CUỐI gai
        # băng (end_x/end_y) thay vì quanh player — spike không "bay" nên mũi
        # gai là "điểm rơi" tự nhiên nhất để neo kiếm vào.
        if base_attack is not None:
            self._cap_ice_attack_at_first_enemy(base_attack)   # kiếm neo ở điểm chạm
            fos_origin = (base_attack["end_x"], base_attack["end_y"])
        else:
            fos_origin = (self.player.x, self.player.y)

        root_damage = self.player.damage * root_params.damage_mult
        self.bullets.extend(spell.rune_tree.dispatch_trigger_firings(
            self.player.x, self.player.y, dir_x, dir_y, root_damage,
            root_params.spawn_count, trigger_params, trigger_reference, order,
            context, source=None, fos_origin=fos_origin))

        bounce_max = self._hit_and_run_bounce_max(spell.rune_tree)
        trail_mods = self._find_destructive_path_modifiers(spell.rune_tree)

        for attack in attacks:
            damage = attack["damage_base"] * root_params.damage_mult

            if attack.get("is_spiral"):
                hits = ice_rune.targets_in_ice_spiral(attack, self.enemies)
                for target in hits:
                    if id(target) in damaged_targets:
                        continue
                    damaged_targets.add(id(target))
                    ice_rune.apply_charge_hit(target, damage, attack["ratio"], stack=stack)
                    self._spawn_damage_number(target.x, target.y - target.radius, damage)
                self.effects.append({
                    "kind": "ice_spiral",
                    "cx": attack["start_x"],
                    "cy": attack["start_y"],
                    "radius": attack["radius"],
                    "aim_angle": attack["aim_angle"],
                    "arc_length_rad": attack["arc_length_rad"],
                    "duration": 0.48 + attack["ratio"] * 0.8,
                })
                continue

            # Gai thẳng: Hit-And-Run bẻ thành chuỗi đoạn phản xạ tường (1 đoạn
            # nếu không có rune này) — mỗi đoạn dừng ở địch gần nhất (không
            # xuyên), dừng LUÔN chuỗi ngay khi 1 đoạn chặn trúng địch.
            for seg_attack in self._build_ice_bounce_segments(attack, bounce_max):
                self._cap_ice_attack_at_first_enemy(seg_attack)
                hits = self._targets_in_ice_hitbox(seg_attack)
                for target in hits:
                    if id(target) not in damaged_targets:
                        damaged_targets.add(id(target))
                        ice_rune.apply_charge_hit(target, damage, attack["ratio"], stack=stack)
                        self._spawn_damage_number(target.x, target.y - target.radius, damage)
                self.effects.append({
                    "kind": "ice_spike",
                    "x": seg_attack["start_x"],
                    "y": seg_attack["start_y"],
                    "x2": seg_attack["end_x"],
                    "y2": seg_attack["end_y"],
                    "width": seg_attack["width"] * 1.35,
                    "duration": 0.48 + seg_attack["length"] / 80.0 * 0.045,
                })
                for mod in trail_mods:
                    mod.leave_trail_along(seg_attack["start_x"], seg_attack["start_y"],
                                          seg_attack["end_x"], seg_attack["end_y"], context)
                if hits:
                    break   # đoạn này chặn trúng địch → không đi tiếp đoạn sau
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


    def _reflect_segment_chain(self, start_x: float, start_y: float,
                               dir_x: float, dir_y: float, length: float,
                               max_bounces: int) -> list:
        """HitAndRunModifier cho đòn tức thời (Ice/Lightning — vẽ 1 đường
        thẳng, không có Bullet để raycast từng frame): bẻ tia thành chuỗi đoạn
        phản xạ khỏi chướng ngại vật trên map. Mỗi đoạn (kể cả sau khi bẻ) có
        ĐỘ DÀI = `length` gốc — range reset, như đứng tại điểm chạm tường bắn
        phát mới. Rìa map KHÔNG tính là tường (raycast_reflect chỉ xét
        collision_rects). Trả về list (x1,y1,x2,y2), luôn có ít nhất 1 phần tử."""
        world_map = getattr(self.renderer, "world_map", None)
        dlen = math.hypot(dir_x, dir_y)
        if dlen <= 0 or world_map is None or not hasattr(world_map, "raycast_reflect"):
            return [(start_x, start_y, start_x + dir_x * length, start_y + dir_y * length)]
        ux, uy = dir_x / dlen, dir_y / dlen
        x, y = start_x, start_y
        segments = []
        bounces = 0
        while True:
            ex, ey = x + ux * length, y + uy * length
            hit = world_map.raycast_reflect(x, y, ex, ey)
            if hit is None or bounces >= max_bounces:
                segments.append((x, y, ex, ey))
                break
            hx, hy, nx, ny = hit
            segments.append((x, y, hx, hy))
            dot = ux * nx + uy * ny
            rux, ruy = ux - 2 * dot * nx, uy - 2 * dot * ny
            rlen = math.hypot(rux, ruy)
            if rlen <= 0:
                break
            ux, uy = rux / rlen, ruy / rlen
            x, y = hx, hy
            bounces += 1
        return segments

    def _build_ice_bounce_segments(self, attack: dict, bounce_max: int) -> list:
        """Trả về list các 'attack' con (cùng format dict, damage_base/width
        giữ nguyên) đại diện từng đoạn của gai băng SAU KHI bẻ theo
        Hit-And-Run — 1 phần tử (chính `attack`) nếu không có rune này/không
        bounce. Mỗi đoạn xử lý y hệt 1 gai đơn qua _cap_ice_attack_at_first_enemy
        + _targets_in_ice_hitbox (gọi bên ngoài, ở game_loop._release_ice_charge)."""
        if bounce_max <= 0:
            return [attack]
        segments = self._reflect_segment_chain(
            attack["start_x"], attack["start_y"], attack["dir_x"], attack["dir_y"],
            attack["length"], bounce_max)
        if len(segments) <= 1:
            return [attack]

        half_w = attack["width"] / 2
        result = []
        for sx, sy, ex, ey in segments:
            seg_len = math.hypot(ex - sx, ey - sy)
            if seg_len <= 0:
                continue
            dx, dy = (ex - sx) / seg_len, (ey - sy) / seg_len
            perp_x, perp_y = -dy, dx
            result.append({
                **attack,
                "start_x": sx, "start_y": sy,
                "end_x": ex, "end_y": ey,
                "dir_x": dx, "dir_y": dy,
                "length": seg_len,
                "corners": [
                    (sx + perp_x * half_w, sy + perp_y * half_w),
                    (ex + perp_x * half_w, ey + perp_y * half_w),
                    (ex - perp_x * half_w, ey - perp_y * half_w),
                    (sx - perp_x * half_w, sy - perp_y * half_w),
                ],
            })
        return result or [attack]

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

        if not self._lightning_channel_active:
            self._lightning_channel_active = True
            self._lightning_windup_elapsed = 0.0
            self._lightning_cast_fired     = False
            self._lightning_fos_anchor     = None

        # Đứng im vung tay (animation cast_lightning) NGAY từ lúc bắt đầu giữ
        # chuột — nhưng tia điện CHƯA xuất hiện cho tới khi charge đủ tới
        # khung RELEASE_FRAME (miệng hé đủ), tránh cảm giác tia ra trước khi
        # animation kịp chạy.
        self.player.cast_lock_timer = 0.10
        self.player.cast_anim = 'lightning'
        self.player.attack_timer = 0.18
        self._lightning_windup_elapsed += dt
        release_time = LIGHTNING_CAST_RELEASE_FRAME * LIGHTNING_CAST_FRAME_MS / 1000.0
        if self._lightning_windup_elapsed < release_time:
            return True

        stack = getattr(lightning, 'element_stack', 1)
        primary_hit_damage = self.player.damage + lightning.BONUS_DAMAGE * stack
        primary_damage = (primary_hit_damage / max(spell.fire_rate, 0.08)) * dt
        # chain_damage/max_targets: chỉ còn dùng cho biến thể Spiral ring
        # (_execute_lightning_spiral_ring). Tia thẳng đã bỏ chain (đơn mục tiêu).
        chain_damage = primary_damage * 0.45
        max_targets = 1 + min(4, 2 + stack)

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

        has_spiral = self._has_spiral_modifier(spell)

        # Beam tức thời không có "quãng đường bay" → rune Trigger ĐƠN GIẢN
        # (RollingStone/FuriousOutburst...) chỉ nổ đúng 1 lần khi charge XONG
        # (không phải ngay lúc bắt đầu giữ chuột nữa — khớp đúng lúc tia điện
        # thật sự xuất hiện), giữ lâu không nổ thêm. Trigger THAM GIA cast
        # graph (IS_CAST_GRAPH_TRIGGER, VD Perfect Storm) tách riêng bên dưới
        # để tôn trọng Spawn Count/Damage gắn vào nó. DestructivePath cũng chỉ
        # rải vệt lửa đúng lúc `just_fired` (dọc suốt chiều dài tia, xem
        # trail_mods bên dưới) — không có trigger_once nên không qua
        # _find_triggerable_modifiers().
        just_fired = not self._lightning_cast_fired
        if just_fired:
            self._lightning_cast_fired = True
            aim_x, aim_y = self._lightning_aim_direction(target_x, target_y)
            for trig in self._find_triggerable_modifiers(spell):
                if getattr(trig, 'IS_CAST_GRAPH_TRIGGER', False):
                    continue
                spawned = trig.trigger_once(self.player.x, self.player.y, primary_hit_damage, context,
                                            dir_x=aim_x, dir_y=aim_y)
                if spawned is not None:
                    self.bullets.append(spawned)
                    # Nhánh con (VD Flash of Swords) áp lên chính đạn phụ
                    if getattr(trig, 'OWNS_SUBTREE', False):
                        self.bullets.extend(trig._attach_subtree_and_fire(spawned, context))

            # Flash of Swords neo vào 1 _LiveAnchor thay vì toạ độ tĩnh — anchor
            # này được cập nhật lại MỖI FRAME bên dưới (nhánh tia thẳng và
            # nhánh xoắn ốc) theo điểm chạm hiện tại, để tia kiếm luôn bám
            # đúng tia điện khi người chơi đảo hướng chuột giữa chừng channel.
            fos_x, fos_y = self._lightning_fos_contact_point(aim_x, aim_y, has_spiral)
            self._lightning_fos_anchor = _LiveAnchor(fos_x, fos_y)

            self.bullets.extend(spell.rune_tree.dispatch_trigger_firings(
                self.player.x, self.player.y, aim_x, aim_y, primary_hit_damage,
                root_params.spawn_count, trigger_params, trigger_reference, order,
                context, source=self._lightning_fos_anchor, fos_origin=(fos_x, fos_y)))

        alive_before = {id(enemy) for enemy in self.enemies if enemy.alive}
        boss_alive_before = self.boss is not None and self.boss.alive

        if has_spiral:
            return self._execute_lightning_spiral_ring(
                spell, root_params, target_x, target_y, primary_damage, chain_damage,
                max_targets, alive_before, boss_alive_before, just_fired, context)

        # ── Normal lightning beam ────────────────────────────────────────────
        aim_x, aim_y = self._lightning_aim_direction(target_x, target_y)

        if aim_x < 0:
            self.player.facing_dir = -1
        elif aim_x > 0:
            self.player.facing_dir = 1

        if self._lightning_fos_anchor is not None:
            self._lightning_fos_anchor.x, self._lightning_fos_anchor.y = \
                self._lightning_fos_contact_point(aim_x, aim_y, False)

        # Mỗi rune giữ ĐÚNG batch riêng VÀ đúng ĐỘI HÌNH riêng của nó — tính
        # qua _lightning_batch_beams() (dùng chung với nhánh xoắn ốc bên dưới).
        beams = self._lightning_batch_beams(spell, root_params, aim_x, aim_y)

        bounce_max = self._hit_and_run_bounce_max(spell.rune_tree)
        trail_mods = self._find_destructive_path_modifiers(spell.rune_tree) if just_fired else []

        next_beam_id = 0
        for dir_x, dir_y, start_x, start_y in beams:
            # Hit-And-Run: bẻ tia thành chuỗi đoạn phản xạ tường (1 đoạn nếu
            # không có rune này) — mỗi đoạn dừng ở địch GẦN NHẤT (không chain,
            # không xuyên), dừng LUÔN chuỗi ngay khi 1 đoạn chặn trúng địch.
            if bounce_max > 0:
                segments = self._reflect_segment_chain(
                    start_x, start_y, dir_x, dir_y, LIGHTNING_BEAM_RANGE, bounce_max)
            else:
                segments = [(start_x, start_y,
                            start_x + dir_x * LIGHTNING_BEAM_RANGE,
                            start_y + dir_y * LIGHTNING_BEAM_RANGE)]

            for sx, sy, ex, ey in segments:
                beam_hits = self._targets_in_lightning_beam(sx, sy, ex, ey)
                if beam_hits:
                    target = beam_hits[0]
                    seg_dx, seg_dy = ex - sx, ey - sy
                    seg_len_sq = seg_dx * seg_dx + seg_dy * seg_dy
                    proj = ((target.x - sx) * seg_dx + (target.y - sy) * seg_dy) / seg_len_sq
                    proj = max(0.0, min(1.0, proj))
                    ex = sx + seg_dx * proj
                    ey = sy + seg_dy * proj
                    self._deal_damage(target, primary_damage)

                for mod in trail_mods:
                    mod.leave_trail_along(sx, sy, ex, ey, context)

                self._set_primary_lightning_beam(sx, sy, ex, ey, beam_id=next_beam_id, vortex=False)
                next_beam_id += 1
                if beam_hits:
                    break   # đoạn này chặn trúng địch → không đi tiếp đoạn sau

        self._trim_primary_lightning_beams(next_beam_id)
        self._drop_xp_from_ultimate_kills(alive_before, boss_alive_before)
        return True

    def _execute_lightning_spiral_ring(
        self,
        spell,
        root_params,
        target_x: float,
        target_y: float,
        primary_damage: float,
        chain_damage: float,
        max_targets: int,
        alive_before: set,
        boss_alive_before: bool,
        just_fired: bool = False,
        context: dict = None,
    ) -> bool:
        """Tia xoắn ốc (Twist of Fate) khi Lightning gắn rune này — mỗi 'bản'
        của cast (bản gốc + batch từ Frenetic Energy/Stars Aligned/...) là 1
        xoắn ốc LIÊN TỤC riêng, xoay ra ngoài dần tới bán kính `radius`. Dùng
        CHUNG `_lightning_batch_beams()` với nhánh tia thẳng
        (_channel_lightning_attack) — sửa/thêm rune batch mới ở đó tự động ra
        đúng số xoắn ốc ở đây luôn, không cần viết tay riêng nữa (trước đây
        hàm này không nhận root_params nên hoàn toàn bỏ qua Spawn Count của
        Frenetic/Stars Aligned — luôn chỉ ra ĐÚNG 1 xoắn ốc dù gắn thêm rune
        nào). Trước đây tách thành class `LightningSpiralAttack` riêng dưới
        `logic/abilities/`, nhưng nó chỉ gọi từ ĐÚNG 1 chỗ và thao tác thẳng
        lên state của GameLoop (không phải logic thuần) — vi phạm quy tắc
        `logic/` không được phụ thuộc `ui/`, nên đưa lại thành method ở đây."""
        radius = self._lightning_spiral_radius()

        aim_x, aim_y = self._lightning_aim_direction(target_x, target_y)
        if aim_x < 0:
            self.player.facing_dir = -1
        elif aim_x > 0:
            self.player.facing_dir = 1

        if self._lightning_fos_anchor is not None:
            self._lightning_fos_anchor.x, self._lightning_fos_anchor.y = \
                self._lightning_fos_contact_point(aim_x, aim_y, True)

        # Mỗi rune giữ ĐÚNG batch riêng VÀ đúng ĐỘI HÌNH riêng của nó — tính
        # qua _lightning_batch_beams() (dùng chung với nhánh tia thẳng phía trên).
        # origin_fn = đúng vị trí người chơi (KHÔNG lệch về phía trước như tia
        # thẳng) — xoắn ốc phải xuất phát khít tại nhân vật.
        beams = self._lightning_batch_beams(
            spell, root_params, aim_x, aim_y,
            origin_fn=lambda dx, dy: (self.player.x, self.player.y))
        self._trim_primary_lightning_beams(len(beams))

        trail_mods = self._find_destructive_path_modifiers(spell.rune_tree) if just_fired else []

        for i, (dir_x, dir_y, start_x, start_y) in enumerate(beams):
            orbit_angle = math.atan2(dir_y, dir_x)
            # Vẽ CHỈ tới đúng điểm chạm địch (giống tia thẳng dừng ở điểm
            # chạm) — không trúng ai thì vẫn vươn hết tầm radius đầy đủ.
            render_radius = self._spiral_contact_radius(start_x, start_y, radius)
            end_x = start_x + math.cos(orbit_angle) * render_radius
            end_y = start_y + math.sin(orbit_angle) * render_radius
            self._set_primary_lightning_beam(start_x, start_y, end_x, end_y, beam_id=i, vortex=True)

            ring_hits = self._targets_in_vortex(start_x, start_y, radius)
            for j, target in enumerate(ring_hits[:max_targets]):
                dmg = primary_damage if j == 0 else chain_damage
                self._deal_damage(target, dmg)

            for mod in trail_mods:
                mod.leave_trail_along(start_x, start_y, end_x, end_y, context)

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

    def _lightning_batch_beams(self, spell, root_params, aim_x: float, aim_y: float,
                               origin_fn=None) -> list:
        """Trả về list (dir_x, dir_y, start_x, start_y) cho MỌI 'bản' của cast
        này (bản gốc + batch từ Frenetic Energy/Stars Aligned/...) — DÙNG
        CHUNG cho cả tia thẳng (_channel_lightning_attack) và xoắn ốc Twist
        of Fate (_execute_lightning_spiral_ring), qua đúng 1 lần gọi
        RuneTree.resolve_batch_positions(). Sửa/thêm rune batch mới ở đây tự
        động ăn theo CẢ 2 kiểu tia, không cần viết tay riêng từng nơi nữa.
        'line' (Stars Aligned): lệch gốc vuông góc, CÙNG hướng bắn.
        'cone' (Frenetic Energy): CÙNG gốc, hướng lệch NGẪU NHIÊN trong
        jitter_deg — đúng như Bullet thật của Fire/Wind toả cone (xem
        RuneTree._spawn_copy_at).
        origin_fn(dir_x, dir_y) -> (x, y): điểm gốc cho 1 bản — mặc định
        `_lightning_cast_origin` (lệch nhẹ về phía trước, dùng cho tia thẳng).
        Xoắn ốc truyền vào hàm khác (luôn trả về vị trí NGƯỜI CHƠI) vì xoắn ốc
        phải xuất phát khít tại nhân vật, không lệch theo hướng ngắm."""
        if origin_fn is None:
            origin_fn = self._lightning_cast_origin
        base_angle = math.atan2(aim_y, aim_x)
        positions = spell.rune_tree.resolve_batch_positions(0.0, 0.0, base_angle, root_params.batches)
        beams = []
        for dx, dy, jitter_deg in positions:
            if dx != 0.0 or dy != 0.0:
                dir_x, dir_y = aim_x, aim_y
                ox, oy = origin_fn(aim_x, aim_y)
                start_x, start_y = ox + dx, oy + dy
            else:
                angle_offset = random.uniform(-jitter_deg / 2, jitter_deg / 2) if jitter_deg > 0 else 0.0
                dir_x, dir_y = self._rotated_direction(aim_x, aim_y, angle_offset)
                start_x, start_y = origin_fn(dir_x, dir_y)
            beams.append((dir_x, dir_y, start_x, start_y))
        return beams

    def _lightning_spiral_radius(self) -> float:
        """Bán kính vòng xoắn ốc (Twist of Fate) — thu nhỏ lại để bao sát
        người chơi hơn so với tầm tia thẳng đầy đủ."""
        return LIGHTNING_BEAM_RANGE * 0.55

    def _spiral_contact_radius(self, cx: float, cy: float, radius: float) -> float:
        """Bán kính THẬT SỰ để vẽ xoắn ốc — nếu có địch trong tầm, chỉ vươn ra
        tới đúng khoảng cách xa nhất trong số các mục tiêu bị trúng (giống tia
        thẳng dừng lại đúng điểm chạm, không vẽ xuyên qua/ra ngoài địch); nếu
        không trúng ai thì vẫn vươn hết `radius` đầy đủ để cho thấy hết tầm."""
        hits = self._targets_in_vortex(cx, cy, radius)
        if not hits:
            return radius
        reach = max(math.hypot(t.x - cx, t.y - cy) for t in hits)
        return max(20.0, min(radius, reach))

    def _lightning_fos_contact_point(self, aim_x: float, aim_y: float, has_spiral: bool) -> tuple[float, float]:
        """Điểm chạm hiện tại của tia (thẳng hoặc xoắn ốc) theo hướng ngắm
        MỚI NHẤT — gọi lại mỗi frame trong lúc channel để cập nhật anchor của
        Flash of Swords, cho tia kiếm bám đúng tia điện khi đổi hướng chuột."""
        if has_spiral:
            spiral_radius = self._lightning_spiral_radius()
            reach = self._spiral_contact_radius(self.player.x, self.player.y, spiral_radius)
            return (self.player.x + aim_x * reach, self.player.y + aim_y * reach)

        b_sx, b_sy = self._lightning_cast_origin(aim_x, aim_y)
        b_ex = b_sx + aim_x * LIGHTNING_BEAM_RANGE
        b_ey = b_sy + aim_y * LIGHTNING_BEAM_RANGE
        aim_hits = self._targets_in_lightning_beam(b_sx, b_sy, b_ex, b_ey)
        if aim_hits:
            t0 = aim_hits[0]
            sdx, sdy = b_ex - b_sx, b_ey - b_sy
            sl = sdx * sdx + sdy * sdy
            p = max(0.0, min(1.0, ((t0.x - b_sx) * sdx + (t0.y - b_sy) * sdy) / sl))
            return (b_sx + sdx * p, b_sy + sdy * p)
        return (b_ex, b_ey)

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

    def _update_fire_cast(self, dt: float, wx: float, wy: float) -> None:
        """Fire: giữ chuột thì đứng im vung tay (SATYR hàng 4) thay vì bắn tức
        thời. Đạn chỉ ra ở đúng khung FIRE_CAST_RELEASE_FRAME (vệt vàng rõ
        nhất), rồi vẫn đứng im hết animation mới đi tiếp được — giữa 2 lần
        bắn (lúc fire_rate cooldown chưa hết) player đi lại bình thường."""
        if not self._fire_cast_active:
            if not self.player.can_fire():
                return
            self._fire_cast_active  = True
            self._fire_cast_elapsed = 0.0
            self._fire_cast_fired   = False
            self._fire_cast_target  = (wx, wy)
            self.player.cast_anim   = 'fire'
            self.audio.play("fireball")

        self._fire_cast_elapsed += dt * 1000.0
        self.player.cast_lock_timer = max(
            0.0, (FIRE_CAST_TOTAL_MS - self._fire_cast_elapsed) / 1000.0)

        release_ms = FIRE_CAST_RELEASE_FRAME * FIRE_CAST_FRAME_MS
        if not self._fire_cast_fired and self._fire_cast_elapsed >= release_ms:
            self._spawn_bullet(*self._fire_cast_target)
            self.player.reset_fire_timer()
            self._fire_cast_fired = True

        if self._fire_cast_elapsed >= FIRE_CAST_TOTAL_MS:
            self._fire_cast_active = False
            self.player.cast_anim  = None

    def _cancel_fire_cast(self) -> None:
        if self._fire_cast_active:
            self._fire_cast_active = False
            self.player.cast_anim  = None

    def _spawn_bullet(self, target_x: float, target_y: float) -> None:
        """
        Tạo đạn mới từ vị trí người chơi bắn về hướng target_x, target_y.
        Lấy thông tin của chiêu đang dùng (`active_spell`) và `rune_tree` gắn vào đạn.
        Kích hoạt hiệu ứng `on_fire()` của cây ngọc (vd: ngọc tách đạn sẽ đẻ ra nhiều viên cùng lúc).
        
        👉 BƯỚC TIẾP THEO (Bước 11): Hãy xem cách đạn lưu trữ RuneTree lúc khởi tạo. Mở file [logic/entities/bullet.py](file:///c:/Users/acer/Downloads/OOP-mihu_branch/logic/entities/bullet.py) hàm `__init__`.
        """
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
        """
        Kiểm tra va chạm giữa đạn và quái vật.
        Nếu đạn chạm quái vật, nó sẽ gọi `enemy.take_damage(bullet.damage)`.
        Và gọi `bullet.rune_tree.on_hit(bullet, enemy, context)`.

        👉 BƯỚC TIẾP THEO (Bước 16): Khi đạn chạm quái, hàm `take_damage` của quái sẽ được gọi. Mở file [logic/entities/enemy.py](file:///c:/Users/acer/Downloads/OOP-mihu_branch/logic/entities/enemy.py) hàm `take_damage`.
        """
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
                    self._deal_damage(enemy, bullet.damage, getattr(bullet, 'is_crit', False))
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
                        self._deal_damage(self.boss, bullet.damage, getattr(bullet, 'is_crit', False))
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
        # Không vẽ thêm hiệu ứng nổ chồng lên quái nữa — quái đã tự phản ứng
        # bằng frame "hit" có sẵn trong sprite sheet riêng của nó (renderer.py
        # draw_enemy/draw_boss chọn anim_name='hit' theo hurt_timer).
        vt = getattr(bullet, 'visual_type', '')
        if vt == 'blood_ball':
            self.active_effects.append(ImpactEffect(bullet.x, bullet.y, 'blood_impact'))

    def _spawn_damage_number(self, x: float, y: float, amount: float,
                             is_crit: bool = False) -> None:
        """Số dmg bay lên tại (x, y) rồi mờ dần — gọi ngay sau mỗi lần
        take_damage() thật (không hiện nếu dmg <= 0, VD đòn bị né/miss)."""
        if amount <= 0:
            return
        import random as _rnd
        self.damage_numbers.append({
            'x': x + _rnd.uniform(-6.0, 6.0),
            'y': y,
            'vy': -46.0,
            'text': str(int(round(amount))),
            'is_crit': is_crit,
            'age': 0.0,
            'duration': 0.7,
        })

    def _deal_damage(self, target, amount: float, is_crit: bool = False) -> None:
        """Gây damage lên quái/boss VÀ sinh số dmg bay lên cùng lúc — dùng ở
        mọi chỗ đánh trúng quái (bullet/AoE/beam) để không sót chỗ nào."""
        target.take_damage(amount)
        if amount <= 0:
            return
        self._spawn_damage_number(target.x, target.y - target.radius, amount, is_crit)

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
                self._deal_damage(entity, effect.damage, getattr(effect, 'is_crit', False))
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

    def _resolve_player_map_collision(self, old_x: float, old_y: float) -> None:
        if getattr(self, "noclip_mode", False):
            return
        self._resolve_entity_map_collision(self.player, old_x, old_y, reset_velocity=True)

    def _is_map_blocked(self, x: float, y: float, radius: float) -> bool:
        return self._map_collides_circle(x, y, radius)

    def _update_bullet_wall_bounce(self, bullet, old_x: float, old_y: float) -> None:
        """Hit-And-Run: đạn/boomerang phản xạ khỏi chướng ngại vật trên map
        khi đang bay (Fire/Wind) — raycast đúng đoạn di chuyển vừa xong; nếu
        cắt tường thì phản xạ vận tốc (góc tới = góc phản xạ) + reset lifetime
        (range đầy lại, như bắn phát mới từ điểm chạm tường). Rìa map KHÔNG
        tính là tường (raycast_reflect chỉ xét collision_rects)."""
        if not bullet.alive:
            return
        rune_tree = getattr(bullet, 'rune_tree', None)
        if rune_tree is None:
            return
        bounce_max = self._hit_and_run_bounce_max(rune_tree)
        if bounce_max <= 0 or bullet.bounce_count >= bounce_max:
            return
        # WindBoomerang: chỉ bounce ở pha bay ra, không đụng lúc pause/return.
        if getattr(bullet, 'phase', 'out') != 'out':
            return
        world_map = getattr(self.renderer, "world_map", None)
        if world_map is None or not hasattr(world_map, "raycast_reflect"):
            return
        hit = world_map.raycast_reflect(old_x, old_y, bullet.x, bullet.y)
        if hit is None:
            return
        hx, hy, nx, ny = hit
        dot = bullet.vx * nx + bullet.vy * ny
        new_vx = bullet.vx - 2 * dot * nx
        new_vy = bullet.vy - 2 * dot * ny
        bullet.x, bullet.y = hx, hy
        bullet.redirect(new_vx, new_vy)   # Bullet/WindBoomerang tự reset range của mình
        bullet.bounce_count += 1

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

    # ── Creative / Test mode ──────────────────────────────────────────────────

    def _creative_combos(self) -> list:
        """Các tổ hợp rune tiêu biểu — chọn những cái dễ lộ bug nhất: cast-graph
        lồng nhau, phản xạ tường, orbit, stack trùng loại. Mỗi tổ hợp ≤ 5
        modifier (vừa 5 slot nhánh)."""
        from logic.rune.modifiers.flash_of_swords_trigger import FlashOfSwordsTrigger
        from logic.rune.modifiers.self_centered_modifier import SelfCenteredModifier
        from logic.rune.modifiers.twist_of_fate_modifier import TwistOfFateModifier
        from logic.rune.modifiers.frenetic_energy_modifier import FreneticEnergyModifier
        from logic.rune.modifiers.stars_aligned_modifier import StarsAlignedModifier
        from logic.rune.modifiers.perfect_storm_modifier import PerfectStormModifier
        from logic.rune.modifiers.heavy_hitter_modifier import HeavyHitterModifier
        from logic.rune.modifiers.hit_and_run_modifier import HitAndRunModifier
        from logic.rune.modifiers.piercing_eyes_modifier import PiercingEyesModifier
        from logic.rune.modifiers.furious_outburst_modifier import FuriousOutburstModifier
        from logic.rune.modifiers.destructive_path_modifier import DestructivePathModifier
        from logic.rune.modifiers.lightened_heart_modifier import LightenedHeartModifier
        from logic.rune.modifiers.rolling_stone_modifier import RollingStoneModifier
        from logic.rune.modifiers.haste_rune import HasteRune
        return [
            ("Nested Chaos (cast-graph lồng)",
             [FlashOfSwordsTrigger, SelfCenteredModifier, TwistOfFateModifier,
              FreneticEnergyModifier, StarsAlignedModifier]),
            ("Vortex Storm (nhiều lốc + batch)",
             [PerfectStormModifier, FreneticEnergyModifier, StarsAlignedModifier,
              HeavyHitterModifier]),
            ("Bounce + Pierce (phản xạ tường)",
             [HitAndRunModifier, PiercingEyesModifier, HeavyHitterModifier,
              TwistOfFateModifier]),
            ("Outburst Rain (trigger theo quãng đường)",
             [FuriousOutburstModifier, DestructivePathModifier, HeavyHitterModifier,
              LightenedHeartModifier]),
            ("Rolling Barrage (nhiều đá + bắn nhanh)",
             [RollingStoneModifier, FreneticEnergyModifier, HasteRune,
              PiercingEyesModifier]),
            ("Double Stack (trùng loại x2)",
             [TwistOfFateModifier, TwistOfFateModifier, SelfCenteredModifier,
              SelfCenteredModifier]),
            ("Kitchen Sink (nhiều trigger cùng lúc)",
             [FlashOfSwordsTrigger, PerfectStormModifier, FuriousOutburstModifier,
              HitAndRunModifier, HeavyHitterModifier]),
        ]

    def _creative_apply_combo(self, classes: list) -> None:
        """Nạp danh sách modifier vào slot nhánh của CẢ 2 chiêu (bỏ qua giới
        hạn điểm — đây là test mode). Đặt thẳng slot.rune rồi rebuild cây."""
        for spell in self.player.spells:
            mod_slots = [s for s in spell.rune_slots.slots if s.slot_type == 'modifier']
            for s in mod_slots:
                if not s.locked:
                    s.rune = None
            for s, cls in zip(mod_slots, classes):
                s.rune = cls()
            spell.rebuild_rune_tree()

    def _creative_spawn(self, kind: str) -> None:
        wx, wy = self.input.get_mouse_world_pos(
            self._camera_x(), self._camera_y(), self.renderer.zoom)
        if kind == 'boss':
            self.boss = Boss(wx, wy)
            return
        cls = {'enemy': Enemy, 'ranged': RangedEnemy, 'fast': FastEnemy,
               'tank': TankEnemy, 'dummy': DummyEnemy}[kind]
        self.enemies.append(cls(wx, wy))

    def _creative_spawn_horde(self, count: int = 12) -> None:
        types = [Enemy, RangedEnemy, FastEnemy, TankEnemy]
        for i in range(count):
            ang = (i / count) * math.tau
            r   = random.uniform(180.0, 340.0)
            x   = self.player.x + math.cos(ang) * r
            y   = self.player.y + math.sin(ang) * r
            self.enemies.append(random.choice(types)(x, y))

    def _creative_clear(self) -> None:
        self.enemies       = []
        self.boss          = None
        self.bullets       = []
        self.enemy_bullets = []
        self.active_effects = []
        self.effects       = []

    def _handle_creative_key(self, key) -> bool:
        """Xử lý phím tắt creative. Trả về True nếu đã tiêu thụ phím (để Q/E,
        Space... vẫn hoạt động bình thường thì trả False cho các phím đó)."""
        # Đang mở bảng chọn tổ hợp → phím số chọn tổ hợp thay vì spawn
        if self._combo_picker_open:
            return self._handle_combo_picker_key(key)

        spawn_map = {
            pygame.K_1: 'enemy', pygame.K_2: 'ranged',
            pygame.K_3: 'fast',  pygame.K_4: 'tank', pygame.K_5: 'boss',
            pygame.K_7: 'dummy',
        }
        if key in spawn_map:
            self._creative_spawn(spawn_map[key])
            return True
        if key == pygame.K_6:
            self._creative_spawn_horde()
            return True
        if key in (pygame.K_0, pygame.K_k):
            self._creative_clear()
            return True
        if key == pygame.K_c:
            self._combo_picker_open = True   # mở bảng chọn tổ hợp rune
            return True
        if key == pygame.K_v:
            self.player.god_mode = not self.player.god_mode
            return True
        if key == pygame.K_b:
            self.wave_auto = not self.wave_auto
            return True
        if key == pygame.K_F1:
            self.show_creative_help = not self.show_creative_help
            return True
        return False

    def _handle_combo_picker_key(self, key) -> bool:
        """Phím tắt khi bảng chọn tổ hợp đang mở."""
        if key in (pygame.K_c, pygame.K_ESCAPE):
            self._combo_picker_open = False
            return True
        if key == pygame.K_0:
            self._creative_apply_combo([])   # xoá hết rune
            self._combo_index = -1
            return True
        combos = self._creative_combos()
        if pygame.K_1 <= key <= pygame.K_9:
            idx = key - pygame.K_1
            if idx < len(combos):
                self._combo_index = idx
                self._creative_apply_combo(combos[idx][1])
            return True
        return True   # nuốt mọi phím khác khi bảng mở

    def _combo_picker_click(self, pos) -> None:
        """Click 1 dòng trong bảng chọn tổ hợp (hoặc ngoài bảng để đóng)."""
        for rect, idx in self._combo_picker_rects:
            if rect.collidepoint(pos):
                if idx == -1:
                    self._creative_apply_combo([])
                    self._combo_index = -1
                else:
                    self._combo_index = idx
                    self._creative_apply_combo(self._creative_combos()[idx][1])
                return
        # Click ra ngoài panel → đóng
        self._combo_picker_open = False

    def _draw_creative_overlay(self) -> None:
        """Bảng hướng dẫn + trạng thái creative, vẽ trên cửa sổ thật (self.screen).
        Đặt ở dải trống giữa HUD (trái) và minimap (phải) để không đè lên nhau."""
        font = self.font_small
        ox = 336   # bắt đầu sau cột HUD bên trái
        if not self.show_creative_help:
            hint = font.render("F1: hiện bảng Creative", True, (150, 210, 255))
            self.screen.blit(hint, (ox, 14))
            return

        combos = self._creative_combos()
        combo_name = combos[self._combo_index][0] if self._combo_index >= 0 else "(chưa nạp — nhấn C)"
        god = "BẬT" if getattr(self.player, 'god_mode', False) else "tắt"
        waves = "BẬT" if self.wave_auto else "tắt"
        n_enemy = sum(1 for e in self.enemies if e.alive)

        lines = [
            ("CREATIVE / TEST MODE", (255, 220, 120)),
            ("Spawn tại con trỏ:  1 Enemy  2 Ranged  3 Fast  4 Tank  5 Boss  7 Dummy", (215, 225, 240)),
            ("6 Cụm quái quanh nhân vật     0 / K  Xoá sạch quái + đạn", (215, 225, 240)),
            ("C  Bảng chọn tổ hợp rune     Q / E  đổi chiêu", (215, 225, 240)),
            (f"V  God mode [{god}]    B  Wave tự động [{waves}]    F1  Ẩn bảng", (215, 225, 240)),
            (f"Tổ hợp rune: {combo_name}", (150, 230, 170)),
            (f"Số quái: {n_enemy}", (170, 190, 210)),
        ]
        pad = 12
        line_h = 24
        w = 660
        h = pad * 2 + line_h * len(lines)
        panel = pygame.Surface((w, h), pygame.SRCALPHA)
        panel.fill((12, 16, 26, 225))
        pygame.draw.rect(panel, (90, 130, 180), panel.get_rect(), 2)
        self.screen.blit(panel, (ox, 10))
        for i, (text, col) in enumerate(lines):
            surf = font.render(text, True, col)
            self.screen.blit(surf, (ox + pad, 10 + pad + i * line_h))

        if self._combo_picker_open:
            self._draw_combo_picker()

    def _draw_combo_picker(self) -> None:
        """Bảng danh sách tổ hợp rune — click hoặc bấm số để nạp vào cả 2 chiêu."""
        font = self.font_small
        combos = self._creative_combos()
        rows = [(-1, "Xoá hết rune (chỉ còn nguyên tố)")]
        rows += [(i, name) for i, (name, _cls) in enumerate(combos)]

        row_h = 34
        w = 560
        pad = 16
        title_h = 40
        h = title_h + pad + row_h * len(rows) + pad
        px = WINDOW_W // 2 - w // 2
        py = WINDOW_H // 2 - h // 2

        # Nền mờ toàn màn để nổi bật bảng
        dim = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 120))
        self.screen.blit(dim, (0, 0))

        panel = pygame.Surface((w, h), pygame.SRCALPHA)
        panel.fill((16, 20, 32, 245))
        pygame.draw.rect(panel, (120, 160, 210), panel.get_rect(), 2, border_radius=8)
        self.screen.blit(panel, (px, py))

        title = font.render("CHỌN TỔ HỢP RUNE", True, (255, 220, 120))
        self.screen.blit(title, (px + pad, py + 12))
        hint = font.render("Click hoặc bấm số  ·  C / ESC đóng", True, (150, 165, 185))
        self.screen.blit(hint, hint.get_rect(topright=(px + w - pad, py + 14)))

        self._combo_picker_rects = []
        mx, my = pygame.mouse.get_pos()
        y = py + title_h + pad
        for idx, name in rows:
            rect = pygame.Rect(px + pad, y, w - pad * 2, row_h - 6)
            self._combo_picker_rects.append((rect, idx))
            active = (idx == self._combo_index)
            hover = rect.collidepoint(mx, my)
            if active:
                bg = (46, 66, 52)
            elif hover:
                bg = (40, 50, 68)
            else:
                bg = (24, 30, 44)
            pygame.draw.rect(self.screen, bg, rect, border_radius=6)
            brd = (110, 220, 150) if active else (70, 84, 104)
            pygame.draw.rect(self.screen, brd, rect, 2, border_radius=6)

            keycap = "0" if idx == -1 else str(idx + 1)
            k_surf = font.render(keycap, True, (255, 220, 120) if not active else (150, 240, 170))
            self.screen.blit(k_surf, k_surf.get_rect(midleft=(rect.left + 12, rect.centery)))
            n_col = (235, 245, 255) if (active or hover) else (185, 195, 212)
            n_surf = font.render(name, True, n_col)
            self.screen.blit(n_surf, n_surf.get_rect(midleft=(rect.left + 44, rect.centery)))
            y += row_h

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
        self.damage_numbers = [
            d for d in self.damage_numbers if d['age'] < d['duration']
        ]

    def _update_footsteps(self, dt: float, old_x: float, old_y: float) -> None:
        """Phát tiếng bước chân theo nhịp khi player thực sự dịch chuyển.

        Dùng khoảng cách đã đi (sau va chạm) để không kêu khi đi vào tường.
        """
        moved = math.hypot(self.player.x - old_x, self.player.y - old_y)
        if moved < 0.5:
            self._footstep_timer = self.FOOTSTEP_INTERVAL   # đứng yên → bước kế tiếp kêu ngay
            return
        self._footstep_timer -= dt
        if self._footstep_timer <= 0.0:
            self.audio.play("footstep")
            self._footstep_timer = self.FOOTSTEP_INTERVAL

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
                damage_numbers=self.damage_numbers,
                dt=self._dt)
            self._present_game_surface()
            self.hud.draw(self.player, self.wave_mgr.get_wave_info())
            
            if self.wave_notif_timer > 0:
                alpha = min(255, max(0, int((self.wave_notif_timer / 3.0) * 255 * 2)))
                notif_surf = self.font_big.render(self.wave_notif_text, True, (255, 255, 0))
                notif_surf.set_alpha(alpha)
                self.screen.blit(notif_surf, (WINDOW_W//2 - notif_surf.get_width()//2, WINDOW_H//4))

            if self.creative_mode:
                self._draw_creative_overlay()

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
