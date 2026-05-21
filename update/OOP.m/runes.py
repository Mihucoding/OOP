import math
import pygame

class RuneNode:
    """Class gốc định nghĩa các sự kiện và UI của Rune"""
    def __init__(self, name, cost):
        self.name = name
        self.cost = cost
        self.children = []
        self.parent = None # Trỏ tới Node cha để dễ tháo lắp
        
        # UI Properties (Tọa độ vẽ trên Menu)
        self.ui_x = 0
        self.ui_y = 0
        self.ui_radius = 25
        self.is_dragging = False

    def get_total_cost(self):
        """Tính tổng dung lượng (cost) của nhánh này"""
        total = self.cost
        for child in self.children:
            total += child.get_total_cost()
        return total

    def detach(self):
        """Tháo node này ra khỏi cha của nó"""
        if self.parent:
            self.parent.children.remove(self)
            self.parent = None

    def try_attach(self, new_parent, core_node):
        """Thử gắn vào một node cha mới, kiểm tra dung lượng"""
        # Nếu đang gắn ở nhánh khác, tạm tính dung lượng nếu rút nó ra
        current_used = core_node.get_total_cost()
        if self.parent:
            current_used -= self.get_total_cost()
            
        # Kiểm tra xem dung lượng còn lại có đủ để gắn nhánh này vào không
        if core_node.max_capacity - current_used >= self.get_total_cost():
            self.detach() # Rút khỏi chỗ cũ
            new_parent.children.append(self) # Gắn vào chỗ mới
            self.parent = new_parent
            return True
        return False

    def on_spawn(self, projectile, spell_manager):
        for child in self.children: child.on_spawn(projectile, spell_manager)

    def on_update(self, projectile, dt, spell_manager):
        for child in self.children: child.on_update(projectile, dt, spell_manager)

    def on_hit(self, projectile, target, spell_manager):
        for child in self.children: child.on_hit(projectile, target, spell_manager)

    # UI Draw
    def draw_node(self, screen, font):
        color = (200, 200, 200) if self.cost > 0 else (255, 165, 0) # Màu khác nhau cho Lõi và Modifier
        if self.is_dragging:
            color = (0, 255, 0) # Highlight màu xanh khi đang kéo
            
        pygame.draw.circle(screen, color, (int(self.ui_x), int(self.ui_y)), self.ui_radius)
        pygame.draw.circle(screen, (255, 255, 255), (int(self.ui_x), int(self.ui_y)), self.ui_radius, 2)
        
        # Cắt chữ cái đầu tiên để in lên hình tròn
        text = font.render(self.name[:2], True, (0, 0, 0))
        text_rect = text.get_rect(center=(self.ui_x, self.ui_y))
        screen.blit(text, text_rect)


