import math

class LightningSpiralAttack:
    """
    Logic tấn công của Lightning khi có SpiralModifier (Vòng cung tĩnh/Vortex Ring).
    Được gọi từ GameLoop để bóc tách logic.
    """
    
    def execute(
        self,
        game_loop,
        target_x: float,
        target_y: float,
        primary_damage: float,
        chain_damage: float,
        max_targets: int,
        alive_before: set,
        boss_alive_before: bool,
    ) -> bool:
        # Lấy hằng số từ game_loop module
        from ui.game_loop import LIGHTNING_BEAM_RANGE
        
        # Bán kính thu nhỏ lại để bao sát người hơn (như yêu cầu "thu nhỏ bán kính")
        radius = LIGHTNING_BEAM_RANGE * 0.55
        
        # 1. Tính toán quỹ đạo vòng cung tĩnh
        cx, cy = game_loop.player.x, game_loop.player.y
        aim_x, aim_y = game_loop._lightning_aim_direction(target_x, target_y)
        orbit_angle = math.atan2(aim_y, aim_x)
        
        # Khoảng hở GAP trong renderer là 0.7. Góc bắt đầu vòng cung là orbit_angle + 0.35.
        start_angle = orbit_angle + 0.35
        
        # Điểm bắt đầu vòng cung để tia thẳng nối vào (link point)
        link_x = cx + math.cos(start_angle) * radius
        link_y = cy + math.sin(start_angle) * radius
        
        # Điểm tâm khoảng hở để UI biết cách xoay vòng cung
        gap_x = cx + math.cos(orbit_angle) * radius
        gap_y = cy + math.sin(orbit_angle) * radius
        
        # Xóa các beam cũ. Ta cần 2 beam: 1 tia thẳng, 1 vòng cung.
        game_loop._trim_primary_lightning_beams(2)
        
        # Tia 1: Tia thẳng xuất phát từ nhân vật nối khít vào điểm BẮT ĐẦU của đường tròn
        game_loop._set_primary_lightning_beam(cx, cy, link_x, link_y, beam_id=0, vortex=False)
        
        # Tia 2: Vòng cung khép kín bao quanh nhân vật
        game_loop._set_primary_lightning_beam(cx, cy, gap_x, gap_y, beam_id=1, vortex=True)
        
        if aim_x < 0:
            game_loop.player.facing_dir = -1
        elif aim_x > 0:
            game_loop.player.facing_dir = 1
            
        # 2. Xử lý sát thương (Tìm quái trong bán kính orbit)
        ring_hits = game_loop._targets_in_vortex(cx, cy, radius)
        for i, target in enumerate(ring_hits[:max_targets]):
            dmg = primary_damage if i == 0 else chain_damage
            target.take_damage(dmg)
            
        # 3. Rớt XP nếu quái chết
        game_loop._drop_xp_from_ultimate_kills(alive_before, boss_alive_before)
        
        return True
