# Assets - Sounds

Thêm các file âm thanh vào đây, ví dụ:
- shoot.wav
- enemy_hit.wav
- boss_spawn.wav
- background_music.mp3

Dùng trong pygame:
```python
import pygame.mixer

pygame.mixer.init()
sound = pygame.mixer.Sound('assets/sounds/shoot.wav')
sound.play()
```
