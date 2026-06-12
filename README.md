# Caro AI Lab

Đồ án Caro/Gomoku bằng Python và Pygame, hỗ trợ luật tổng quát `m,n,k`,
ba thuật toán AI và giao diện trực quan phục vụ báo cáo môn Trí tuệ nhân tạo.

## Kiến trúc

Project tách thành bốn lớp chính:

- `game`: mô hình bàn cờ, luật thắng và trạng thái/lịch sử; không phụ thuộc UI.
- `ai`: Greedy, Minimax và Alpha-Beta dùng chung heuristic, root-search helper và metrics.
- `ui`: component Pygame, menu, settings, move-history bar và các màn hình.
- `experiments`: chạy AI vs AI trên terminal để so sánh thời gian, node và win rate.

`main.py` chỉ điều phối vòng lặp Pygame và chuyển màn hình. Cấu hình được kiểm
tra bởi `GameSettings` và lưu trong `utils/settings.json`.

## Kế hoạch triển khai

1. Xây dựng `Board`, luật thắng bốn hướng và `GameState` độc lập với Pygame.
2. Tạo heuristic chung và chuẩn hóa API trả về nước đi kèm `SearchMetrics`.
3. Cài Greedy một lớp, Minimax giới hạn độ sâu và Alpha-Beta có cắt tỉa.
4. Xây component UI, menu, settings, game screen và bộ xem lại lịch sử.
5. Ghép các màn hình trong vòng lặp `App`, sau đó lưu/đọc cấu hình JSON.
6. Tạo chương trình AI vs AI và đánh giá luật, chiến thuật, render headless.

Thứ tự này cho phép đánh giá thuật toán không cần mở giao diện, đồng thời giữ
phần trình bày và phần logic tách biệt rõ ràng trong báo cáo.

## Cấu trúc thư mục

```text
.
├── main.py
├── requirements.txt
├── README.md
├── config/
│   └── settings.py
├── game/
│   ├── board.py
│   ├── history_store.py
│   ├── match_history.py
│   ├── metrics.py
│   ├── rules.py
│   └── state.py
├── ai/
│   ├── __init__.py
│   ├── base.py
│   ├── greedy.py
│   ├── minimax.py
│   ├── alphabeta.py
│   └── search_helpers.py
├── ui/
│   ├── board_view.py
│   ├── components.py
│   ├── game_screen.py
│   ├── history_screen.py
│   ├── menu.py
│   ├── metrics_panel.py
│   ├── move_history_bar.py
│   ├── replay_screen.py
│   └── settings_screen.py
├── experiments/
│   └── evaluate.py
└── utils/
    ├── helpers.py
    ├── seedmaker.py
    ├── match_history.json
    └── settings.json
```

## Vai trò các file chính

| File | Trách nhiệm |
|---|---|
| `main.py` | Khởi tạo Pygame, vòng lặp chính và chuyển màn hình |
| `config/settings.py` | Hằng số UI, dataclass cấu hình và lưu JSON |
| `game/board.py` | Ma trận bàn cờ, đặt/xóa quân, sinh nước ứng viên |
| `game/history_store.py` | Đọc/ghi lịch sử trận đấu JSON theo schema có kiểm tra |
| `game/match_history.py` | Bản ghi metric theo nước và tổng kết trận |
| `game/metrics.py` | Cộng dồn search metrics và khởi tạo session stats |
| `game/rules.py` | Kiểm tra chuỗi thắng ngang, dọc và hai đường chéo |
| `game/state.py` | Lượt chơi, kết quả, lịch sử và dựng bàn cờ xem lại |
| `ai/greedy.py` | Tìm kiếm tham lam một lớp |
| `ai/minimax.py` | Minimax giới hạn độ sâu |
| `ai/alphabeta.py` | Minimax có cắt tỉa Alpha-Beta |
| `ai/search_helpers.py` | Root tracker và terminal evaluation dùng chung cho AI |
| `ui/components.py` | Button, selector, stepper, font, panel và cache gradient |
| `ui/board_view.py` | Hình học, ánh xạ click và render bàn cờ động |
| `ui/metrics_panel.py` | Dựng view-model và hiển thị metrics theo lượt/trận |
| `ui/move_history_bar.py` | Điều hướng review và toggle phân tích dùng chung |
| `ui/menu.py` | Menu trước trận đấu |
| `ui/history_screen.py` | Phân trang lịch sử các ván đã lưu và chọn trận replay |
| `ui/replay_screen.py` | Dựng lại bàn cờ và metrics của từng nước trong trận cũ |
| `ui/settings_screen.py` | Cấu hình m,n,k, mode, AI và depth |
| `ui/game_screen.py` | Điều phối trận đấu, AI, input và move history |
| `experiments/evaluate.py` | Benchmark AI vs AI trên terminal |
| `utils/helpers.py` | Heuristic, sắp xếp nước và metrics dùng chung |
| `utils/seedmaker.py` | Sinh global seed và tách seed cho opening/X/O |

