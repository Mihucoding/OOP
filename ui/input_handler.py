import pygame

from ui.renderer import SCREEN_W, SCREEN_H, PIXEL_SCALE

class InputHandler:
    """Đọc input từ keyboard + mouse, trả về game commands."""

    def get_move_direction(self) -> tuple:
        """
        Đọc sự kiện từ bàn phím để biết người chơi đang bấm phím nào (W, A, S, D).
        Tính toán vector hướng di chuyển (move_x, move_y).
        Ví dụ: Bấm D -> (1, 0). Bấm W và A -> (-1, -1).
        Vector này sẽ được truyền lại cho hàm _update ở GameLoop.

        👉 BƯỚC TIẾP THEO (Bước 7): Quay trở lại file [ui/game_loop.py](file:///c:/Users/acer/Downloads/OOP-mihu_branch/ui/game_loop.py) hàm `_update` để xem nó lấy (move_x, move_y) này truyền cho Player thế nào.
        """
        keys = pygame.key.get_pressed()
        move_x = keys[pygame.K_d] - keys[pygame.K_a]
        move_y = keys[pygame.K_s] - keys[pygame.K_w]
        return move_x, move_y

    def get_mouse_world_pos(self, camera_x: float, camera_y: float, zoom: float = 1.0) -> tuple:
        # pygame.mouse.get_pos() → (screen_x, screen_y)
        # Chuyển sang world coords: world_x = screen_x + camera_x - SCREEN_W/2
        # Trả về (world_x, world_y)
        mouse_x, mouse_y = pygame.mouse.get_pos()
        mouse_x /= PIXEL_SCALE
        mouse_y /= PIXEL_SCALE
        world_x = (mouse_x - SCREEN_W / 2) / zoom + camera_x
        world_y = (mouse_y - SCREEN_H / 2) / zoom + camera_y
        return world_x, world_y

    def is_firing(self) -> bool:
        # Trả về True nếu pygame.mouse.get_pressed()[0] (chuột trái)
        keys = pygame.mouse.get_pressed()
        return keys[0]

    def process_events(self) -> str | None:
        # Duyệt pygame.event.get()
        # QUIT → trả về 'quit'
        # ESC → trả về 'pause'
        # Ngược lại → None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "pause"
        return None
