---
title: Whisper Audio Transcription
emoji: 🎤
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.19.2
app_file: app.py
pinned: false
license: mit
---

# 🎤 Whisper Audio Transcription

Ứng dụng chuyển đổi giọng nói thành text (Speech-to-Text) sử dụng OpenAI Whisper model.

## ✨ Tính năng

- 📁 **Upload file audio**: Hỗ trợ MP3, WAV, M4A, và nhiều định dạng khác
- 🎙️ **Record trực tiếp**: Ghi âm và transcribe ngay lập tức
- 🌍 **Đa ngôn ngữ**: Tự động detect ngôn ngữ (hỗ trợ 100+ ngôn ngữ)
- ⚡ **Nhanh chóng**: Sử dụng Whisper Small model cho tốc độ và độ chính xác tốt

## 🔧 Technology Stack

- **Model**: OpenAI Whisper Small
- **Framework**: Gradio 4.19.2
- **Hosting**: Hugging Face Spaces (Free Tier)

## 🚀 Cách sử dụng

1. Chọn tab "Upload File" hoặc "Record Audio"
2. Upload file audio hoặc record giọng nói
3. Click nút "Transcribe"
4. Nhận kết quả text

## 💡 Tips

- Sử dụng audio chất lượng tốt để có kết quả chính xác nhất
- Nói rõ ràng và tránh tiếng ồn nền
- Model hỗ trợ auto-detect ngôn ngữ, không cần chỉ định trước

## 📦 Deploy locally

```bash
# Clone repository
git clone <your-repo-url>
cd huggingface_deploy

# Install dependencies
pip install -r requirements.txt

# Run app
python app.py
```

## 📄 License

MIT License

---

**Powered by OpenAI Whisper & Hugging Face Spaces**
