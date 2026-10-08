# Kế hoạch: Game nấu ăn stream YouTube 24/7

Ngày lập: 07/10/2026

## 1. Mục tiêu

Một game 2D nhẹ chạy 24/7 trên VPS Oracle OCI (Always Free, tối đa 2 OCPU / 12 GB RAM), stream lên YouTube, người xem comment để điều khiển game.

## 2. Thiết kế game

**Ý tưởng:** game nấu ăn. Một đầu bếp nấu lần lượt các món do người xem đặt.

**Ba lệnh chính:**

- `!nau [tên món]`: thêm một món vào hàng đợi. Mỗi người chỉ có 1 món đang chờ. Không ghi tên món thì game chọn ngẫu nhiên.
- `!khen`: khen món vừa nấu xong. Mỗi người khen tối đa 1 lần cho mỗi món.
- `!donate`: nhận thưởng. MVP dùng điểm/xu trong game; về sau gắn donate tiền thật (xem mục 5).

**Vòng lặp game:**

1. Người xem gõ `!nau` → món vào hàng đợi.
2. Đầu bếp nấu từng món (10–20 giây, có thanh tiến độ).
3. Món xong hiện tên món và tên người đặt.
4. Người xem `!khen` → tăng độ hài lòng của quán.
5. Độ hài lòng và thưởng mở khóa món mới, trang trí quán.

**Lý do chọn kiểu game này:** từ lúc người xem comment đến lúc thấy kết quả trên stream mất vài giây, nên game cần chịu được độ trễ. Game nấu ăn theo hàng đợi phù hợp vì không đòi phản xạ nhanh.

**Gợi ý để stream hấp dẫn:**

- Hiện tên người đặt trên món.
- Món được khen nhiều thì "hiếm" hoặc đẹp hơn.
- Bảng xếp hạng người đặt/khen nhiều nhất trong ngày.
- Khi hàng đợi trống, đầu bếp tự nấu món ngẫu nhiên để stream không đứng hình.

## 3. Định dạng stream

- Stream **dọc 9:16** để có cơ hội xuất hiện trong Shorts feed trên điện thoại (không đảm bảo lượt xem; máy tính bảng không hiển thị).
- Canvas đề xuất: **720×1280, 30 fps**, H.264, khoảng 4 Mbps, audio AAC 128 kbps. Số điểm ảnh xấp xỉ 720p ngang nên CPU không tăng.
- Chỉ làm **một luồng dọc**, không phát song song ngang + dọc vì phải mã hóa hai luồng, quá nặng cho 2 core ARM.
- Link trong vertical live feed có thể không bấm được, nên **QR/hướng dẫn donate phải vẽ ngay trong game**.
- Bố cục gợi ý: bếp và đầu bếp ở trên, hàng đợi món và bảng xếp hạng ở dưới, chừa lề trên và dưới vì giao diện YouTube phủ lên.
- Bot chat không đổi: luồng ngang và dọc dùng chung live chat.

## 4. Kiến trúc

```text
YouTube Live Chat → Chat Bot (Python) → Command Queue → Game Logic → Game 2D (Pygame)
                                                                          ↓
                                                               Xvfb → FFmpeg → RTMPS → YouTube
```

- Chat Bot và Game Logic tách nhau. Chat chỉ gửi lệnh (`nau`, `khen`, `donate`), game quyết định xử lý.
- Mọi nguồn đầu vào (bàn phím, YouTube chat, sự kiện donate) đều đẩy vào cùng một command queue.
- Game xử lý queue theo tick, có cooldown và giới hạn tốc độ mỗi người.
- Chạy bằng 3 service systemd (`game`, `chatbot`, `stream`) với `Restart=always`.

## 5. Donate tiền thật (làm sau MVP)

- Cách đơn giản nhất: dùng dịch vụ donate cho streamer (Streamlabs, StreamElements, Ko-fi, Buy Me a Coffee), nhận tiền về PayPal. Script trên VPS nghe sự kiện donate rồi đẩy vào queue của game.
- Lựa chọn khác: Super Chat (cần kênh đủ điều kiện kiếm tiền), hoặc chuyển khoản/QR ngân hàng qua dịch vụ có webhook (ví dụ SePay, Casso).
- Cần làm kỹ: xác thực sự kiện (token/secret), chống trùng mã giao dịch, lọc tên và lời nhắn trước khi hiện lên stream.
- Cần kiểm tra: phí PayPal và phí từng dịch vụ (rút về ngân hàng Việt Nam có phí giao dịch, chênh lệch tỷ giá và phí mỗi lần rút), dịch vụ có hỗ trợ Việt Nam không, chính sách YouTube về donate ngoài nền tảng, nghĩa vụ thuế.
- Tránh để phần thưởng giống cờ bạc (ví dụ donate để quay trúng món hiếm).

## 6. Bảng kế hoạch thực thi

