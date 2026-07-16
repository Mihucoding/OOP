"""Quản lý âm thanh (SFX) đơn giản cho game.

Chỉ thuộc lớp `ui/` (được phép import pygame). Load sẵn các sound và phát theo
tên khoá, có throttle để tránh spam khi bắn liên tục. Nếu máy không có thiết bị
âm thanh (headless/CI) thì tự tắt an toàn, không làm crash game.
"""
import os
import pygame

# Thư mục chứa SFX phép thuật trong asset pack.
_SPELLS_SUBPATH = os.path.join(
    "assets", "sounds",
    "Free Fantasy SFX Pack By TomMusic",
    "Free Fantasy SFX Pack By TomMusic",
    "OGG Files", "SFX", "Spells",
)


class AudioManager:
    """Load + phát hiệu ứng âm thanh với throttle theo từng khoá."""

    def __init__(self, volume: float = 0.6) -> None:
        self._enabled = False
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._last_play_ms: dict[str, int] = {}
        self._music_path: str | None = None
        self._music_key: str | None = None   # bài nhạc đang phát (None = im lặng)

        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
            self._enabled = True
        except pygame.error:
            self._enabled = False
            return

        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        spells = os.path.join(root, _SPELLS_SUBPATH)
        sounds = os.path.join(root, "assets", "sounds")

        # Khoá logic → tên file sound.
        self._register("fire_spray",  os.path.join(spells, "Firespray 1.ogg"), volume)
        self._register("ice_barrage", os.path.join(spells, "Ice Barrage 1.ogg"), volume)
        self._register("fireball",    os.path.join(spells, "Fireball 1.ogg"),   volume)
        self._register("footstep",    os.path.join(sounds, "hit_co.mp3"),       volume * 0.5)
        self._register("on_hit",      os.path.join(sounds, "on_hit.wav"),       volume * 0.6)
        self._register("level_up",    os.path.join(sounds, "level_up.mp3"),     volume)

        # Nhạc nền (stream qua mixer.music, không load vào RAM như Sound).
        boss_music = os.path.join(sounds, "background.mp3")
        if os.path.exists(boss_music):
            self._music_files = {"boss": boss_music}
        else:
            self._music_files = {}

    def _register(self, key: str, path: str, volume: float) -> None:
        try:
            snd = pygame.mixer.Sound(path)
            snd.set_volume(volume)
            self._sounds[key] = snd
        except (pygame.error, FileNotFoundError):
            pass   # thiếu file → bỏ qua khoá đó, không crash

    def play(self, key: str, throttle_ms: int = 80) -> None:
        """Phát sound theo khoá. Bỏ qua nếu chưa đủ `throttle_ms` từ lần trước."""
        if not self._enabled:
            return
        snd = self._sounds.get(key)
        if snd is None:
            return
        now = pygame.time.get_ticks()
        if now - self._last_play_ms.get(key, -99999) < throttle_ms:
            return
        self._last_play_ms[key] = now
        snd.play()

    def play_music(self, key: str, volume: float = 0.5) -> None:
        """Phát nhạc nền lặp vô hạn (loops=-1 → tự động 'reload'). Bỏ qua nếu
        bài đó đang phát rồi (tránh restart mỗi frame)."""
        if not self._enabled or key == self._music_key:
            return
        path = self._music_files.get(key)
        if path is None:
            return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(loops=-1)
            self._music_key = key
        except pygame.error:
            pass

    def stop_music(self) -> None:
        """Dừng nhạc nền (VD boss chết / thua / về menu)."""
        if not self._enabled or self._music_key is None:
            return
        try:
            pygame.mixer.music.stop()
        except pygame.error:
            pass
        self._music_key = None
