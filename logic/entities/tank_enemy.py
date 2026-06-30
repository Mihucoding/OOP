from logic.entities.enemy import Enemy

class TankEnemy(Enemy):
    """
    Quái Đỡ Đòn: máu siêu trâu, tốc độ cực chậm, hình thể to.
    Màu UI: BROWN.
    """
    RADIUS = 35
    BASE_HP = 200
    BASE_SPEED = 40
    XP_VALUE = 30
    COLOR = (139, 69, 19) # Brown
