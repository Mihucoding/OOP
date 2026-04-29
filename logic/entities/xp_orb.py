import math


class XPOrb:
    RADIUS = 8
    COLLECT_RADIUS = 40  # player nhặt tự động khi trong bán kính này

    def __init__(self, x: float, y: float, value: int):
        self.x = x
        self.y = y
        self.radius = XPOrb.RADIUS
        self.value = value     # lượng XP cho player
        self.alive = True

    def check_collect(self, player_x: float, player_y: float) -> bool:
        # Trả về True nếu player đủ gần (dùng khoảng cách Euclidean)
        # Nếu True → set self.alive = False
        pass
