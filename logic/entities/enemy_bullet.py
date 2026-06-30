import math


class EnemyBullet:
    """Đạn do RangedEnemy bắn về phía player."""
    SPEED    = 220
    RADIUS   = 5
    DAMAGE   = 12.0
    LIFETIME = 4.0

    def __init__(self, x: float, y: float, target_x: float, target_y: float):
        self.x       = float(x)
        self.y       = float(y)
        self.radius  = EnemyBullet.RADIUS
        self.damage  = EnemyBullet.DAMAGE
        self.alive   = True
        self.elapsed = 0.0

        dx   = target_x - x
        dy   = target_y - y
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.vx = (dx / dist) * EnemyBullet.SPEED
            self.vy = (dy / dist) * EnemyBullet.SPEED
        else:
            self.vx = 0.0
            self.vy = -EnemyBullet.SPEED

    def update(self, dt: float) -> None:
        self.x       += self.vx * dt
        self.y       += self.vy * dt
        self.elapsed += dt
        if self.elapsed >= EnemyBullet.LIFETIME:
            self.alive = False
