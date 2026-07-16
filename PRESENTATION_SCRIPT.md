# 🎮 Script Thuyết Trình — Rune Craft Roguelike

> **Dự án OOP**: 2D Top-down Survival Roguelike — Hệ thống Chế tạo Phép thuật (Rune Crafting)
> **Công nghệ**: Python 3.11 + Pygame-CE · 1280×720
> **Thời lượng gợi ý**: 12–15 phút (thuyết trình + demo)

---

## 🎬 PHẦN 0 — MỞ ĐẦU (Hook) · ~1 phút

> *(Mở sẵn game ở màn hình menu, chưa nhấn Play)*

"Chào thầy/cô và các bạn. Hãy tưởng tượng một trò chơi mà **không có hai người chơi nào giống nhau**. Một người biến phép lửa thành cơn mưa cầu lửa tự nổ; một người khác biến nó thành lưỡi kiếm xoay quanh mình như một cơn bão thép.

Điều thú vị là: chúng tôi **không code từng phép một**. Chúng tôi xây một **hệ thống** cho phép người chơi *tự lắp ghép* phép thuật từ những viên đá Rune — giống như xếp hình LEGO. Và đằng sau đó là một bài toán OOP kinh điển: **Composite Pattern**.

Đây là **Rune Craft Roguelike**."

> *(Nhấn Play, để game chạy nền vài giây rồi quay lại slide)*

---

## 📖 PHẦN 1 — GIỚI THIỆU DỰ ÁN · ~1.5 phút

**Thể loại**: Roguelike sinh tồn góc nhìn từ trên xuống. Người chơi đứng giữa bản đồ vô hạn, quái vật tràn tới theo từng đợt (wave), sống sót càng lâu càng mạnh, mục tiêu cuối là hạ **Boss**.

**Điểm khác biệt cốt lõi** — không nằm ở đồ họa, mà ở **hệ thống chế tạo phép**:
- 4 nguyên tố cơ bản (Lửa, Băng, Sét, Gió)
- Hơn 14 loại Rune bổ trợ (Modifier & Trigger)
- Người chơi ghép chúng thành **cây phép (Rune Tree)** → tạo ra hàng trăm tổ hợp phép khác nhau.

**3 mục tiêu OOP** mà dự án đặt ra và chứng minh:
1. **Composite Pattern** — cấu trúc cây phép lồng nhau
2. **Open/Closed Principle** — thêm phép mới không sửa code cũ
3. **Composition over Inheritance** — đạn không phân loại bằng kế thừa, mà bằng cây Rune gắn vào lúc chạy

---

## 🏛️ PHẦN 2 — KIẾN TRÚC & CẤU TRÚC · ~2.5 phút

### Nguyên tắc vàng: Tách `logic/` khỏi `ui/`

"Quy tắc bất biến số 1 của dự án: **thư mục `logic/` TUYỆT ĐỐI không được import pygame hay bất cứ thứ gì từ `ui/`**. Chỉ `ui/` mới được phép biết tới `logic/`."

> *(Chỉ vào sơ đồ)*

```
main.py                 ← điểm vào, chỉ gọi GameLoop().run()
│
├── logic/              ← "BỘ NÃO" — thuần Python, không pygame, test được độc lập
│   ├── entities/       → player, enemy, boss, bullet, xp_orb, status_effect...
│   ├── rune/           → TRÁI TIM: Composite Pattern
│   │   ├── rune_component.py   (ABC gốc)
│   │   ├── rune_tree.py        (cây phép)
│   │   ├── elements/           (Fire, Ice, Lightning, Wind)
│   │   └── modifiers/          (14+ rune bổ trợ)
│   ├── abilities/      → ultimate/, movement/ (dash)
│   ├── wave/           → wave_manager (sinh quái theo đợt)
│   └── leveling/       → level_manager, stat_upgrade
│
└── ui/                 ← "BỘ MẶT" — pygame, vẽ, âm thanh, input
    ├── game_loop.py    (vòng lặp chính, điều phối)
    ├── renderer.py     (vẽ mọi thứ)
    ├── hud.py, audio.py, input_handler.py
    └── screens/        (menu, level-up, builder, game-over, win)
```

