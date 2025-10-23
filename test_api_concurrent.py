"""
Test Whisper API với nhiều luồng đồng thời
Kiểm tra performance khi chạy multi-threading như trong RegTikTok.py
"""

import sys
import os
import threading
import time
from datetime import datetime

# Fix encoding cho Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

try:
    from gradio_client import Client
    import base64
except ImportError:
    print("❌ Chưa cài gradio_client!")
    print("Chạy: pip install gradio_client")
    sys.exit(1)

# Config
SPACE_URL = "https://ganggangthao-whisper-transcription.hf.space"
TEST_AUDIO = "test_audio.mp3"
NUM_THREADS = 5  # Số luồng test (giống khi chạy nhiều account cùng lúc)

# Shared results
results = []
results_lock = threading.Lock()


def test_api_in_thread(thread_id, audio_path):
    """
    Test API trong 1 thread (giống mỗi account register trong RegTikTok)
    """
    start_time = time.time()
    result = {
        'thread_id': thread_id,
        'success': False,
        'text': None,
        'duration': 0,
        'error': None
    }

    try:
        print(f"[Thread-{thread_id}] 🚀 Bắt đầu gọi API...")

        # Đọc và convert audio sang base64
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
            base64_audio = base64.b64encode(audio_bytes).decode('utf-8')

        # Kết nối và gọi API
        client = Client(SPACE_URL)

        api_result = client.predict(
            base64_audio,
            "en",
            api_name="/transcribe_base64"
        )

        duration = time.time() - start_time

        # Parse kết quả
        if isinstance(api_result, dict) and api_result.get("success"):
            text = api_result.get("text", "").strip()
            clean_text = ''.join(c for c in text if c.isalnum())

            result['success'] = True
            result['text'] = clean_text
            result['duration'] = duration

            print(f"[Thread-{thread_id}] ✅ Thành công! Text: '{clean_text}' | Thời gian: {duration:.2f}s")
        else:
            error = api_result.get("error", "Unknown error")
            result['error'] = error
            result['duration'] = duration
            print(f"[Thread-{thread_id}] ❌ Lỗi: {error} | Thời gian: {duration:.2f}s")

    except Exception as e:
        duration = time.time() - start_time
        result['error'] = str(e)
        result['duration'] = duration
        print(f"[Thread-{thread_id}] ❌ Exception: {e} | Thời gian: {duration:.2f}s")

    # Lưu kết quả
    with results_lock:
        results.append(result)


def test_concurrent_api(num_threads=5):
    """
    Test API với nhiều luồng đồng thời
    """
    print("=" * 70)
    print("🔥 TEST WHISPER API - MULTI-THREADING")
    print("=" * 70)
    print(f"Space URL: {SPACE_URL}")
    print(f"Audio file: {TEST_AUDIO}")
    print(f"Số luồng: {NUM_THREADS}")
    print("-" * 70)

    if not os.path.exists(TEST_AUDIO):
        print(f"❌ File không tồn tại: {TEST_AUDIO}")
        return False

    # Reset results
    global results
    results = []

    # Tạo và start threads
    threads = []
    start_time = time.time()

    print(f"\n⏰ Bắt đầu: {datetime.now().strftime('%H:%M:%S')}")
    print(f"🚀 Tạo {num_threads} threads...\n")

    for i in range(num_threads):
        thread = threading.Thread(
            target=test_api_in_thread,
            args=(i + 1, TEST_AUDIO)
        )
        threads.append(thread)
        thread.start()

        # Delay nhỏ để tránh request cùng lúc quá
        time.sleep(0.5)

    print(f"\n⏳ Đang đợi {num_threads} threads hoàn thành...\n")

    # Đợi tất cả threads hoàn thành
    for thread in threads:
        thread.join()

    total_duration = time.time() - start_time

    # Phân tích kết quả
    print("\n" + "=" * 70)
    print("📊 KẾT QUẢ PHÂN TÍCH")
    print("=" * 70)

    success_count = sum(1 for r in results if r['success'])
    fail_count = len(results) - success_count

    print(f"\n🎯 Tổng quan:")
    print(f"   • Tổng requests: {len(results)}")
    print(f"   • Thành công: {success_count} ✅")
    print(f"   • Thất bại: {fail_count} ❌")
    print(f"   • Tỷ lệ thành công: {success_count/len(results)*100:.1f}%")
    print(f"   • Tổng thời gian: {total_duration:.2f}s")

    if results:
        durations = [r['duration'] for r in results]
        avg_duration = sum(durations) / len(durations)
        min_duration = min(durations)
        max_duration = max(durations)

        print(f"\n⏱️  Thời gian xử lý:")
        print(f"   • Trung bình: {avg_duration:.2f}s")
        print(f"   • Nhanh nhất: {min_duration:.2f}s")
        print(f"   • Chậm nhất: {max_duration:.2f}s")

    # Chi tiết từng thread
    print(f"\n📋 Chi tiết từng thread:")
    for r in sorted(results, key=lambda x: x['thread_id']):
        status = "✅" if r['success'] else "❌"
        text = r['text'] if r['text'] else "N/A"
        error = f" - Error: {r['error']}" if r['error'] else ""
        print(f"   Thread-{r['thread_id']}: {status} | {r['duration']:.2f}s | Text: {text}{error}")

    # Đánh giá
    print("\n" + "=" * 70)
    print("💡 ĐÁNH GIÁ & KHUYẾN NGHỊ")
    print("=" * 70)

    if success_count == len(results):
        print("\n✅ API hoạt động HOÀN HẢO với multi-threading!")
        print("   → Có thể chạy nhiều luồng đồng thời trong RegTikTok.py")
        print(f"   → Khuyến nghị: {num_threads}-{num_threads*2} threads đồng thời")
    elif success_count >= len(results) * 0.8:
        print("\n⚠️  API hoạt động TỐT nhưng có vài lỗi:")
        print(f"   → {fail_count} requests bị fail (có thể do network hoặc Space quá tải)")
        print("   → Khuyến nghị: Giảm số threads hoặc thêm retry logic")
    else:
        print("\n❌ API KHÔNG ỔN ĐỊNH với nhiều requests đồng thời:")
        print(f"   → {fail_count}/{len(results)} requests failed")
        print("   → Khuyến nghị:")
        print("     1. Giảm số threads (1-2 threads)")
        print("     2. Thêm delay giữa các requests")
        print("     3. Hoặc dùng local Whisper model")

    print("\n" + "=" * 70)

    return success_count == len(results)


