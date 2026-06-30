import math
from logic.rune.elements.ice_rune import IceRune


class IceSpiralAttack:
    """
    Logic tấn công của Ice Rune khi có SpiralModifier.
    Thay vì đâm thẳng, gai băng sẽ trồi lên thành một vòng cung bao quanh người chơi.
    Thời gian charge càng lâu, vòng cung càng khép kín (max 360 độ).
    """

    def build_charge_attack(
        self,
        ice_rune: IceRune,
        caster_x: float,
        caster_y: float,
        target_x: float,
        target_y: float,
        held_time: float,
    ) -> dict:
        charge_ratio = ice_rune.charge_ratio(held_time)

        dx = target_x - caster_x
        dy = target_y - caster_y
        dist = math.hypot(dx, dy)
        if dist <= 0:
            dx, dy = 1.0, 0.0
        else:
            dx, dy = dx / dist, dy / dist

        aim_angle = math.atan2(dy, dx)

        # Bán kính cố định của vòng băng
        radius = 160.0

        # Cung tròn (Arc) mở rộng dựa trên charge_ratio
        # Gồng tối đa (charge_ratio = 1.0) sẽ tạo vòng tròn khép kín 360 độ (math.tau)
        # Gồng ít nhất sẽ tạo vòng cung nhỏ (~60 độ)
        min_arc = 1.0
        max_arc = math.tau
        arc_length_rad = min_arc + (max_arc - min_arc) * charge_ratio

        return {
            "is_spiral": True,
            "ratio": charge_ratio,
            "charge_ratio": charge_ratio,
            "radius": radius,
            "aim_angle": aim_angle,
            "arc_length_rad": arc_length_rad,
            "dir_x": dx,
            "dir_y": dy,
            "start_x": caster_x,  # Tâm vòng tròn
            "start_y": caster_y,
            "damage_mult": ice_rune.MIN_DAMAGE_MULT
            + (ice_rune.MAX_DAMAGE_MULT - ice_rune.MIN_DAMAGE_MULT) * charge_ratio,
        }

    def targets_in_ice_spiral(self, attack: dict, enemies: list) -> list:
        """Kiểm tra quái nằm trong cung tròn của băng"""
        hits = []
        cx = attack["start_x"]
        cy = attack["start_y"]
        radius = attack["radius"]
        aim_angle = attack["aim_angle"]
        arc_length = attack["arc_length_rad"]

        # Vòng cung mọc đều ra 2 bên từ aim_angle
        # Độ dày của tường băng (hitbox width)
        thickness = 78.0  # ice_rune.HITBOX_WIDTH

        for enemy in enemies:
            if not enemy.alive:
                continue

            dx = enemy.x - cx
            dy = enemy.y - cy
            dist = math.hypot(dx, dy)

            # Kiểm tra khoảng cách có nằm trong độ dày tường băng không
            if abs(dist - radius) <= thickness / 2 + enemy.radius:
                # Kiểm tra góc
                angle = math.atan2(dy, dx)

                # Chuẩn hóa góc về [-pi, pi] so với aim_angle
                diff = (angle - aim_angle + math.pi) % math.tau - math.pi

                if abs(diff) <= arc_length / 2 + (enemy.radius / max(1.0, radius)):
                    hits.append(enemy)

        return hits