| # | Giai đoạn | Việc cần làm | Xong khi | Ước tính |
| --- | --- | --- | --- | --- |
| 0 | Chốt thiết kế | Liệt kê 10–15 món và thời gian nấu. Chốt luật `!nau`, `!khen`, `!donate`. | Có 1 trang ghi rõ luật và vòng lặp game | 1 ngày |
| 1 | Game chạy local | Pygame canvas 720×1280: đầu bếp, hàng đợi món, thanh tiến độ, tên người đặt, thanh hài lòng. Điều khiển tạm bằng bàn phím. `!donate` bằng điểm trong game. | Chơi được cả vòng: đặt món → nấu → khen → thưởng | 4–6 ngày |
| 2 | Lớp lệnh | `handle_command()`, command queue, cooldown, mỗi người 1 món chờ, mỗi món khen 1 lần, giới hạn tốc độ. | Lệnh giả chạy đúng, spam không làm hỏng game | 1–2 ngày |
| 3 | Kết nối YouTube Chat | Project Google, OAuth, lấy `liveChatId`, đọc chat bằng `streamList` hoặc polling, parse `!nau`, `!khen`. Test bằng stream không công khai. | Comment trên YouTube làm đầu bếp nấu món | 2–3 ngày |
| 4 | Stream thử từ máy local | FFmpeg đẩy 720×1280 30 fps lên YouTube, theo dõi CPU. Nặng thì hạ độ phân giải hoặc fps. Kiểm tra luồng dọc hiện đúng trên điện thoại. | Xem được stream trên YouTube, hình ổn định | 1–2 ngày |
| 5 | Đưa lên Oracle OCI | Tạo VM A1 (tối đa 2 OCPU / 12 GB), cài môi trường, chạy game + FFmpeg qua Xvfb, đo CPU/RAM. | Stream thử chạy từ VPS ít nhất vài giờ | 2–4 ngày |
| 6 | Chạy 24/7 | 3 service systemd (`Restart=always`), log, watchdog đơn giản, stream key cố định, bật auto-start/auto-stop. | Chạy liên tục 48 giờ không cần can thiệp | 2–3 ngày |
| 7 | Donate tiền thật (tùy chọn) | Chọn dịch vụ donate, viết script nhận sự kiện, xác thực, chống trùng, lọc tên. Vẽ QR/hướng dẫn donate trong game. | Donate thử hiện đúng tên và kích hoạt thưởng | 2–3 ngày |
| 8 | Mở public và vận hành | Overlay, bảng xếp hạng, món mới theo mốc, theo dõi log hằng ngày. | Có người thật chơi, stream không sập trong 1 tuần | liên tục |

Tổng thời gian giai đoạn 0–6 khoảng 2,5–4 tuần nếu làm bán thời gian. Đây là ước tính, cần điều chỉnh theo quỹ thời gian thực tế.

## 7. Rủi ro và việc cần kiểm tra

- **Oracle hết capacity:** tạo VM A1 có thể báo hết capacity ở nhiều region. Thử tạo sớm, ngay trong lúc làm game.
- **Bị thu hồi instance:** instance Always Free có thể bị thu hồi nếu mức dùng quá thấp (với A1 có điều kiện về RAM). Game nhẹ + FFmpeg có thể chỉ dùng 1–2 GB trên 12 GB, cần theo dõi.
- **CPU không đủ:** x264 720×1280 30 fps trên 2 core ARM cần đo thật ở giai đoạn 4–5. Nếu thiếu, hạ độ phân giải hoặc fps trước.
- **Băng thông:** khoảng 4 Mbps chạy 24/7 vào khoảng 1,3 TB/tháng, thấp hơn hạn mức 10 TB outbound của OCI.
- **YouTube 24/7:** dùng stream key cố định, bật auto-start/auto-stop; kiểm tra giới hạn lưu bản ghi với live quá 12 giờ và quota API đọc chat.
- **Bảo mật:** token OAuth và secret của dịch vụ donate lưu an toàn trên VPS, không đưa lên GitHub.
- **Điều kiện live dọc:** kiểm tra trong YouTube Studio điều kiện đăng live dọc cho kênh trước khi mở public.

## 8. Việc còn cần quyết định

- [ ] `!donate` là điểm trong game hay tiền thật? (MVP đề xuất: điểm trong game)
- [ ] Khán giả chính là người Việt hay quốc tế? (quyết định chọn PayPal hay QR ngân hàng)
- [ ] Chọn dịch vụ donate (Streamlabs, StreamElements, Ko-fi...).
- [ ] Danh sách 10–15 món ăn đầu tiên và thời gian nấu.
- [ ] Phong cách hình ảnh của game (đầu bếp, quán, màu sắc).

## 9. Cấu trúc thư mục đề xuất

```text
interactive-stream/
├── game/        (main.py, game_state.py, renderer.py, commands.py)
├── youtube/     (chat.py, auth.py, parser.py)
├── donate/      (listener.py)
├── stream/      (start_stream.sh, watchdog.sh)
├── config/      (config.json)
├── systemd/     (game.service, chatbot.service, stream.service)
└── logs/
```
