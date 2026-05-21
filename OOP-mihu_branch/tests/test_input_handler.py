import unittest
from unittest.mock import patch
import pygame
from ui.input_handler import InputHandler

class TestInputHandler(unittest.TestCase):
    @patch('pygame.key.get_pressed')
    def test_get_move_direction(self, mock_get_pressed):
        # Giả lập mảng trả về từ get_pressed
        mock_keys = [0] * 512
        mock_keys[pygame.K_w] = 1
        mock_keys[pygame.K_d] = 1
        mock_get_pressed.return_value = mock_keys
        
        handler = InputHandler()
        mx, my = handler.get_move_direction()
        self.assertEqual(mx, 1)  # D=1, A=0 -> 1
        self.assertEqual(my, -1) # S=0, W=1 -> -1

    @patch('pygame.mouse.get_pos')
    def test_get_mouse_world_pos(self, mock_get_pos):
        mock_get_pos.return_value = (800, 600)
        handler = InputHandler()
        # SCREEN_W = 1280, SCREEN_H = 720
        # world_x = 800 + 1000 - 640 = 1160
        # world_y = 600 + 1000 - 360 = 1240
        wx, wy = handler.get_mouse_world_pos(1000.0, 1000.0)
        self.assertEqual(wx, 1160)
        self.assertEqual(wy, 1240)

if __name__ == '__main__':
    unittest.main()