# ================= CÁC LOẠI RUNE CỤ THỂ (TIẾNG ANH) =================
class CoreRune(RuneNode):
    def __init__(self, element, capacity):
        super().__init__(f"{element} Core", 0)
        self.element = element
        self.max_capacity = capacity
        
        # Define fixed slots: (id, rel_x, rel_y, parent_id)
        # Slot 0 is always the Core itself.
        self.slots = []
        self._init_layout()

    def _init_layout(self):
        if self.element == "Fire":
            self.slots = [
                {'id': 0, 'rel_x': 0,    'rel_y': 0,   'parent_id': -1, 'rune': self},
                {'id': 1, 'rel_x': -100, 'rel_y': 60,  'parent_id': 0,  'rune': None}, # Left
                {'id': 2, 'rel_x': 0,    'rel_y': 100, 'parent_id': 0,  'rune': None}, # Center 1
                {'id': 3, 'rel_x': 0,    'rel_y': 190, 'parent_id': 2,  'rune': None}, # Center 2
                {'id': 4, 'rel_x': 100,  'rel_y': 60,  'parent_id': 0,  'rune': None}, # Right 1
                {'id': 5, 'rel_x': 100,  'rel_y': 150, 'parent_id': 4,  'rune': None}, # Right 2
            ]
        elif self.element == "Ice":
            self.slots = [
                {'id': 0, 'rel_x': 0,    'rel_y': 0,   'parent_id': -1, 'rune': self},
                {'id': 1, 'rel_x': 0,    'rel_y': 90,  'parent_id': 0,  'rune': None}, # Center 1
                {'id': 2, 'rel_x': 0,    'rel_y': 180, 'parent_id': 1,  'rune': None}, # Center 2
                {'id': 3, 'rel_x': 100,  'rel_y': 120, 'parent_id': 1,  'rune': None}, # Right 1
                {'id': 4, 'rel_x': 100,  'rel_y': 210, 'parent_id': 3,  'rune': None}, # Right 2
                {'id': 5, 'rel_x': -100, 'rel_y': 240, 'parent_id': 2,  'rune': None}, # Left branch
            ]
        elif self.element == "Lightning":
            self.slots = [
                {'id': 0, 'rel_x': 0,    'rel_y': 0,   'parent_id': -1, 'rune': self},
                {'id': 1, 'rel_x': -110, 'rel_y': 50,  'parent_id': 0,  'rune': None}, # Left 1
                {'id': 2, 'rel_x': -110, 'rel_y': 150, 'parent_id': 1,  'rune': None}, # Left 2
                {'id': 3, 'rel_x': 110,  'rel_y': 50,  'parent_id': 0,  'rune': None}, # Right 1
                {'id': 4, 'rel_x': 110,  'rel_y': 150, 'parent_id': 3,  'rune': None}, # Right 2
                {'id': 5, 'rel_x': 0,    'rel_y': 110, 'parent_id': 3,  'rune': None}, # Center from Right
            ]
        elif self.element == "Wind":
            self.slots = [
                {'id': 0, 'rel_x': 0,    'rel_y': 0,   'parent_id': -1, 'rune': self},
                {'id': 1, 'rel_x': 0,    'rel_y': 90,  'parent_id': 0,  'rune': None}, # Center 1
                {'id': 2, 'rel_x': -100, 'rel_y': 90,  'parent_id': 1,  'rune': None}, # Branch Left
                {'id': 3, 'rel_x': 0,    'rel_y': 180, 'parent_id': 1,  'rune': None}, # Center 2
                {'id': 4, 'rel_x': 100,  'rel_y': 180, 'parent_id': 3,  'rune': None}, # Branch Right
                {'id': 5, 'rel_x': 0,    'rel_y': 270, 'parent_id': 3,  'rune': None}, # Center 3
            ]
        else: # Default
            self.slots = [
                {'id': 0, 'rel_x': 0, 'rel_y': 0, 'parent_id': -1, 'rune': self},
            ]

    def get_total_cost(self):
        total = 0
        for s in self.slots:
            if s['rune'] and s['rune'] != self:
                total += s['rune'].cost
        return total

    def try_attach_to_slot(self, rune, slot_id):
        if slot_id < 0 or slot_id >= len(self.slots): return False
        slot = self.slots[slot_id]
        if slot['rune'] is not None: return False # Already occupied
        
        # Parent check: slot must have a parent that is occupied
        if slot['parent_id'] != -1:
            parent_slot = self.slots[slot['parent_id']]
            if parent_slot['rune'] is None: return False
            
        # Capacity check
        current_used = self.get_total_cost()
        if self.max_capacity - current_used >= rune.cost:
            # If it was in another slot, clear it?
            # Actually, the inventory logic handles tháo lắp.
            slot['rune'] = rune
            rune.parent = slot['rune'] # Dummy parent for logic compatibility or just use slot info
            return True
        return False
        
    def find_slot_by_rune(self, rune):
        for s in self.slots:
            if s['rune'] == rune: return s
        return None

    def remove_rune(self, rune):
        for s in self.slots:
            if s['rune'] == rune:
                s['rune'] = None
                rune.parent = None
                return True
        return False

    def on_spawn(self, projectile, spell_manager):
        # We need to execute runes in tree order (from slots)
        # For simplicity, just iterate slots that have runes
        for s in self.slots:
            if s['rune'] and s['rune'] != self:
                s['rune'].on_spawn(projectile, spell_manager)

    def on_update(self, projectile, dt, spell_manager):
        for s in self.slots:
            if s['rune'] and s['rune'] != self:
                s['rune'].on_update(projectile, dt, spell_manager)

    def on_hit(self, projectile, target, spell_manager):
        for s in self.slots:
            if s['rune'] and s['rune'] != self:
                s['rune'].on_hit(projectile, target, spell_manager)

class SplitRune(RuneNode):
    def __init__(self):
        super().__init__("Split Modifier", 2)
        
    def on_spawn(self, projectile, spell_manager):
        if not getattr(projectile, 'has_split', False):
            projectile.has_split = True
            for angle in [-0.3, 0.3]:
                cos_a, sin_a = math.cos(angle), math.sin(angle)
                nx = projectile.dir_x * cos_a - projectile.dir_y * sin_a
                ny = projectile.dir_x * sin_a + projectile.dir_y * cos_a
                # Create a new projectile of the same class
                proj_class = projectile.__class__
                # Build common parameters
                kwargs = {
                    'spell_manager': spell_manager,
                    'core_tree': spell_manager.core_tree,
                    'trigger_spawn': False
                }
                
                # Handle different class signatures
                if hasattr(projectile, 'player'): # Wind
                    new_p = proj_class(
                        projectile.x, projectile.y, projectile.x + nx, projectile.y + ny,
                        projectile.speed, projectile.radius, projectile.damage,
                        projectile.player, **kwargs
                    )
                elif hasattr(projectile, 'length') and projectile.length > 0: # Ice
                    new_p = proj_class(
                        projectile.x, projectile.y, projectile.x + nx, projectile.y + ny,
                        projectile.speed, projectile.radius, projectile.damage,
                        projectile.length, **kwargs
                    )
                else: # Default Fire/Lightning
                    new_p = proj_class(
                        projectile.x, projectile.y, projectile.x + nx, projectile.y + ny,
                        projectile.speed, projectile.radius, projectile.damage,
                        projectile.color, **kwargs
                    )
                
                new_p.has_split = True
                spell_manager.projectiles.append(new_p)
        super().on_spawn(projectile, spell_manager)

