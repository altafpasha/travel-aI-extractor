import io
import os
import time
import requests
from PIL import Image, ImageDraw

BASE_URL = os.getenv("TARGET_URL", "http://travel_ai_extractor_api:8000")
API_KEY = os.getenv("API_KEY", "travel_sec_key_892374918237")
HEADERS = {"X-API-Key": API_KEY}

def test_health():
    print("1. Testing Health Endpoint (GET /health)...")
    res = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {res.status_code}")
    print(f"Response: {res.json()}\n")
    assert res.status_code == 200

def test_text_extraction():
    print("2. Testing Text Extraction (POST /extract/text)...")
    payload = {
        "text": "Exploring Shibuya Crossing and Tokyo Tower in Tokyo Japan.",
        "context": "Tokyo Vacation"
    }
    res = requests.post(f"{BASE_URL}/extract/text", json=payload, headers=HEADERS)
    print(f"Status Code: {res.status_code}")
    print(f"Response: {res.json()}\n")
    assert res.status_code == 200

def test_image_extraction():
    print("3. Testing Image Extraction (POST /extract/image)...")
    img = Image.new("RGB", (400, 200), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    draw.text((20, 80), "Kyoto Fushimi Inari Shrine", fill=(0, 0, 0))
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    img_bytes = img_byte_arr.getvalue()

    files = {"file": ("test_kyoto_photo.jpg", img_bytes, "image/jpeg")}
    res = requests.post(f"{BASE_URL}/extract/image", files=files, headers=HEADERS)
    print(f"Status Code: {res.status_code}")
    print(f"Response: {res.json()}\n")
    assert res.status_code == 200

def test_video_extraction():
    print("4. Testing Video Extraction (POST /extract/video)...")
    dummy_video_path = "/tmp/temp_test_video.mp4"
    os.system(f'ffmpeg -y -f lavfi -i testsrc=duration=3:size=320x240:rate=1 -c:v libx264 "{dummy_video_path}" -loglevel quiet')
    
    if os.path.exists(dummy_video_path) and os.path.getsize(dummy_video_path) > 0:
        with open(dummy_video_path, "rb") as f:
            video_bytes = f.read()
        files = {"file": ("travel_reel.mp4", video_bytes, "video/mp4")}
        res = requests.post(f"{BASE_URL}/extract/video", files=files, headers=HEADERS)
        print(f"Status Code: {res.status_code}")
        print(f"Response: {res.json()}\n")
        assert res.status_code == 200
        try:
            os.remove(dummy_video_path)
        except Exception:
            pass
    else:
        print("FFmpeg cli unavailable for synthetic mp4 generation, skipping video binary upload file step.")

def test_universal_extraction():
    print("5. Testing Universal Extraction (POST /extract/universal)...")
    payload = {
        "source_type": "text",
        "content": "Exploring cafes in Kyoto and visiting Fushimi Inari.",
        "context": "Japan"
    }
    res = requests.post(f"{BASE_URL}/extract/universal", json=payload, headers=HEADERS)
    print(f"Status Code: {res.status_code}")
    print(f"Response: {res.json()}\n")
    assert res.status_code == 200

def test_async_queue_and_polling():
    print("6. Testing Async Queue & Polling (POST /extract/async & GET /jobs/{job_id})...")
    payload = {
        "source_type": "text",
        "content": "Visiting Fushimi Inari Shrine and Kinkaku-ji in Kyoto.",
        "context": "Async Queue Test"
    }
    res = requests.post(f"{BASE_URL}/extract/async", json=payload, headers=HEADERS)
    print(f"Enqueue Status Code: {res.status_code}")
    data = res.json()
    print(f"Enqueue Response: {data}")
    assert res.status_code == 202
    job_id = data["job_id"]

    for _ in range(10):
        time.sleep(0.3)
        poll_res = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=HEADERS)
        poll_data = poll_res.json()
        print(f"Poll Job Status ({job_id}): {poll_data['status']}")
        if poll_data["status"] == "completed":
            print(f"Final Job Result: {poll_data['result']}\n")
            break

def test_cache_stats_and_prune():
    print("7. Testing Cache Statistics & Retention Pruning (GET /cache & DELETE /cache/prune)...")
    stats_res = requests.get(f"{BASE_URL}/cache", headers=HEADERS)
    print(f"Cache Stats Status Code: {stats_res.status_code}")
    print(f"Cache Stats Response: {stats_res.json()}")

    prune_res = requests.delete(f"{BASE_URL}/cache/prune?days=30", headers=HEADERS)
    print(f"Prune Status Code: {prune_res.status_code}")
    print(f"Prune Response: {prune_res.json()}\n")
    assert prune_res.status_code == 200

if __name__ == "__main__":
    print("==================================================")
    print("   STARTING END-TO-END LIVE FEATURE INTEGRATION TESTS")
    print(f"   Target URL: {BASE_URL}")
    print("==================================================\n")
    test_health()
    test_text_extraction()
    test_image_extraction()
    test_video_extraction()
    test_universal_extraction()
    test_async_queue_and_polling()
    test_cache_stats_and_prune()
    print("==================================================")
    print("   ALL LIVE FEATURE INTEGRATION TESTS PASSED SUCCESSFULLY! 🎉")
    print("==================================================")
