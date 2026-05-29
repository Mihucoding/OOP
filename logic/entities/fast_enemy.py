from logic.entities.enemy import Enemy

class FastEnemy(Enemy):
    """
    Quái Nhanh: máu ít, di chuyển cực nhanh.
    Màu UI: YELLOW (vẽ bởi Renderer).
    """
    RADIUS = 15
    BASE_HP = 30
    BASE_SPEED = 150
    XP_VALUE = 15
    COLOR = (255, 255, 0) # YELLOW
