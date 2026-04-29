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
