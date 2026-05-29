# Nhật ký Cập nhật (Change Log)

Gửi Leader, dưới đây là những thay đổi và cập nhật mình vừa đưa vào project để bạn tiện review (chuẩn bị cho việc Pull Request):

## 1. Dọn dẹp lỗi Xung đột (Merge Conflicts) toàn dự án
- Đã sửa lỗi toàn bộ các file trong thư mục `logic/` và `ui/` bị dính các thẻ báo lỗi Git (`<<<<<<< HEAD`, `=======`) do quá trình trộn code bị lỗi trước đó.
- Code hiện tại đã quay trở lại cấu trúc Clean Architecture nguyên bản và chạy cực kỳ ổn định thông qua `main.py` ở thư mục gốc (vẫn giữ được map nền đất đẹp).

## 2. Hệ thống Độ khó theo Wave (Difficulty Scaling)
- **Tính năng Scale độ khó:**
  - **Máu quái (HP)**: Tăng thêm 5% mỗi Wave.
  - **Tốc độ (Speed)**: Tăng thêm 2% mỗi Wave.
  - Cả Quái Cận chiến, Bắn xa và Boss đều được áp dụng hệ số nhân (Multiplier) này một cách đồng bộ thông qua hàm khởi tạo `__init__`.

## 3. Thêm 2 loại Quái Mới (Đúng chuẩn OOP)
- Tách riêng 2 loại quái mới thành các file độc lập kế thừa từ class `Enemy` gốc (`logic/entities/fast_enemy.py` và `logic/entities/tank_enemy.py`):
  - **FastEnemy** (Quái nhanh): Máu cơ bản 30, Tốc độ 150. (Bắt đầu xuất hiện ngẫu nhiên từ Wave 5).
  - **TankEnemy** (Quái trâu/Đỡ đòn): Máu cơ bản 200, Tốc độ 40. (Bắt đầu xuất hiện ngẫu nhiên từ Wave 10).
- **Lưu ý thiết kế OOP:** Đã thiết lập lại `Enemy.__init__` dùng `self.__class__` để lấy số liệu động. Do đó `FastEnemy` và `TankEnemy` không cần định nghĩa lại hàm `__init__`, giúp code cực kì gọn.

## 4. Giao diện (UI) Thông báo Wave
- Đã thêm logic vào `ui/game_loop.py` để hiển thị dòng thông báo Wave ở giữa màn hình mỗi khi chuyển Wave. Dòng chữ sẽ tự động mờ dần (Fade out) và biến mất sau 3 giây.
- Có tính năng cảnh báo khi có quái mới:
  - Wave 5: `WAVE 5 - FAST ENEMIES APPEAR!`
  - Wave 10: `WAVE 10 - TANK ENEMIES APPEAR!`
  - Wave Boss: `WARNING: BOSS INCOMING!`

## 5. Cập nhật Unit Tests
- Đã viết thêm 3 Unit Test mới cho cơ chế Multiplier (hệ số máu/tốc độ) và 2 class quái mới vào `tests/test_entities.py`.
- Toàn bộ codebase hiện tại đã được Test phủ: Tổng cộng **43/43 tests** đều chạy thành công (Passed).

## 6. Nâng cấp AI Cận chiến (Action Roguelike) & Hitbox
- **Xóa bỏ Sát thương Chạm thân (Contact Damage)** cho quái thường. Giờ đây quái sẽ không tự động trừ máu khi cọ xát vào người chơi.
- Bổ sung **State Machine (Máy Trạng Thái)** cho quái: `RUN` -> `ATTACK` -> `COOLDOWN`. Quái tiếp cận, đứng lại thực hiện đòn chém, và chỉ tạo vùng **Hitbox Vũ khí** ngay tại khoảnh khắc chém.
- Con `FastEnemy` được trang bị riêng cơ chế **Wind-up (gồng)** và **Lunge (lao cực nhanh)** tạo độ khó cao, bắt buộc người chơi phải dùng kỹ năng lướt (Dash) để né.

## 7. Tích hợp Hoạt ảnh (Sprite Animations)
- **Enemy Thường**: Được khoác lên bộ áo của Nấm Nổi Điên (`assets/sprites/Mushroom`). Đầy đủ animation: Chạy, Cắn, Bị bắn trúng (Hit) và Nằm gục (Die).
- **Ranged Enemy**: Sử dụng bộ áo Quái vật Bay (`assets/sprites/Ranged`). Đã bổ sung logic "đứng yên khóa chân (`cast_lock`) trong 0.5s" khi bắn đạn để tạo cảm giác thực tế.
- Xử lý mượt mà hiện tượng Moonwalk (tự động quay đầu `facing_dir`), đồng bộ thời gian chết để không bị lỗi hitbox, và tinh chỉnh vị trí Thanh Máu (HP Bar) lên cao để không bị che bởi Sprite.

> **Lời nhắn:** Kế hoạch hiện tại là chúng ta sẽ thống nhất giữ vững cấu trúc thư mục Clean Architecture này (`logic/` và `ui/` phân tách rõ ràng) để dễ test và tránh conflict về sau nhé! Cả phần Hitbox cận chiến này sau này có thể tái sử dụng dễ dàng cho người chơi.