class BounceRune(RuneNode):
    def __init__(self):
        super().__init__("Bounce Modifier", 2)

    def on_hit(self, projectile, target, spell_manager):
        bounces = getattr(projectile, 'bounce_count', 0)
        if bounces < 2:  # Số lần nảy tối đa (2 lần)
            best_target, min_dist = None, 9999
            
            # Tìm quái gần nhất để nảy tới
            for enemy in spell_manager.enemies_ref:
                if enemy != target and enemy.alive:
                    dist = math.hypot(enemy.x - projectile.x, enemy.y - projectile.y)
                    if dist < min_dist and dist < 250:  # Phạm vi tìm mục tiêu nảy (250px)
                        min_dist, best_target = dist, enemy
            
            if best_target:
                projectile.bounce_count = bounces + 1
                dx, dy = best_target.x - projectile.x, best_target.y - projectile.y
                dist = math.hypot(dx, dy)
                
                if dist > 0: 
                    # 1. Đổi hướng cho đạn thông thường
                    if hasattr(projectile, 'dir_x'):
                        projectile.dir_x, projectile.dir_y = dx / dist, dy / dist
                    
                    # 2. Đổi hướng cho đạn dùng vector vận tốc (vx, vy)
                    if hasattr(projectile, 'vx'):
                        speed = math.hypot(projectile.vx, projectile.vy)
                        if speed == 0: speed = 400
                        projectile.vx, projectile.vy = (dx / dist) * speed, (dy / dist) * speed
                
                # Bật cờ sống sót
                projectile.alive = True
                projectile.is_alive = True
                projectile.is_bouncing = True  # Ra hiệu cho main.py đừng xóa đạn
                projectile.lifetime += 0.5     # Tăng thêm tgian sống để kịp bay tới đích
                
        super().on_hit(projectile, target, spell_manager)

class SpiralRune(RuneNode):
    def __init__(self):
        super().__init__("Spiral Modifier", 1)

    def on_update(self, projectile, dt, spell_manager):
        cos_a, sin_a = math.cos(10 * dt), math.sin(10 * dt)
        nx = projectile.dir_x * cos_a - projectile.dir_y * sin_a
        ny = projectile.dir_x * sin_a + projectile.dir_y * cos_a
        projectile.dir_x, projectile.dir_y = nx, ny
        super().on_update(projectile, dt, spell_manager)

class HeavyBurdenRune(RuneNode):
    def __init__(self):
        super().__init__("Heavy Burden", 1)
    def on_spawn(self, projectile, spell_manager):
        projectile.damage *= 1.15
        projectile.radius *= 1.2
        super().on_spawn(projectile, spell_manager)

class HeavyHitterRune(RuneNode):
    def __init__(self):
        super().__init__("Heavy Hitter", 2)
    def on_spawn(self, projectile, spell_manager):
        projectile.damage *= 1.5
        if hasattr(projectile, 'speed'):
            projectile.speed *= 0.75
        super().on_spawn(projectile, spell_manager)

class SelfCenteredRune(RuneNode):
    def __init__(self):
        super().__init__("Self-Centered", 2)
        
    def on_spawn(self, projectile, spell_manager):
        projectile.lifetime *= 2.0
        
        # Lưu biến
        projectile.start_lifetime = projectile.lifetime
        
        # Đề phòng vũ khí không có dir_y, dir_x (xài getattr thay vì truy cập trực tiếp)
        dir_y = getattr(projectile, 'dir_y', 0)
        dir_x = getattr(projectile, 'dir_x', 1)
        projectile.start_angle = math.atan2(dir_y, dir_x)
        
        projectile.speed = 0
        super().on_spawn(projectile, spell_manager)

    def on_update(self, projectile, dt, spell_manager):
        # Fallback an toàn: Tự khởi tạo nếu thiếu (để game không bao giờ crash)
        if not hasattr(projectile, 'start_lifetime'):
            projectile.start_lifetime = getattr(projectile, 'lifetime', 1.0)
            projectile.start_angle = 0

        px, py = spell_manager.player.x, spell_manager.player.y
        rotation_speed = 15
        target_radius = 110
        
        elapsed = projectile.start_lifetime - projectile.lifetime
        
        # Hiệu ứng phóng to quỹ đạo trong 0.3s đầu
        transition_duration = 0.3 
        if elapsed < transition_duration:
            current_radius = target_radius * (elapsed / transition_duration)
        else:
            current_radius = target_radius
            
        current_angle = projectile.start_angle + (elapsed * rotation_speed)
        
        projectile.x = px + math.cos(current_angle) * current_radius
        projectile.y = py + math.sin(current_angle) * current_radius
        
        super().on_update(projectile, dt, spell_manager)