def test_sequential_api(num_requests=5):
    """
    Test API tuần tự (không dùng threading) để so sánh
    """
    print("\n" + "=" * 70)
    print("🐌 TEST SEQUENTIAL (Không dùng threading)")
    print("=" * 70)

    results_seq = []
    start_time = time.time()

    for i in range(num_requests):
        print(f"\n[Request {i+1}/{num_requests}] 🚀 Gọi API...")

        try:
            with open(TEST_AUDIO, "rb") as f:
                base64_audio = base64.b64encode(f.read()).decode('utf-8')

            req_start = time.time()
            client = Client(SPACE_URL)
            result = client.predict(base64_audio, "en", api_name="/transcribe_base64")
            duration = time.time() - req_start

            if result.get("success"):
                text = ''.join(c for c in result.get("text", "") if c.isalnum())
                print(f"[Request {i+1}] ✅ Thành công: {text} | {duration:.2f}s")
                results_seq.append({'success': True, 'duration': duration})
            else:
                print(f"[Request {i+1}] ❌ Lỗi | {duration:.2f}s")
                results_seq.append({'success': False, 'duration': duration})

        except Exception as e:
            print(f"[Request {i+1}] ❌ Exception: {e}")
            results_seq.append({'success': False, 'duration': 0})

    total_duration = time.time() - start_time
    avg_duration = sum(r['duration'] for r in results_seq) / len(results_seq)

    print(f"\n📊 Sequential results:")
    print(f"   • Tổng thời gian: {total_duration:.2f}s")
    print(f"   • Trung bình/request: {avg_duration:.2f}s")

    return results_seq


# ========== MAIN ==========
if __name__ == "__main__":
    if not os.path.exists(TEST_AUDIO):
        print(f"⚠️ Không tìm thấy file: {TEST_AUDIO}")
        sys.exit(1)

    # Test 1: Multi-threading (giống RegTikTok)
    print("\n🔥 TEST 1: MULTI-THREADING")
    success_concurrent = test_concurrent_api(NUM_THREADS)

    # Test 2: Sequential (để so sánh)
    # print("\n🐌 TEST 2: SEQUENTIAL")
    # test_sequential_api(NUM_THREADS)

    # Kết luận
    print("\n" + "🎊" * 25)
    if success_concurrent:
        print("✅ API SẴN SÀNG CHO MULTI-THREADING!")
        print("✅ Có thể chạy RegTikTok.py với nhiều luồng")
    else:
        print("⚠️  CÂN NHẮC GIẢM SỐ LUỒNG HOẶC DÙNG LOCAL MODEL")
    print("🎊" * 25)
