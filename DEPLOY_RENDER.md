# 🚀 Hướng Dẫn Deploy Whisper API lên Render (FREE)

## ✅ Điều Kiện
- Tài khoản GitHub (miễn phí)
- Tài khoản Render (miễn phí - không cần thẻ credit)

---

## 📋 BƯỚC 1: Chuẩn Bị GitHub Repository

### 1.1. Tạo Repository Mới trên GitHub
1. Vào https://github.com/new
2. Đặt tên repo (ví dụ: `whisper-api`)
3. Chọn **Public** hoặc **Private** (cả 2 đều free trên Render)
4. **KHÔNG** tick "Initialize with README"
5. Click **Create repository**

### 1.2. Push Code Lên GitHub

Mở Terminal/CMD trong thư mục `huggingface_deploy` và chạy:

```bash
# Khởi tạo git repo (nếu chưa có)
git init

# Add tất cả files
git add .

# Commit
git commit -m "Initial commit - Whisper API for TikTok Tool"

# Thêm remote (thay YOUR_USERNAME và YOUR_REPO)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Push lên GitHub
git branch -M main
git push -u origin main
```

**Lưu ý:** Thay `YOUR_USERNAME` và `YOUR_REPO` bằng username và tên repo của bạn!

---

## 🌐 BƯỚC 2: Deploy Lên Render

### 2.1. Tạo Tài Khoản Render
1. Vào https://render.com
2. Click **Get Started** → Sign Up với GitHub
3. Authorize Render để truy cập GitHub

### 2.2. Tạo Web Service Mới
1. Sau khi đăng nhập, click **New +** → **Web Service**
2. Chọn repository `whisper-api` vừa tạo
3. Click **Connect**

### 2.3. Cấu Hình Deploy
Điền thông tin như sau:

| Trường | Giá Trị |
|--------|---------|
| **Name** | `whisper-transcription-api` (hoặc tên bạn thích) |
| **Region** | `Singapore` (gần Việt Nam nhất) |
| **Branch** | `main` |
| **Runtime** | `Docker` |
| **Instance Type** | **Free** ✅ |

### 2.4. Environment Variables (Tùy chọn)
Không cần thêm gì, giữ mặc định.

### 2.5. Deploy!
1. Click **Create Web Service**
2. Đợi ~5-10 phút để Render:
   - Build Docker image
   - Download Whisper model
   - Start service

**Theo dõi logs để xem tiến trình!**

---

## ✅ BƯỚC 3: Kiểm Tra & Sử Dụng

### 3.1. Lấy URL API
Sau khi deploy xong, bạn sẽ có URL dạng:
```
https://whisper-transcription-api.onrender.com
```

### 3.2. Test API
1. Mở URL trên trình duyệt → Thấy giao diện Gradio ✅
2. Upload file audio để test

### 3.3. Cập Nhật Code RegTikTok.py
Sửa dòng 76 trong file `RegTikTok.py`:

```python
# CŨ (Hugging Face):
self.whisper_api_url = "https://ganggangthao-whisper-transcription.hf.space/api/predict"

# MỚI (Render - URL của bạn):
self.whisper_api_url = "https://YOUR-APP-NAME.onrender.com/api/predict"
```

**Thay `YOUR-APP-NAME` bằng tên app của bạn trên Render!**

---

## 🎯 Kiểm Tra API Với Multi-Threading

Chạy file test:
```bash
python test_api_concurrent.py
```

Nếu thấy ✅ → API sẵn sàng cho đa luồng!

---

## 📊 Giới Hạn Free Tier của Render

| Tính năng | Giới hạn |
|-----------|----------|
| **Giờ chạy** | 750 giờ/tháng (đủ dùng cả tháng) |
| **RAM** | 512 MB |
| **CPU** | Shared (đủ cho Whisper Small) |
| **Bandwidth** | 100 GB/tháng |
| **Sleep** | Sau 15 phút không dùng |
| **Cold start** | ~30 giây khi wake up |

### Lưu Ý Về Sleep Mode:
- Service sẽ **ngủ** sau 15 phút không có request
- Request đầu tiên sau khi ngủ sẽ mất ~30 giây để wake up
- Các request tiếp theo sẽ nhanh bình thường

**Giải pháp:**
- Nếu muốn API luôn active, có thể dùng cron job ping mỗi 10 phút
- Hoặc upgrade lên plan $7/tháng để không bị sleep

---

## 🔧 Troubleshooting

### Lỗi: Build Failed
- Kiểm tra logs trên Render
- Đảm bảo `Dockerfile` và `requirements.txt` đúng

### Lỗi: Out of Memory
- Whisper Small đã tối ưu cho 512MB RAM
- Nếu vẫn lỗi, thử model `tiny` (nhỏ hơn)

### Lỗi: Too Many Requests (vẫn còn)
- API của bạn không giới hạn requests!
- Có thể do network hoặc code logic
- Kiểm tra logs trong `RegTikTok.py`

---

## 🎊 Hoàn Thành!

Bạn đã có API Whisper riêng, **MIỄN PHÍ**, **KHÔNG GIỚI HẠN REQUESTS**!

### Ưu điểm so với Hugging Face:
✅ Không bị rate limit "too many requests"
✅ Ổn định hơn khi chạy đa luồng
✅ Control hoàn toàn API của mình
✅ Có thể custom code tùy ý

### Nếu cần nâng cấp:
- **$7/tháng**: Không sleep, 2GB RAM, nhiều CPU hơn
- Hoặc dùng **VPS** nếu cần performance cao hơn

---

**Chúc bạn thành công! 🎉**

Nếu có vấn đề gì, check logs trên Render Dashboard.