**Vì sao tách như vậy?** — 2 lợi ích lớn:
1. **Kiểm thử được**: toàn bộ logic gameplay chạy và test bằng `pytest` mà **không cần mở cửa sổ game**.
2. **Thay giao diện không đụng logic**: có thể đổi từ Pygame sang engine khác mà `logic/` giữ nguyên.

> 💡 *Câu chốt*: "Đây chính là nguyên tắc **Separation of Concerns** — tách bạch mối quan tâm."

---

## ⭐ PHẦN 3 — ĐIỂM NHẤN OOP: COMPOSITE PATTERN · ~3 phút

> *(Đây là phần quan trọng nhất — nói chậm, có ví dụ)*

### Bài toán

"Nếu làm theo cách thông thường: mỗi loại phép là một class con — `FireBullet`, `SplitFireBullet`, `BouncingFireBullet`... Với 4 nguyên tố × 14 modifier, ta sẽ có **hàng trăm class**, và mỗi tổ hợp mới lại phải viết thêm class. Đây là **địa ngục kế thừa** (inheritance hell)."

### Lời giải: Composite Pattern

```
RuneComponent (ABC)               ← interface chung: on_hit, on_update, on_fire
│
├── ElementRune  (LEAF - lá)      ← chỉ định hiệu ứng khi TRÚNG: Fire cháy, Ice làm chậm
│
└── ModifierRune (COMPOSITE - nhánh)  ← thay đổi HÀNH VI đạn, và CÓ THỂ CHỨA RUNE CON
```

**Ý tưởng then chốt**: một `ModifierRune` có thể chứa các Rune con → tạo thành **cây**. Khi đạn bắn ra, hệ thống **duyệt cây đệ quy** và gọi `on_fire`, `on_update`, `on_hit` trên từng node.

> *(Chỉ vào `rune_tree.py`)* "Cả cây được xử lý bằng đệ quy `_traverse_fire`, `_traverse_update`, `_traverse_hit` — giới hạn độ sâu `MAX_DEPTH = 3`."

### Composition over Inheritance — chứng minh sống

"Nhìn class `Bullet`: nó **không hề biết** mình là đạn lửa hay đạn băng. Nó chỉ giữ một tham chiếu `rune_tree` được gắn vào **lúc chạy (runtime)**. Muốn đạn cháy? Gắn Fire Rune. Muốn nó tách đôi? Gắn Split. Cùng một class `Bullet`, hành vi hoàn toàn khác nhau — **quyết định bằng dữ liệu, không bằng kiểu**."

### Open/Closed — thêm phép mới

"Quy tắc dự án: **thêm một Rune mới = thêm MỘT file class mới, KHÔNG sửa** `RuneComponent`, `Bullet`, hay `RuneTree`. Class cha đóng với sửa đổi, mở với mở rộng — đúng chữ O trong SOLID."

> 💡 *Câu chốt*: "Composite Pattern biến 'hàng trăm class phép' thành 'vài chục viên gạch nhỏ + một cái cây'."

---

## 🔮 PHẦN 4 — HỆ THỐNG RUNE CHI TIẾT · ~2.5 phút

### 4 Nguyên tố (Element — leaf node)

| Rune | Hình dạng bắn | Hiệu ứng đặc trưng |
|------|---------------|--------------------|
| 🔥 **Fire** | Fire bolt (vung tay phun lửa) | Gây cháy (burn) theo thời gian |
| ❄️ **Ice** | Sạc rồi thả (charge) | Gai băng bắn xa, làm đóng băng/chậm |
| ⚡ **Lightning** | Tia sét tức thời | Chain lightning + sát thương cộng thêm |
| 🌪️ **Wind** | Boomerang xuyên địch | Làm chậm, đạn bay đi-về |

### Modifier & Trigger (composite node) — vài viên tiêu biểu

**Modifier** (đổi thuộc tính/quỹ đạo đạn):
- **Heavy Hitter**: +damage nhưng −tốc độ đạn
- **Lightened Heart**: +tốc độ, −kích thước
- **Piercing Eyes**: đạn xuyên thêm nhiều địch
- **Frenetic Energy**: bắn thêm nhiều viên toả hình nón (cone)
- **Stars Aligned**: bắn thêm nhiều viên dàn hàng ngang (line)
- **Self-Centered**: đạn quay quanh người chơi như vệ tinh
- **Haste Rune** (passive): giảm hồi chiêu (cooldown)

