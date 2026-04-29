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
