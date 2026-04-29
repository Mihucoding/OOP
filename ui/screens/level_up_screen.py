import pygame

SCREEN_W, SCREEN_H = 1280, 720


class LevelUpScreen:
    """
    Màn hình lên cấp: hiển thị 3 Rune lựa chọn.
    Dừng game loop cho đến khi player chọn.
    """

    CARD_W, CARD_H = 200, 280
    CARD_GAP = 40

    def __init__(self, screen: pygame.Surface, font_big, font_small):
        self.screen = screen
        self.font_big = font_big
        self.font_small = font_small

    def draw(self, choices: list) -> None:
        # Vẽ overlay tối nền
        # Vẽ 3 card cạnh nhau ở giữa màn hình
        # Mỗi card: màu rune + tên + mô tả
        # Vẽ số 1/2/3 gợi ý phím bấm
        pass

    def handle_event(self, event: pygame.event.Event) -> int | None:
        # Phím 1 → trả về 0
        # Phím 2 → trả về 1
        # Phím 3 → trả về 2
        # Click vào card → trả về index tương ứng
        pass
