import random
import math


class WaveManager:
    """
    Quản lý spawn quái và boss.
    - Spawn theo thời gian: mỗi SPAWN_INTERVAL giây spawn 1 nhóm quái
    - Random spawn nhỏ: mỗi RANDOM_INTERVAL giây spawn 1 quái ngẫu nhiên
    - Boss: sau BOSS_WAVE waves hoặc BOSS_TIME giây
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

    def update(self, dt: float, player_x: float, player_y: float,
               enemy_list: list, boss_ref) -> dict:
        """
        Trả về dict events:
        {
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

    def get_wave_info(self) -> str:
        if self.boss_spawned:
            return "BOSS"
        return f"Wave {self.wave}"