## Cài đặt và chạy game

Yêu cầu Python 3.10 trở lên.

```bash
python -m pip install -r requirements.txt
python main.py
```

Trong màn hình Settings:

- `m`: số hàng, từ 3 đến 20.
- `n`: số cột, từ 3 đến 24.
- `k`: số quân liên tiếp để thắng, từ 3 đến 8.
- Chế độ: Người vs Người, Người vs AI hoặc AI vs AI.
- Có thể chọn riêng thuật toán cho X và O trong chế độ AI vs AI.
- Độ sâu Minimax và Alpha-Beta được cấu hình riêng, mỗi thuật toán từ 1 đến 4.

Trong Người vs AI, người chơi cầm X và đi trước. Hai nút mũi tên ở vùng
`MOVE HISTORY` cho phép lùi/tiến qua các nước đã thực hiện. Khi đang ở chế độ
`REVIEW`, trận đấu tạm dừng cho đến khi trở lại nước mới nhất (`LIVE`).

Nút `PHÂN TÍCH AI` bật heatmap các nước ứng viên của lượt AI đang xem. Màu xanh
là thứ hạng cao, màu đỏ là thứ hạng thấp và viền cam đánh dấu nước được chọn.
Rê chuột lên một ô để xem tọa độ, điểm, thứ hạng, trạng thái thắng ngay và số
nhánh bị cắt trong cây con. Ở `LIVE`, heatmap dùng lượt AI gần nhất; ở `REVIEW`,
nó dùng đúng snapshot của nước đang chọn. Tùy chọn này chỉ tồn tại trong phiên
chạy và không được lưu vào `settings.json`.

Mỗi ván kết thúc được tự động lưu vào `utils/match_history.json`. Bản ghi gồm
cấu hình `m,n,k`, seed, kết quả, toàn bộ nước đi, metrics và dữ liệu heatmap của
từng lượt AI. Mở `LỊCH SỬ` từ menu hoặc màn hình game, chọn `XEM LẠI`, rồi dùng
hai nút mũi tên để dựng lại trạng thái bàn cờ từng bước. File lịch sử là dữ liệu
local và được loại khỏi Git; nếu file hỏng hoặc sai schema, game bỏ qua dữ liệu
không hợp lệ thay vì làm gián đoạn quá trình khởi động.

## Thuật toán

### Greedy Search

Xét từng nước ứng viên, đánh giá bàn cờ sau đúng một lượt và chọn điểm cao
nhất. Thuật toán nhanh nhưng không dự đoán được phản ứng nhiều bước của đối thủ.
Trước khi dùng heuristic, AI luôn ưu tiên nước thắng ngay hoặc nước bắt buộc
phải chặn để không bỏ sót chiến thuật một lượt.
Greedy luôn có depth hiệu dụng bằng 1; Minimax và Alpha-Beta có depth riêng
trong Settings. Heatmap của Greedy hiển thị trực tiếp `Heuristic`, tức điểm bàn
cờ sau khi thử từng nước ứng viên.

