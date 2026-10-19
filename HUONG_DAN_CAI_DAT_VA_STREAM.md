# 🍜 HƯỚNG DẪN CÀI ĐẶT & LIVESTREAM COZY MIDNIGHT DINER 24/7
> **Game Nấu Ăn Tương Tác Dọc (9:16) Phát Trực Tiếp YouTube Live 24/7**  
> Dành cho máy tính cá nhân (Windows/macOS) và máy chủ đám mây (Linux VPS).

---

## 📌 MỤC LỤC
1. [Giới thiệu tổng quan kiến trúc](#1-giới-thiệu-tổng-quan-kiến-trúc)
2. [Cài đặt môi trường từ đầu (Trắng máy)](#2-cài-đặt-môi-trường-từ-đầu-trắng-máy)
3. [Chạy thử nghiệm & Điều khiển phím tắt Local](#3-chạy-thử-nghiệm--điều-khiển-phím-tắt-local)
4. [Sử dụng Bàn điều khiển Studio Controller (Desktop GUI)](#4-sử-dụng-bàn-điều-khiển-studio-controller-desktop-gui)
5. [Kết nối YouTube Live Chat & Cổng Donate](#5-kết-nối-youtube-live-chat--cổng-donate)
6. [Hướng dẫn Phát Sóng Livestream lên YouTube](#6-hướng-dẫn-phát-sóng-livestream-lên-youtube)
   - [Cách 1: Sử dụng OBS Studio (Khuyên dùng trên Windows)](#cách-1-sử-dụng-obs-studio-khuyên-dùng-trên-windows)
   - [Cách 2: Sử dụng FFmpeg chạy ngầm](#cách-2-sử-dụng-ffmpeg-chạy-ngầm)
   - [Cách 3: Chạy 24/7 trên VPS Linux (Oracle Cloud / Ubuntu)](#cách-3-chạy-247-trên-vps-linux-oracle-cloud--ubuntu)
7. [Các mẹo vận hành Stream 24/7 không gián đoạn](#7-các-mẹo-vận-hành-stream-247-không-gián-đoạn)

---

## 1. Giới thiệu tổng quan kiến trúc

**Cozy Midnight Diner** là dự án game giả lập quán ăn đêm lofi được thiết kế chuyên biệt cho luồng livestream tương tác 24/7:
- **Định dạng hiển thị:** Khung dọc chuẩn **9:16 (720x1280)** tối ưu cho **YouTube Shorts / Mobile Live Feed**.
- **Cơ chế tương tác:** Người xem gõ lệnh trong khung chat YouTube (`!cook ramen`, `!yum`, `!tip 100`, `!menu`) → Đầu bếp mèo trong game sẽ nhận đơn và nấu trực tiếp trên màn hình.
- **Hệ thống âm thanh:** Nhạc nền Lofi thư giãn + Âm thanh chiên xào (sizzle), chuông reo (bell ding), tiền xu (coin chime).
- **Hệ thống tự động hóa:** Tích hợp sẵn bot **Viewer Simulator** tự động trò chuyện và đặt món khi vắng khách để luồng stream luôn sinh động.

```text
[Khán giả YouTube Chat] ---> [YouTube Chat Poller API] ---\
[Người ủng hộ Donate]    ---> [Universal Webhook :8088]    ---> [Command Queue] ---> [Game Pygame 720x1280]
[Streamer Điều khiển]    ---> [Studio Controller GUI]  ---/                                 |
                                                                                    | (Bắt hình & tiếng)
                                                                                    v
                                                                       [OBS Studio HOẶC FFmpeg]
                                                                                    |
                                                                                    v
                                                                        [YouTube RTMPS Live 24/7]
```

---

## 2. Cài đặt môi trường từ đầu (Trắng máy)

### Bước 2.1: Cài đặt Python
1. Tải và cài đặt **Python 3.10 trở lên** (Khuyên dùng Python 3.11 hoặc 3.12) từ trang chủ [python.org](https://www.python.org/downloads/).
2. **Lưu ý quan trọng trên Windows:** Khi cài đặt, hãy tích chọn ô **`Add Python to PATH`**.

### Bước 2.2: Mở Terminal tại thư mục dự án
Mở PowerShell (Windows) hoặc Terminal (Linux/macOS) và trỏ đến thư mục `catcook`:
```bash
cd "c:\Users\dat\Downloads\catcook"
```

### Bước 2.3: Tạo môi trường ảo (Khuyên dùng)
```bash
# Tạo môi trường ảo venv
python -m venv .venv

# Kích hoạt môi trường ảo:
# Trên Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# (Hoặc nếu dùng Command Prompt CMD):
# .\.venv\Scripts\activate.bat
# Trên Linux/macOS:
# source .venv/bin/activate
```

### Bước 2.4: Cài đặt các thư viện cần thiết
Dự án đã có sẵn file `requirements.txt`:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Các thư viện chính được cài đặt bao gồm:
- `pygame-ce`: Engine đồ họa 2D & âm thanh tối ưu hiệu năng.
- `requests`: Gọi YouTube Data API v3 đọc chat.
- `Pillow` & `numpy`: Xử lý đồ họa sprite và hiệu ứng hạt.

Kiểm tra cài đặt hoàn tất bằng cách chạy test tự động:
```bash
python -m unittest discover tests
```
*(Nếu hiển thị `Ran 9 tests ... OK` là môi trường đã chuẩn 100%).*

---

## 3. Chạy thử nghiệm & Điều khiển phím tắt Local

### Khởi chạy game
Chạy lệnh:
```bash
python main.py
```
Cửa sổ game **Cozy Midnight Diner** sẽ xuất hiện với âm nhạc Lofi và khung cảnh quán ăn đêm ấm cúng.

### Bảng phím tắt điều khiển nhanh trên bàn phím:
| Phím | Chức năng | Mô tả chi tiết |
| :---: | :--- | :--- |
| **`1` - `9`, `0`** | Đặt món nhanh | Gọi trực tiếp 10 món ăn nổi bật (Ramen, Pizza, Tacos, Boba, Parfait, Curry...) |
| **`SPACE`** hoặc **`Y`** | Cổ vũ `!yum` | Thả tim bay lơ lửng + hiệu ứng âm thanh pop |
| **`T`** | Gửi tiền tip `!tip 100` | Nổ pháo hoa hạt vàng + tiếng leng keng chuông tiền xu |
| **`M`** | Xem menu `!menu` | Hiển thị toàn bộ danh sách 16 món ăn lên khung chat |
| **`C`** | Gõ lệnh chat tự do | Mở khung gõ phím góc dưới để streamer nhập thử bất kỳ lệnh nào (vd: `!cook waffles`) |
| **`V`** | Bật / Tắt Chat Sim | Kích hoạt hoặc tạm dừng bot giả lập người xem |
| **`O`** | Mở Studio Controller | Bật ngay cửa sổ bàn điều khiển độc lập |
| **`ESC`** | Thoát game | Đóng ứng dụng an toàn |

---

## 4. Sử dụng Bàn điều khiển Studio Controller (Desktop GUI)

Để streamer có thể quản lý luồng stream trực quan mà không cần nhớ phím tắt hay sửa code, dự án tích hợp sẵn **Studio Controller** (Giao diện Dark Theme hiện đại viết bằng Tkinter).

### Cách khởi động:
- **Cách 1:** Nhấn phím **`O`** ngay trong cửa sổ game.
- **Cách 2:** Chạy game kèm cờ Studio: `python main.py --studio`
- **Cách 3:** Mở riêng bàn điều khiển độc lập: `python studio_controller.py`

### 4 Tab chức năng chính của Studio Controller:
1. **🎵 Âm thanh & Nhạc:**
   - Điều chỉnh thanh trượt âm lượng nhạc nền (BGM) và hiệu ứng âm thanh (SFX).
   - Nút bật/tắt âm thanh xèo xèo chiên xào (Cooking Sizzle Loop).
   - Nút chuyển bài nhạc Lofi tiếp theo.
2. **🍳 Bếp & Gameplay:**
   - Xem trực tiếp số lượng món đang xếp hàng (Queue).
   - Bảng 16 nút bấm tương ứng với 16 món ăn để thêm đơn nấu ngay lập tức.
   - Nút **Bỏ qua món hiện tại (Skip)** hoặc **Xóa toàn bộ hàng đợi (Reset Queue)** khi cần.
   - Nút kích hoạt đầu bếp tự nấu (Idle Cook Trigger).
3. **💬 Sự kiện & Chat Sim:**
   - Bật/tắt Viewer Simulator và điều chỉnh thời gian ngẫu nhiên giữa các lần bot chat (12s - 28s).
   - Nút kích hoạt giả lập bão tim (`!yum`), tặng tiền tip (`!tip 500`), hoặc yêu cầu menu.
4. **📡 Cài đặt Stream:**
   - Nhập **YouTube API Key** và **Video ID / URL** của buổi phát trực tiếp.
   - Nút bấm **"Lưu & Tự động dò tìm Live Chat ID"**.
   - Cổng Webhook nhận Donate quốc tế (`8088`) kèm nút gửi thử nghiệm thông báo donate.

---

## 5. Kết nối YouTube Live Chat & Cổng Donate

### 5.1. Kết nối YouTube Live Chat thật (Khán giả gõ lệnh)

1. **Lấy YouTube Data API v3 Key (Miễn phí):**
   - Truy cập [Google Cloud Console](https://console.cloud.google.com/).
   - Tạo một dự án mới (ví dụ: `CatCook-Stream`).
   - Vào mục **APIs & Services** → **Library** → Tìm kiếm **"YouTube Data API v3"** và bấm **Enable**.
   - Vào mục **Credentials** → Chọn **Create Credentials** → **API key**. Sao chép mã API key nhận được.

2. **Cấu hình vào game:**
   - Mở file [`config/config.json`](file:///c:/Users/dat/Downloads/catcook/config/config.json) hoặc điền trực tiếp trong Tab 4 của **Studio Controller**:
     ```json
     "youtube": {
       "api_key": "AIzaSyYourGoogleApiKeyHere...",
       "video_id": "dQw4w9WgXcQ",
       "enabled": true,
       "polling_interval": 4.0
     }
     ```
   - Trong đó `video_id` là mã định danh buổi live trên link YouTube (Ví dụ link là `https://www.youtube.com/watch?v=AbCdEfGh` thì `video_id` là `AbCdEfGh`).
   - Bấm **"Lưu & Kết nối"** trên Studio Controller. Hệ thống sẽ tự động tìm `live_chat_id` và bắt đầu đọc comment trực tiếp sau mỗi 4 giây!

### 5.2. Kết nối Cổng Donate Webhook (Tùy chọn)

Game tích hợp sẵn máy chủ HTTP lắng nghe webhook tại cổng `8088` (URL: `http://localhost:8088/webhook/donate`).
- Tương thích với các payload JSON từ **Streamlabs, Ko-fi, PayPal, SePay**:
  ```json
  {
    "sender": "Hoàng Nam",
    "amount": 5.0,
    "currency": "USD",
    "message": "Nấu cho mình tô Ramen đặc biệt nhé!"
  }
  ```
- Khi nhận được donate:
  - Game sẽ phát âm thanh leng keng của đồng vàng rơi.
  - Nổ hiệu ứng pháo hoa Confetti và tia sáng lung linh trên bàn ăn.
  - Tự động đẩy món ăn tương ứng vào bếp với thẻ VIP mang tên người ủng hộ!

---

## 6. Hướng dẫn Phát Sóng Livestream lên YouTube

Khung hình game được thiết kế chuẩn tỉ lệ **dọc 9:16 (720x1280)** để hiển thị tối ưu trên YouTube Shorts feed và màn hình điện thoại di động.

---

### Cách 1: Sử dụng OBS Studio (Khuyên dùng trên Windows)

Đây là cách phổ biến, dễ cài đặt và ổn định nhất cho streamer:

#### Bước 1: Cài đặt cấu hình dọc trong OBS Studio
1. Tải và cài đặt [OBS Studio](https://obsproject.com/).
2. Mở OBS → Chọn **Settings (Cài đặt)** → Tab **Video**:
   - **Base (Canvas) Resolution:** Gõ thủ công `720x1280`
   - **Output (Scaled) Resolution:** Gõ `720x1280` (hoặc `1080x1920` nếu mạng mạnh)
   - **Common FPS Values:** Chọn `30` (hoặc `60`)
3. Bấm **Apply** → Lúc này màn hình preview trong OBS sẽ chuyển sang khung dọc 9:16!

#### Bước 2: Thêm nguồn bắt hình & tiếng Game
1. Khởi động game bằng lệnh: `python main.py`
2. Trong OBS, tại ô **Sources (Nguồn)** bấm dấu `+`:
   - Chọn **Window Capture (Bắt cửa sổ)**.
   - Đặt tên là `CatCook Game`.
   - Trong mục Window, chọn: `[python.exe]: Cozy Midnight Diner - 24/7 Interactive Stream`.
   - Bấm **OK**. Kéo giãn hình ảnh vừa khít toàn bộ khung dọc 720x1280.
3. Thêm âm thanh:
   - Trong ô **Audio Mixer**, đảm bảo nguồn **Desktop Audio** đang bắt được tiếng nhạc Lofi và âm thanh chiên xào phát ra từ game.

#### Bước 3: Nhập Stream Key và Bắt đầu phát
1. Mở [YouTube Live Control Room (Studio)](https://studio.youtube.com/).
2. Bấm **Create (Tạo)** → **Go Live (Phát trực tiếp)**.
3. Chọn loại luồng trực tiếp, sao chép **Stream Key (Khóa phát trực tiếp)**.
4. Trong OBS: Vào **Settings** → Tab **Stream** → Chọn Service: **YouTube - RTMPS** → Dán Stream Key vào.
5. Bấm **Start Streaming (Bắt đầu phát trực tiếp)** trên OBS.
6. Buổi phát sóng của bạn đã chính thức lên sóng YouTube! 🎉

---

### Cách 2: Sử dụng FFmpeg chạy ngầm (Không cần OBS)

Nếu máy tính của bạn cấu hình khiêm tốn hoặc bạn muốn treo stream chạy ngầm không cần mở phần mềm nặng như OBS, bạn có thể dùng **FFmpeg**:

1. Cài đặt FFmpeg trên Windows (hoặc đã có sẵn trong Python qua `imageio_ffmpeg`).
2. Mở file [`stream/start_stream_windows.bat`](file:///c:/Users/dat/Downloads/catcook/stream/start_stream_windows.bat).
3. Thay `YOUR_STREAM_KEY` bằng Stream Key YouTube của bạn:
   ```bat
   ffmpeg -f gdigrab -framerate 30 -video_size 720x1280 -i title="Cozy Midnight Diner - 24/7 Interactive Stream" -c:v libx264 -preset veryfast -b:v 3500k -c:a aac -b:a 128k -f flv rtmp://a.rtmp.youtube.com/live2/YOUR_STREAM_KEY
   ```
4. Chạy file `.bat` để bắt đầu truyền thẳng luồng lên YouTube.

---

### Cách 3: Chạy 24/7 trên VPS Linux (Oracle Cloud / Ubuntu)

Dành cho ai muốn cắm stream liên tục cả tháng trên máy chủ ảo (VPS) mà không cần bật máy tính ở nhà:

1. Copy toàn bộ thư mục `catcook` lên máy chủ Ubuntu.
2. Cài đặt các gói phụ thuộc hệ thống:
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3-pip xvfb ffmpeg fonts-dejavu
   pip install -r requirements.txt
   ```
3. Cấp quyền thực thi và điền Stream Key vào file script:
   ```bash
   chmod +x stream/start_stream_linux.sh
   export STREAM_KEY="your_youtube_stream_key_here"
   ./stream/start_stream_linux.sh
   ```
   *(Script sẽ tự động tạo màn hình ảo `Xvfb :99` độ phân giải 720x1280, khởi chạy game và dùng FFmpeg x11grab đẩy luồng lên YouTube 24/7).*
4. Để stream tự động khởi động lại khi VPS reboot, cấu hình file systemd có sẵn tại [`systemd/diner_stream.service`](file:///c:/Users/dat/Downloads/catcook/systemd/diner_stream.service).

---

## 7. Các mẹo vận hành Stream 24/7 không gián đoạn

1. **Khóa Stream Key cố định:**
   - Trong YouTube Studio Live, hãy chọn **"Reusable Stream Key" (Khóa luồng có thể tái sử dụng)** thay vì khóa tạm thời theo từng phiên, để nếu có rớt mạng và kết nối lại thì không bị đổi URL stream.
2. **Bật Auto-Start và Auto-Stop:**
   - Trong cài đặt buổi live trên YouTube Studio, bật tùy chọn **Enable Auto-start** (Tự động phát khi có tín hiệu) và **Enable Auto-stop** (Tự động dừng khi ngắt kết nối).
3. **Duy trì Bot Viewer Simulator:**
   - Luôn bật Viewer Simulator (ở Tab 3 Studio Controller hoặc để mặc định trong config). Khi stream mới tạo chưa có khán giả thật, các lượt khách ảo sẽ ghé quán đều đặn mỗi 15-25 giây để màn hình không bao giờ bị đứng im, giúp thuật toán YouTube dễ đề xuất stream hơn.
4. **Tối ưu RAM/CPU:**
   - Pygame-ce và cấu trúc render tối ưu của Cozy Midnight Diner chỉ tiêu thụ khoảng **80 - 150 MB RAM** và **3-6% CPU**, rất nhẹ nhàng và an toàn khi treo máy dài ngày.
