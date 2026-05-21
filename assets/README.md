# Assets Folder Structure

```
assets/
├── fonts/
│   └── [game fonts - .ttf, .otf files]
├── sounds/
│   └── [audio files - .wav, .mp3]
└── sprites/
    ├── [character/entity images - .png]
    └── effects/ [optional subfolder for effect sprites]
```

## Hướng dẫn tải/sử dụng Assets

### Bước 1: Tìm/tải assets phù hợp
- **Sprites:** itch.io, opengameart.org (tìm "roguelike sprite", "bullet", "enemy")
- **Sounds:** freesound.org, zapsplat.com (tìm sound effects + background music)
- **Fonts:** Google Fonts (tải .ttf), fontawesome nếu cần icon

### Bước 2: Đặt file vào thư mục tương ứng
- Tất cả ảnh vào `sprites/`
- Tất cả âm thanh vào `sounds/`
- Tất cả font vào `fonts/`

### Bước 3: Load trong code
- Xem README.md trong từng subfolder để biết cách load

## Ghi chú
- **Optional:** Hiện tại code dùng colored shapes, bạn có thể thêm sprites sau
- Tất cả file được ignore trong `.gitignore` (nếu có) để tiết kiệm repo size
- Hãy check license trước khi dùng asset từ internet!
