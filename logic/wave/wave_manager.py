import random
import math


class WaveManager:
    """
    Quản lý spawn quái và boss.
    - Spawn theo thời gian: mỗi SPAWN_INTERVAL giây spawn 1 nhóm quái
    - Random spawn nhỏ: mỗi RANDOM_INTERVAL giây spawn 1 quái ngẫu nhiên
    - Boss: sau BOSS_WAVE waves hoặc BOSS_TIME giây
    - Từ wave 2 trở đi: 30% cơ hội spawn RangedEnemy thay vì Enemy thường
    """
    SPAWN_INTERVAL   = 15.0   # giây giữa 2 đợt spawn chính
    SPAWN_COUNT_BASE = 3      # quái mỗi đợt ban đầu
    RANDOM_INTERVAL  = 8      # giây random spawn nhỏ

    BOSS_WAVE = 8             # boss xuất hiện sau wave này
    BOSS_TIME = 12 * 60       # hoặc sau 12 phút

    WORLD_SPAWN_RADIUS = 700  # spawn ngoài vùng nhìn của player
    RANGED_CHANCE      = 0.3  # 30% cơ hội spawn RangedEnemy (từ wave 2)

    def __init__(self):
        self.wave         = 0
        self.time_elapsed = 0.0
        self.spawn_timer  = self.SPAWN_INTERVAL
        self.random_timer = self.RANDOM_INTERVAL
        self.boss_spawned = False
        self.boss_alive   = False
        self.enemies: list = []
        self.boss          = None

    def update(self, dt: float, player_x: float, player_y: float,
               enemy_list: list, boss_ref) -> dict:
        """
        Trả về dict events:
        {
          'spawn_enemies': list[tuple(x, y, type)],  # type = 'normal' | 'ranged'
          'spawn_boss':    bool,
          'summon_enemies': int,
        }
        """
        self.time_elapsed += dt
        
        hp_mult = 1.0 + (self.wave * 0.05)
        speed_mult = 1.0 + (self.wave * 0.02)
        
        events = {
            'spawn_enemies':  [],
            'spawn_boss':     False,
            'summon_enemies': 0,
            'hp_mult':        hp_mult,
            'speed_mult':     speed_mult,
            'new_wave_started': False,
        }

        # Đợt spawn chính (theo thời gian)
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_timer = self.SPAWN_INTERVAL
            self.wave       += 1
            events['new_wave_started'] = True
            events['hp_mult'] = 1.0 + (self.wave * 0.05)
            events['speed_mult'] = 1.0 + (self.wave * 0.02)
            
            count = self.SPAWN_COUNT_BASE + self.wave
            for _ in range(count):
                pos        = self._random_spawn_pos(player_x, player_y)
                rand_val = random.random()
                if self.wave >= 10 and rand_val < 0.15:
                    enemy_type = 'tank'
                elif self.wave >= 5 and rand_val < 0.35:
                    enemy_type = 'fast'
                elif self.wave >= 2 and rand_val < 0.65:
                    enemy_type = 'ranged'
                else:
                    enemy_type = 'normal'
                events['spawn_enemies'].append((pos[0], pos[1], enemy_type))

        # Random spawn nhỏ
        self.random_timer -= dt
        if self.random_timer <= 0:
            self.random_timer = self.RANDOM_INTERVAL
            pos = self._random_spawn_pos(player_x, player_y)
            events['spawn_enemies'].append((pos[0], pos[1], 'normal'))

        # Boss trigger: sau BOSS_WAVE waves hoặc BOSS_TIME giây
        if not self.boss_spawned:
            if self.wave >= self.BOSS_WAVE or self.time_elapsed >= self.BOSS_TIME:
                self.boss_spawned = True
                events['spawn_boss'] = True

        # Boss summon: đọc cờ pending_summon từ boss
        if boss_ref and getattr(boss_ref, 'alive', False) and boss_ref.pending_summon:
            events['summon_enemies'] = boss_ref.SUMMON_COUNT
            boss_ref.pending_summon  = False

        return events

    def _random_spawn_pos(self, player_x: float, player_y: float) -> tuple:
        angle = random.uniform(0, 2 * math.pi)
        x     = player_x + math.cos(angle) * self.WORLD_SPAWN_RADIUS
        y     = player_y + math.sin(angle) * self.WORLD_SPAWN_RADIUS
        return (x, y)

    def get_wave_info(self) -> str:
        if self.boss_spawned:
            return "BOSS"
        return f"Wave {self.wave}"