### Minimax giới hạn độ sâu

Luân phiên tầng MAX/MIN đến độ sâu cấu hình. Giá trị lá lấy từ các mẫu chuỗi
theo mục tiêu `k`. Số nhánh được giới hạn theo độ sâu để kiểm soát thời gian.
Heatmap hiển thị `Minimax Value`, tức utility được truyền ngược từ cây tìm kiếm
cho từng nước ở tầng gốc, không phải heuristic một bước sau khi đặt quân.

### Alpha-Beta Pruning

Dùng đúng cùng cây, thứ tự nước đi và heuristic với Minimax, nhưng loại các
nhánh không thể làm thay đổi quyết định bằng hai biên `alpha` và `beta`. Vì vậy,
ở cùng độ sâu hai thuật toán phải chọn cùng nước đi; Alpha-Beta thường mở ít node
hơn. Heatmap hiển thị `Alpha-Beta Value`; một số giá trị có thể là biên do nhánh
đã bị cắt, nhưng vẫn là giá trị thực tế thuật toán dùng để quyết định. Panel
metrics hiển thị thêm số nhánh đã cắt khi có.

Các AI chỉ xét ô trống trong bán kính hai ô quanh quân đã đánh. Đây là kỹ thuật
giảm không gian trạng thái phổ biến cho Gomoku, không làm thay đổi luật chơi.
Hàm heuristic phân biệt chuỗi mở hai đầu, mở một đầu và bị chặn hoàn toàn theo
khoảng cách đến độ dài thắng `k`, đúng với mô hình trình bày trong báo cáo.

Tìm kiếm AI chạy trên một thread nền với bản sao bàn cờ. Depth cao vẫn cần nhiều
thời gian do độ phức tạp lũy thừa, nhưng cửa sổ Pygame tiếp tục vẽ và nhận sự kiện
thay vì đứng hình.

Trong game, các nước có cùng mức ưu tiên được xáo trộn bằng bộ sinh ngẫu nhiên
của từng AI. Vì vậy restart có thể tạo diễn biến khác nhưng AI không chọn nước có
điểm thấp hơn chỉ để tạo ngẫu nhiên. Mỗi ván sinh một global seed mới từ entropy
hệ điều hành, sau đó dẫn xuất seed riêng cho X và O.

## Chạy thí nghiệm AI

Chạy toàn bộ cặp thuật toán trên bàn 10x10, thắng 5:

```bash
python experiments/evaluate.py --games 4 \
  --minimax-depth 2 --alphabeta-depth 2 --opening-moves 2
```

Chỉ so sánh Minimax với Alpha-Beta:

```bash
python experiments/evaluate.py --rows 12 --cols 12 --win 5 \
  --minimax-depth 3 --alphabeta-depth 3 \
  --games 3 --algorithms minimax alphabeta
```

Trên PowerShell có thể viết cùng lệnh trên một dòng. Kết quả gồm:

- số trận X thắng, O thắng và hòa của từng cặp;
- thời gian trung bình trên mỗi nước;
- số node trung bình trên mỗi nước;
- W-D-L, win rate và score rate tổng hợp theo thuật toán.

Để báo cáo công bằng, nên chạy nhiều trận với cùng kích thước, `k`, depth của
từng thuật toán và cấu hình máy; sau đó ghi rõ giới hạn nhánh ứng viên trong
phần phương pháp.
Mỗi lần chạy experiments sinh một global seed mới và in seed đó trong kết quả.
Từ global seed, chương trình tạo nhiều game seed khác nhau nên các trận không lặp
một kịch bản. Cùng game index vẫn dùng chung opening giữa các matchup để phép so
sánh công bằng. Kết quả còn in game seed và opening của từng case để kiểm chứng.
Phần tổng hợp loại self-play vì trận một thuật toán đấu chính nó luôn kéo tỷ lệ
về mức trung tính.
