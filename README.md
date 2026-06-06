# Caro AI Lab

Đồ án Caro/Gomoku bằng Python và Pygame, hỗ trợ luật tổng quát `m,n,k`,
ba thuật toán AI và giao diện trực quan phục vụ báo cáo môn Trí tuệ nhân tạo.

## Kiến trúc

Project tách thành bốn lớp chính:

- `game`: mô hình bàn cờ, luật thắng và trạng thái/lịch sử; không phụ thuộc UI.
- `ai`: Greedy, Minimax và Alpha-Beta dùng chung heuristic và metrics.
- `ui`: component Pygame, menu, settings và màn hình thi đấu.
- `experiments`: chạy AI vs AI trên terminal để so sánh thời gian, node và win rate.

`main.py` chỉ điều phối vòng lặp Pygame và chuyển màn hình. Cấu hình được kiểm
tra bởi `GameSettings` và lưu trong `utils/settings.json`.

## Kế hoạch triển khai

1. Xây dựng `Board`, luật thắng bốn hướng và `GameState` độc lập với Pygame.
2. Tạo heuristic chung và chuẩn hóa API trả về nước đi kèm `SearchMetrics`.
3. Cài Greedy một lớp, Minimax giới hạn độ sâu và Alpha-Beta có cắt tỉa.
4. Xây component UI, menu, settings, game screen và bộ xem lại lịch sử.
5. Ghép các màn hình trong vòng lặp `App`, sau đó lưu/đọc cấu hình JSON.
6. Tạo chương trình AI vs AI và kiểm thử luật, chiến thuật, render headless.

Thứ tự này cho phép kiểm thử thuật toán không cần mở giao diện, đồng thời giữ
phần trình bày và phần logic tách biệt rõ ràng trong báo cáo.

## Cấu trúc thư mục

```text
.
├── main.py
├── requirements.txt
├── README.md
├── config/
│   ├── __init__.py
│   └── settings.py
├── game/
│   ├── __init__.py
│   ├── board.py
│   ├── rules.py
│   └── state.py
├── ai/
│   ├── __init__.py
│   ├── base.py
│   ├── greedy.py
│   ├── minimax.py
│   └── alphabeta.py
├── ui/
│   ├── __init__.py
│   ├── components.py
│   ├── menu.py
│   ├── settings_screen.py
│   └── game_screen.py
├── experiments/
│   ├── __init__.py
│   └── evaluate.py
└── utils/
    ├── __init__.py
    ├── helpers.py
    └── settings.json
```

## Vai trò các file chính

| File | Trách nhiệm |
|---|---|
| `main.py` | Khởi tạo Pygame, vòng lặp chính và chuyển màn hình |
| `config/settings.py` | Hằng số UI, dataclass cấu hình và lưu JSON |
| `game/board.py` | Ma trận bàn cờ, đặt/xóa quân, sinh nước ứng viên |
| `game/rules.py` | Kiểm tra chuỗi thắng ngang, dọc và hai đường chéo |
| `game/state.py` | Lượt chơi, kết quả, lịch sử và dựng bàn cờ xem lại |
| `ai/greedy.py` | Tìm kiếm tham lam một lớp |
| `ai/minimax.py` | Minimax giới hạn độ sâu |
| `ai/alphabeta.py` | Minimax có cắt tỉa Alpha-Beta |
| `ui/components.py` | Button, selector, stepper, font và panel |
| `ui/menu.py` | Menu trước trận đấu |
| `ui/settings_screen.py` | Cấu hình m,n,k, mode, AI và depth |
| `ui/game_screen.py` | Bàn cờ, metrics, lịch sử và điều phối lượt AI |
| `experiments/evaluate.py` | Benchmark AI vs AI trên terminal |
| `utils/helpers.py` | Heuristic, sắp xếp nước và metrics dùng chung |

## Cài đặt và chạy game

Yêu cầu Python 3.10 trở lên.

```bash
python -m pip install -r requirements.txt
python main.py
```

Trong màn hình Settings:

- `m`: số hàng, từ 5 đến 20.
- `n`: số cột, từ 5 đến 24.
- `k`: số quân liên tiếp để thắng, từ 3 đến 8.
- Chế độ: Người vs Người, Người vs AI hoặc AI vs AI.
- Có thể chọn riêng thuật toán cho X và O trong chế độ AI vs AI.
- Độ sâu Minimax/Alpha-Beta từ 1 đến 4.

Trong Người vs AI, người chơi cầm X và đi trước. Hai nút mũi tên ở vùng
`MOVE HISTORY` cho phép lùi/tiến qua các nước đã thực hiện. Khi đang ở chế độ
`REVIEW`, trận đấu tạm dừng cho đến khi trở lại nước mới nhất (`LIVE`).

## Thuật toán

### Greedy Search

Xét từng nước ứng viên, đánh giá bàn cờ sau đúng một lượt và chọn điểm cao
nhất. Thuật toán nhanh nhưng không dự đoán được phản ứng nhiều bước của đối thủ.

### Minimax giới hạn độ sâu

Luân phiên tầng MAX/MIN đến độ sâu cấu hình. Giá trị lá lấy từ các cửa sổ dài
`k`. Số nhánh được giới hạn theo độ sâu để bảo đảm giao diện vẫn phản hồi.

### Alpha-Beta Pruning

Dùng cùng cây và heuristic với Minimax, nhưng loại các nhánh không thể làm thay
đổi quyết định bằng hai biên `alpha` và `beta`. Panel metrics hiển thị thêm số
nhánh đã cắt khi có.

Các AI chỉ xét ô trống trong bán kính hai ô quanh quân đã đánh. Đây là kỹ thuật
giảm không gian trạng thái phổ biến cho Gomoku, không làm thay đổi luật chơi.

## Chạy thí nghiệm AI

Chạy toàn bộ cặp thuật toán trên bàn 10x10, thắng 5:

```bash
python experiments/evaluate.py --games 2 --depth 2
```

Chỉ so sánh Minimax với Alpha-Beta:

```bash
python experiments/evaluate.py --rows 12 --cols 12 --win 5 --depth 3 \
  --games 3 --algorithms minimax alphabeta
```

Trên PowerShell có thể viết cùng lệnh trên một dòng. Kết quả gồm:

- số trận X thắng, O thắng và hòa của từng cặp;
- thời gian trung bình trên mỗi nước;
- số node trung bình trên mỗi nước;
- win rate tổng hợp theo thuật toán.

Để báo cáo công bằng, nên chạy nhiều trận với cùng kích thước, `k`, độ sâu và
cấu hình máy; sau đó ghi rõ giới hạn nhánh ứng viên trong phần phương pháp.