**Trigger** (chủ động cast ra đòn phụ khi có điều kiện):
- **Furious Outburst**: đạn bay đủ xa → nổ ra cầu lửa ngẫu nhiên (20% dmg)
- **Rolling Stone**: khi cast → lăn một tảng đá xuyên phá 5 giây
- **Flash of Swords**: khi cast → sinh lưỡi kiếm xoay quanh nguồn
- **Perfect Storm**: khi cast → tạo lốc xoáy hút quái vào tâm

### Cơ chế "neo vào Trigger gần nhất" (lấy cảm hứng *Echoes of Mystralia*)

"Đây là phần tinh vi nhất. Mỗi Rune tự hỏi: *'Tôi đang gắn vào cái gì?'* — Trigger gần nhất phía trên, hoặc phép gốc nếu không có. Nhờ vậy, đặt **Heavy Hitter** *dưới* **Furious Outburst** thì buff damage chỉ áp lên **cầu lửa**, không rò rỉ lên đạn chính. Cấu trúc **cha–con** trong cây mới mang ý nghĩa, chứ không phải thứ tự slot."

### Ngân sách điểm (game balance)

"Mỗi chiêu có **`MAX_POINTS = 5` điểm**. Rune mạnh tốn nhiều điểm hơn (`POINT_COST`). Người chơi phải **đánh đổi** — đó là chiều sâu chiến thuật."

---

## 🎯 PHẦN 5 — CÁC HỆ THỐNG GAMEPLAY · ~2 phút

### 3 chiêu độc lập + Rune Builder
- Người chơi có **3 SpellBuild** riêng, mỗi chiêu một cây Rune độc lập.
- Nhấn **Q/E** đổi chiêu ngay trong lúc chơi.
- Nhấn **Tab** mở **Rune Builder**: kéo-thả Rune từ kho (inventory) vào cây phép, xem chỉ số trực tiếp.

### Hệ thống lên cấp kép
- Nhặt **XP orb** (rơi ra khi giết quái, có nam châm tự hút).
- Lên cấp → chọn 1 trong 3 thẻ: **Rune mới** *hoặc* **nâng chỉ số (StatUpgrade)**.
- StatUpgrade có **5 bậc hiếm**: Common / Uncommon / Rare / Epic / Legendary (tỉ lệ 50/28/15/6/1%).

### 8 chỉ số nhân vật
HP · Speed · Damage · Armor · HP Regen · **Lucky** · CDR · XP Range.
> "Điểm hay: **Lucky** ảnh hưởng cùng lúc **3 cơ chế** — tỉ lệ chí mạng, tỉ lệ ra đồ hiếm, và số XP orb rơi ra. Một chỉ số, ba tác động."

### Chiêu cuối (Ultimate) & Lướt (Dash)
- **Ultimate** (chuột phải, hồi 8s): 5 loại theo nguyên tố — Fire Nova, Ice Blizzard, Lightning Storm, Wind Cyclone, Shadow Nova.
- **Dash** (Space, 200px, hồi 3s): thiết kế theo `MovementAbility` base để dễ mở rộng (Blink, Ghost Step...).

### Kẻ địch đa dạng & Wave
- 6 loại: Enemy thường, **RangedEnemy** (bắn xa), **FastEnemy**, **TankEnemy**, DummyEnemy (test), **Boss**.
- Wave sinh quái mỗi 15s; **Boss xuất hiện ở wave 8 hoặc phút thứ 12**.
- Hiệu ứng trạng thái: burn / chill / slow / stun / poison (có cộng dồn stack).

### 🔊 Hệ thống âm thanh (mới bổ sung)
"Chúng tôi vừa thêm module `ui/audio.py` — một `AudioManager` nhẹ, load sẵn SFX, có **throttle chống spam** và **tự tắt an toàn** nếu máy không có thiết bị âm thanh. Hiện có tiếng phép (Fireball, Ice Barrage, Firespray) và **tiếng bước chân theo nhịp** khi di chuyển."

---

