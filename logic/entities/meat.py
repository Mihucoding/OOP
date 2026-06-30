from logic.entities.xp_orb import XPOrb

class Meat(XPOrb):
    """
    Vật phẩm thịt rơi ra từ cừu.
    Kế thừa từ XPOrb để tận dụng logic bay hút về phía player và nhặt,
    nhưng có value = 0 để không cộng XP cho người chơi.
    """
    def __init__(self, x: float, y: float, vx: float = 0.0, vy: float = 0.0):
        super().__init__(x, y, value=0, vx=vx, vy=vy)
