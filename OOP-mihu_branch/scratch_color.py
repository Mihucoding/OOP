import pygame
import os

pygame.init()
path = r"c:\Users\acer\Downloads\OOP-mihu_branch\OOP-mihu_branch\assets\map\grass_tileset_16x16.png"
if os.path.exists(path):
    img = pygame.image.load(path)
    found = False
    for row in range(img.get_height() // 16):
        for col in range(img.get_width() // 16):
            tile = img.subsurface((col * 16, row * 16, 16, 16))
            color = tile.get_at((0, 0))[:3]
            if color == (168, 186, 68):
                print(f"Found at col={col}, row={row}")
                found = True
    if not found:
        print("Not found by (0,0) pixel, checking full tile...")
        for row in range(img.get_height() // 16):
            for col in range(img.get_width() // 16):
                tile = img.subsurface((col * 16, row * 16, 16, 16))
                for x in range(16):
                    for y in range(16):
                        if tile.get_at((x, y))[:3] == (168, 186, 68):
                            print(f"Found in col={col}, row={row}")
                            break
                    else:
                        continue
                    break