## 🧪 PHẦN 6 — CHẤT LƯỢNG & KIỂM THỬ · ~1 phút

- Bộ test `pytest` chạy **độc lập không cần mở game** (nhờ tách `logic/`):
  - Test tổ hợp Rune (combo), test Ultimate, test entities, test Player, test input, test Rune builds.
- **Comment tiếng Việt** xuyên suốt, kèm "👉 BƯỚC TIẾP THEO" dẫn người đọc đi qua luồng code — biến source thành **tài liệu học tập**.
- Kiến trúc "nhiều file nhỏ, mỗi Rune một file" → dễ đọc, dễ mở rộng, dễ review.

---

## 🎥 PHẦN 7 — DEMO TRỰC TIẾP · ~2 phút

> *(Kịch bản demo — làm theo thứ tự này để "kể chuyện" bằng gameplay)*

1. **Bắn cơ bản**: chọn Fire, bắn vài phát → chỉ tiếng lửa + hiệu ứng cháy.
2. **Mở Builder (Tab)**: gắn **Frenetic Energy** → cho xem một phát bắn ra chùm đạn toả nón.
3. **Ghép Trigger**: gắn **Furious Outburst** → đạn bay xa tự nổ cầu lửa. "Đây là Composite đang duyệt cây theo thời gian thực."
4. **Đổi chiêu (Q/E)**: chuyển sang build Băng đã lắp sẵn → cơ chế sạc-thả khác hẳn.
5. **Lên cấp**: giết quái, nhặt XP, cho xem màn chọn thẻ Rune/Stat.
6. **Ultimate (chuột phải)**: tung chiêu cuối theo nguyên tố.
7. *(Nếu còn thời gian)* Đợi/kích Boss để cho thấy đỉnh cao độ khó.

---

## 🏁 PHẦN 8 — KẾT LUẬN · ~1 phút

"Tóm lại, **Rune Craft Roguelike** không chỉ là một trò chơi — nó là **minh chứng sống cho 3 nguyên lý OOP**:

- **Composite Pattern** → cây phép lồng nhau, duyệt đệ quy.
- **Open/Closed** → thêm phép mới chỉ cần thêm file, không sửa lõi.
- **Composition over Inheritance** → một class `Bullet` duy nhất, hành vi quyết định bởi cây Rune runtime.

Kết quả là **chiều sâu gameplay gần như vô hạn** sinh ra từ một **bộ luật gọn gàng**. Đó chính là vẻ đẹp của thiết kế hướng đối tượng đúng cách.

Xin cảm ơn thầy/cô và các bạn đã lắng nghe — chúng em xin nhận câu hỏi."

---

## ❓ PHỤ LỤC — CÂU HỎI THƯỜNG GẶP (chuẩn bị trước)

**Hỏi: Vì sao chọn Composite chứ không phải Strategy/Decorator?**
> Vì Rune cần **lồng nhau nhiều tầng** (Rune con trong Rune cha) và xử lý **đồng nhất** cả node lá lẫn node nhánh qua cùng interface — đúng bài toán Composite. Decorator chỉ bọc tuyến tính một lớp, không diễn tả được cấu trúc cây cha–con.

**Hỏi: Làm sao đảm bảo thêm Rune mới không phá vỡ hệ thống?**
> Mọi Rune kế thừa `RuneComponent` và chỉ override các hook (`on_hit`/`on_fire`/`on_update`). `RuneTree` duyệt qua interface chung nên **không cần biết** class cụ thể — thêm class mới là "cắm vào chạy".

**Hỏi: Tách `logic/` khỏi `ui/` có phức tạp hoá không?**
> Ngược lại — nó giúp **test logic không cần pygame** và giữ mỗi tầng một trách nhiệm. Chi phí ban đầu nhỏ, lợi ích bảo trì lớn.

**Hỏi: Cơ chế "neo vào Trigger" giải quyết vấn đề gì?**
> Nó khiến kết quả phụ thuộc **cấu trúc cây** (cha–con) chứ không phụ thuộc **thứ tự slot**. Nhờ đó buff áp đúng mục tiêu (VD chỉ lên cầu lửa, không lên đạn chính), tổ hợp Rune có logic nhất quán và dự đoán được.
