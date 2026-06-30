# Assets - Sprites

Thêm các file ảnh vào đây, ví dụ:
- player.png
- enemy.png
- boss.png
- bullet.png
- xp_orb.png
- effects/ (subfolder cho hiệu ứng)
  - fire.png
  - ice.png
  - poison.png

Dùng trong pygame (Renderer class):
```python
import pygame

image = pygame.image.load('assets/sprites/player.png')
image = pygame.transform.scale(image, (30, 30))
screen.blit(image, (x, y))
```

Hoặc dùng trong Renderer.load_sprite():
```python
renderer.load_sprite('player', 'assets/sprites/player.png', (30, 30))
```

**Lưu ý:** Hiện tại code dùng colored shapes (pygame.draw.circle, etc).
Nếu muốn dùng sprite thì uncomment/implement load_sprite() trong Renderer.
