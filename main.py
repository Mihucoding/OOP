from ui.game_loop import GameLoop

"""
File gốc để chạy toàn bộ trò chơi Rune Craft.
Nó đóng vai trò là "điểm vào" (entry point) của ứng dụng.
Quy trình:
1. Import lớp GameLoop (cỗ máy vòng lặp chính của game).
2. Tạo instance `game = GameLoop()`.
3. Gọi `game.run()` để bắt đầu vòng lặp vô tận (render khung hình và cập nhật logic).

👉 BƯỚC TIẾP THEO (Bước 2): Hãy mở file [ui/game_loop.py](file:///c:/Users/acer/Downloads/OOP-mihu_branch/ui/game_loop.py) và tìm đọc hàm `__init__` để xem game chuẩn bị những gì trước khi chạy.
"""

if __name__ == "__main__":
    game = GameLoop()
    game.run()

    