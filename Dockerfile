# Sử dụng Python 3.10 slim để giảm dung lượng
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Cài đặt ffmpeg (cần cho Whisper)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements trước để tận dụng Docker cache
COPY requirements.txt .

# Cài đặt Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Download Whisper model trước khi chạy (để không phải download mỗi lần restart)
RUN python -c "import whisper; whisper.load_model('small')"

# Expose port
EXPOSE 7860

# Run Gradio app
CMD ["python", "app.py"]
