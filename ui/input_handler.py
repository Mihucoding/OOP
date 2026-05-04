import pygame

SCREEN_W, SCREEN_H = 1280, 720

class InputHandler:
    """Đọc input từ keyboard + mouse, trả về game commands."""

    def get_move_direction(self) -> tuple:
        # Đọc pygame.key.get_pressed()
        # W→(0,-1), S→(0,1), A→(-1,0), D→(1,0), kết hợp chéo
        # Trả về (move_x, move_y) chưa normalize
        keys = pygame.key.get_pressed()
        move_x = keys[pygame.K_d] - keys[pygame.K_a]
        move_y = keys[pygame.K_s] - keys[pygame.K_w]
        return move_x, move_y

    def get_mouse_world_pos(self, camera_x: float, camera_y: float) -> tuple:
        # pygame.mouse.get_pos() → (screen_x, screen_y)
        # Chuyển sang world coords: world_x = screen_x + camera_x - SCREEN_W/2
        # Trả về (world_x, world_y)
        mouse_x, mouse_y = pygame.mouse.get_pos()
        world_x = mouse_x + camera_x - SCREEN_W / 2
        world_y = mouse_y + camera_y - SCREEN_H / 2
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
