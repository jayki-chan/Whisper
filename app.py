import gradio as gr
import whisper
import os
import tempfile
import base64
import json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Load Whisper model (small model - balance giữa tốc độ và độ chính xác)
print("Đang load Whisper model...")
model = whisper.load_model("small")
print("✅ Đã load Whisper model thành công!")

def transcribe_audio(audio_file):
    """
    Transcribe audio file bằng Whisper model

    Args:
        audio_file: Audio file từ Gradio (có thể là file path hoặc tuple)

    Returns:
        str: Text đã transcribe
    """
    try:
        # Xử lý input từ Gradio
        if audio_file is None:
            return "❌ Vui lòng upload file audio!"

        # Nếu audio_file là tuple (từ microphone), lấy file path
        if isinstance(audio_file, tuple):
            audio_path = audio_file[0]
        else:
            audio_path = audio_file

        print(f"🎤 Đang transcribe: {audio_path}")

        # Transcribe audio
        result = model.transcribe(
            audio_path,
            language="en",  # Auto-detect language, có thể đổi thành "vi" cho tiếng Việt
            fp16=False,     # Tắt FP16 để tương thích với CPU
            verbose=False
        )

        transcribed_text = result["text"].strip()
        print(f"✅ Kết quả: {transcribed_text}")

        return transcribed_text

    except Exception as e:
        error_msg = f"❌ Lỗi khi transcribe: {str(e)}"
        print(error_msg)
        return error_msg

def transcribe_base64(base64_audio, language="en"):
    """
    Transcribe audio từ base64 string

    Args:
        base64_audio: Audio đã encode base64
        language: Ngôn ngữ (mặc định "en", dùng None để auto-detect)

    Returns:
        dict: {"text": transcribed_text, "success": True/False}
    """
    try:
        # Decode base64 thành bytes
        audio_bytes = base64.b64decode(base64_audio)

        # Tạo file tạm để Whisper xử lý
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            temp_audio.write(audio_bytes)
            temp_audio_path = temp_audio.name

        print(f"🎤 Đang transcribe từ base64 (size: {len(audio_bytes)} bytes)")

        # Transcribe audio
        result = model.transcribe(
            temp_audio_path,
            language=language if language != "auto" else None,
            fp16=False,
            verbose=False
        )

        transcribed_text = result["text"].strip()

        # Xóa file tạm
        try:
            os.unlink(temp_audio_path)
        except:
            pass

        print(f"✅ Kết quả: {transcribed_text}")

        return {
            "success": True,
            "text": transcribed_text,
            "language": result.get("language", "unknown")
        }

    except Exception as e:
        error_msg = f"Lỗi khi transcribe: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }

# Tạo Gradio Interface
with gr.Blocks(title="Whisper Audio Transcription") as demo:
    gr.Markdown("""
    # 🎤 Whisper Audio Transcription

    Upload file audio hoặc record trực tiếp để chuyển đổi giọng nói thành text bằng OpenAI Whisper.

    **Model:** Whisper Small (chính xác cao, tốc độ vừa phải)

    **Hỗ trợ:** MP3, WAV, M4A, và nhiều định dạng audio khác
    """)

    with gr.Tab("📁 Upload File"):
        audio_input_file = gr.Audio(
            label="Upload Audio File",
            type="filepath",
            sources=["upload"]
        )
        transcribe_btn_file = gr.Button("🚀 Transcribe", variant="primary")
        output_text_file = gr.Textbox(
            label="Kết quả Transcription",
            placeholder="Text sẽ hiện ở đây...",
            lines=10
        )

        transcribe_btn_file.click(
            fn=transcribe_audio,
            inputs=audio_input_file,
            outputs=output_text_file
        )

    with gr.Tab("🎙️ Record Audio"):
        audio_input_mic = gr.Audio(
            label="Record Audio",
            type="filepath",
            sources=["microphone"]
        )
        transcribe_btn_mic = gr.Button("🚀 Transcribe", variant="primary")
        output_text_mic = gr.Textbox(
            label="Kết quả Transcription",
            placeholder="Text sẽ hiện ở đây...",
            lines=10
        )

        transcribe_btn_mic.click(
            fn=transcribe_audio,
            inputs=audio_input_mic,
            outputs=output_text_mic
        )

    with gr.Tab("🔐 Base64 Input (API)"):
        gr.Markdown("""
        ### Gửi audio dưới dạng Base64
        Nhập chuỗi base64 của audio file để transcribe (giống như trong code của bạn)
        """)

        base64_input = gr.Textbox(
            label="Base64 Audio String",
            placeholder="Paste base64 string của audio vào đây...",
            lines=5
        )

        language_select = gr.Dropdown(
            choices=["auto", "en", "vi", "zh", "ja", "ko", "es", "fr", "de"],
            value="auto",
            label="Ngôn ngữ (auto = tự động detect)"
        )

        transcribe_btn_base64 = gr.Button("🚀 Transcribe Base64", variant="primary")

        output_json = gr.JSON(label="Kết quả JSON")

        transcribe_btn_base64.click(
            fn=transcribe_base64,
            inputs=[base64_input, language_select],
            outputs=output_json
        )

    gr.Markdown("""
    ---
    ### 📝 Lưu ý:
    - Model hỗ trợ nhiều ngôn ngữ (auto-detect)
    - Chất lượng audio tốt hơn = kết quả chính xác hơn
    - Thời gian xử lý phụ thuộc vào độ dài audio
    - **Tab Base64**: Dùng để test API với base64 input (như trong code của bạn)

    ### 🔧 Powered by:
    - OpenAI Whisper (Small model)
    - Gradio
    - Hugging Face Spaces
    """)

# Launch app
if __name__ == "__main__":
    demo.launch()
