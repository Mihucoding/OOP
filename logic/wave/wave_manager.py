import random
import math


class WaveManager:
    """
    Quản lý spawn quái và boss.
    - Spawn theo thời gian: mỗi SPAWN_INTERVAL giây spawn 1 nhóm quái
    - Random spawn nhỏ: mỗi RANDOM_INTERVAL giây spawn 1 quái ngẫu nhiên
    - Boss: sau BOSS_WAVE waves hoặc BOSS_TIME giây
<<<<<<< HEAD
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
=======
    """
    SPAWN_INTERVAL = 8.0     # giây giữa 2 đợt spawn chính
    SPAWN_COUNT_BASE = 3     # quái mỗi đợt ban đầu
    RANDOM_INTERVAL = 3.0    # giây random spawn nhỏ

    BOSS_WAVE = 4            # boss xuất hiện sau wave này
    BOSS_TIME = 7 * 60       # hoặc sau 7 phút

    WORLD_SPAWN_RADIUS = 700  # spawn ngoài vùng nhìn của player

    def __init__(self):
        self.wave = 0
        self.time_elapsed = 0.0
        self.spawn_timer = self.SPAWN_INTERVAL
        self.random_timer = self.RANDOM_INTERVAL
        self.boss_spawned = False
        self.boss_alive = False
        self.enemies: list = []   # game loop gán vào
        self.boss = None
>>>>>>> 3e15ae77a0ed8863193acdf98696434a388c7c55

    def update(self, dt: float, player_x: float, player_y: float,
               enemy_list: list, boss_ref) -> dict:
        """
        Trả về dict events:
        {
<<<<<<< HEAD
          'spawn_enemies': list[tuple(x, y, type)],  # type = 'normal' | 'ranged'
          'spawn_boss':    bool,
          'summon_enemies': int,
        }
        """
        self.time_elapsed += dt
        events = {
            'spawn_enemies':  [],
            'spawn_boss':     False,
            'summon_enemies': 0,
        }

        # Đợt spawn chính (theo thời gian)
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_timer = self.SPAWN_INTERVAL
            self.wave       += 1
            count = self.SPAWN_COUNT_BASE + self.wave
            for _ in range(count):
                pos        = self._random_spawn_pos(player_x, player_y)
                enemy_type = (
                    'ranged'
                    if self.wave >= 2 and random.random() < self.RANGED_CHANCE
                    else 'normal'
                )
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
=======
          'spawn_enemies': list[tuple(x,y)],   # vị trí spawn quái mới
          'spawn_boss': bool,                   # có spawn boss không
          'summon_enemies': int,                # số quái boss triệu hồi
        }
        """
        # 1. Cộng time_elapsed
        # 2. Đếm spawn_timer, khi hết → spawn nhóm quái, wave += 1
        #    số quái mỗi wave = SPAWN_COUNT_BASE + wave (tăng dần)
        # 3. Đếm random_timer, khi hết → spawn 1 quái ngẫu nhiên
        # 4. Kiểm tra boss trigger (wave >= BOSS_WAVE hoặc time >= BOSS_TIME)
        # 5. Nếu boss tồn tại và pending_summon=True → spawn summon
        # Trả về events dict
        pass

    def _random_spawn_pos(self, player_x: float, player_y: float) -> tuple:
        # Sinh vị trí spawn ngẫu nhiên xung quanh player (ngoài WORLD_SPAWN_RADIUS)
        # angle = random, x = player_x + cos(angle)*WORLD_SPAWN_RADIUS, ...
        pass
>>>>>>> 3e15ae77a0ed8863193acdf98696434a388c7c55

    def get_wave_info(self) -> str:
        if self.boss_spawned:
            return "BOSS"
        return f"Wave {self.wave}"
