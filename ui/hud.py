import pygame

SCREEN_W, SCREEN_H = 1280, 720


class HUD:
    """Vẽ giao diện: HP bar, XP bar, level, wave, rune tree hiện tại."""

    def __init__(self, screen: pygame.Surface, font: pygame.font.Font):
        self.screen = screen
        self.font = font

    def draw(self, player, wave_info: str) -> None:
        # HP bar: góc trái trên (10, 10), rộng 200, cao 20, màu đỏ
        # XP bar: bên dưới HP bar, màu xanh lá
        # Level: text "Lv.X" bên cạnh XP bar
        # Wave: text góc phải trên
        # Rune list: liệt kê các Rune trong player.rune_tree (màu của từng rune)
        pass
