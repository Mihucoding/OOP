import math

from logic.rune.rune_component import ElementRune
from logic.entities.status_effect import StatusEffect


class IceRune(ElementRune):
    """Ice element. Basic bullets chill; active slot casts a hold-charge spike."""

    # Hit-And-Run: gai băng phản xạ (bẻ góc) khi chạm chướng ngại vật trên map,
    # đi tiếp theo hướng phản xạ với range reset về full — xem
    # game_loop._reflect_segment_chain / _cap_ice_attack_at_first_enemy.
    # SelfCentered giờ là cast-graph modifier: gắn thẳng spike thì vô hại, nhưng
    # gắn dưới 1 Trigger (VD Flash of Swords) thì tia kiếm vẫn quay được → cho phép.
    # TwistOfFate: KHÔNG xoay vận tốc/lớn dần ở đây (spike đứng yên) — thay vào
    # đó là công tắc chuyển gai thẳng sang đòn xoáy vòng (build_spiral_charge_attack).

    SLOW_FACTOR = 0.6
    SLOW_DURATION = 3.0

    CHARGE_MAX_TIME = 0.4   # giây gồng để đạt full charge — khớp thẻ "Duration: 0.0s <-> 0.4s"
    MIN_LENGTH = 130.0
    MAX_LENGTH = 360.0
    HITBOX_WIDTH = 78.0
    START_OFFSET = 44.0
    # Sát thương TUYỆT ĐỐI (không ăn theo player.damage) — mức chưa buff rune
    # gì, charge càng lâu càng gần 250 (khớp thẻ "Damage: 0 <-> 250"). Buff từ
    # rune modifier (HeavyHitter, Frenetic...) vẫn nhân thêm bên ngoài như cũ.
    MIN_DAMAGE = 0.0
    MAX_DAMAGE = 250.0
    # "Apply 25 Chill" trên thẻ: mỗi lần trúng cộng 25 điểm chill, đủ
    # CHILL_FREEZE_THRESHOLD (100) là đóng băng hoàn toàn (slow_factor = 0) —
    # xem StatusEffect (stacks/max_stacks) + Enemy.add_status.
    CHILL_PER_HIT          = 25
    CHILL_FREEZE_THRESHOLD = 100
    SPEED = 40   # chỉ số hiển thị trên thẻ (tốc độ "load" hiệu ứng băng) — chưa gắn cơ chế thật

    def on_hit(self, bullet, enemy, context: dict) -> None:
        chill = StatusEffect(
            effect_type="chill",
            damage_per_sec=0.0,
            duration=self.SLOW_DURATION,
            stacks=self.CHILL_PER_HIT * bullet.element_stack,
            max_stacks=self.CHILL_FREEZE_THRESHOLD,
        )
        enemy.add_status(chill)

    def charge_ratio(self, held_time: float) -> float:
        return max(0.0, min(1.0, held_time / self.CHARGE_MAX_TIME))

    def build_charge_attack(
        self,
        caster_x: float,
        caster_y: float,
        target_x: float,
        target_y: float,
        held_time: float,
        max_length: float | None = None,
    ) -> dict:
        charge_ratio = self.charge_ratio(held_time)
        dx = target_x - caster_x
        dy = target_y - caster_y
        dist = math.hypot(dx, dy)
        if dist <= 0:
            dx, dy = 1.0, 0.0
        else:
            dx, dy = dx / dist, dy / dist

        length = self.MIN_LENGTH + (self.MAX_LENGTH - self.MIN_LENGTH) * charge_ratio
        if max_length is not None:
            length = min(length, max(32.0, max_length))
        length_ratio = max(
            0.0,
            min(1.0, (length - self.MIN_LENGTH) / max(1.0, self.MAX_LENGTH - self.MIN_LENGTH)),
        )
        width = self.HITBOX_WIDTH
        start_x = caster_x + dx * self.START_OFFSET
        start_y = caster_y + dy * self.START_OFFSET
        end_x = start_x + dx * length
        end_y = start_y + dy * length
        perp_x, perp_y = -dy, dx
        half_w = width / 2

        return {
            "ratio": length_ratio,
            "charge_ratio": charge_ratio,
            "length": length,
            "width": width,
            "dir_x": dx,
            "dir_y": dy,
            "start_x": start_x,
            "start_y": start_y,
            "end_x": end_x,
            "end_y": end_y,
            "corners": [
                (start_x + perp_x * half_w, start_y + perp_y * half_w),
                (end_x + perp_x * half_w, end_y + perp_y * half_w),
                (end_x - perp_x * half_w, end_y - perp_y * half_w),
                (start_x - perp_x * half_w, start_y - perp_y * half_w),
            ],
            "damage_base": self.MIN_DAMAGE
            + (self.MAX_DAMAGE - self.MIN_DAMAGE) * length_ratio,
        }

    def build_spiral_charge_attack(
        self,
        caster_x: float,
        caster_y: float,
        target_x: float,
        target_y: float,
        held_time: float,
    ) -> dict:
        """Biến thể tấn công khi có TwistOfFateModifier: thay vì đâm thẳng, gai băng
        trồi lên thành 1 vòng cung bao quanh người chơi. Charge càng lâu,
        vòng cung càng khép kín (tối đa 360 độ)."""
        charge_ratio = self.charge_ratio(held_time)

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

        # Cung tròn (Arc) mở rộng dựa trên charge_ratio.
        # Gồng tối đa (charge_ratio = 1.0) tạo vòng tròn khép kín 360 độ (math.tau).
        # Gồng ít nhất tạo vòng cung nhỏ (~60 độ).
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
            "damage_base": self.MIN_DAMAGE
            + (self.MAX_DAMAGE - self.MIN_DAMAGE) * charge_ratio,
        }

    def targets_in_ice_spiral(self, attack: dict, enemies: list) -> list:
        """Kiểm tra quái nằm trong cung tròn của vòng băng (build_spiral_charge_attack)."""
        hits = []
        cx = attack["start_x"]
        cy = attack["start_y"]
        radius = attack["radius"]
        aim_angle = attack["aim_angle"]
        arc_length = attack["arc_length_rad"]
        thickness = self.HITBOX_WIDTH

        for enemy in enemies:
            if not enemy.alive:
                continue

            dx = enemy.x - cx
            dy = enemy.y - cy
            dist = math.hypot(dx, dy)

            # Kiểm tra khoảng cách có nằm trong độ dày tường băng không
            if abs(dist - radius) <= thickness / 2 + enemy.radius:
                angle = math.atan2(dy, dx)
                # Chuẩn hóa góc về [-pi, pi] so với aim_angle
                diff = (angle - aim_angle + math.pi) % math.tau - math.pi
                if abs(diff) <= arc_length / 2 + (enemy.radius / max(1.0, radius)):
                    hits.append(enemy)

        return hits

    def apply_charge_hit(self, enemy, damage: float, charge_ratio: float, stack: int = 1) -> None:
        enemy.take_damage(damage)
        chill = StatusEffect(
            effect_type="chill",
            damage_per_sec=0.0,
            duration=self.SLOW_DURATION * (1.0 + 0.35 * charge_ratio),
            stacks=self.CHILL_PER_HIT * stack,
            max_stacks=self.CHILL_FREEZE_THRESHOLD,
        )
        enemy.add_status(chill)

    def get_display_name(self) -> str:
        return "Ice Rune"

    def get_description(self) -> str:
        return ("Shards of ice, that can be charged to hit foes from a great distance.\n"
                f"◆ Damage: {int(self.MIN_DAMAGE)} <-> {int(self.MAX_DAMAGE)}\n"
                f"◆ Duration: 0.0s <-> {self.CHARGE_MAX_TIME}s\n"
                f"◆ Speed: {self.SPEED}\n"
                f"◆ Apply {self.CHILL_PER_HIT} Chill\n"
                "◆ The longer the charge, the greater its damage and range")

    def get_color(self) -> tuple:
        return (100, 200, 255)
