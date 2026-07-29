import io
import os
import requests
from PIL import Image, ImageDraw

BASE_URL = os.getenv("TARGET_URL", "http://travel_ai_extractor_api:8000")
API_KEY = os.getenv("API_KEY", "travel_sec_key_892374918237")
HEADERS = {"X-API-Key": API_KEY}

def clear_cache():
    print("Clearing cache for fresh extraction testing...")
    res = requests.delete(f"{BASE_URL}/cache", headers=HEADERS)
    print(f"Cache cleared response: {res.json()}\n")

def test_real_paris_text_extraction():
    print("--- REAL TEST 1: Real Travel Text Extraction (Paris, France) ---")
    payload = {
        "text": "Just arrived in Paris! Spent the afternoon walking near the Eiffel Tower, grabbed coffee by the Louvre Museum, and visited Notre-Dame Cathedral.",
        "context": "Paris, France Trip"
    }
    res = requests.post(f"{BASE_URL}/extract/text", json=payload, headers=HEADERS)
    print(f"Status Code: {res.status_code}")
    data = res.json()
    print(f"Destination: {data.get('destination')}")
    print(f"Execution Time: {data.get('execution_time_seconds')} seconds")
    print("Extracted Places:")
    for place in data.get("places", []):
        print(f"  - {place['name']} | City: {place['city']} | Country: {place['country']} | Verified: {place['verified']} | Confidence: {place['confidence']}%")
    print("")

def test_real_rome_image_extraction():
    print("--- REAL TEST 2: Real Travel Image Extraction (Rome Colosseum) ---")
    img = Image.new("RGB", (800, 400), color=(250, 245, 235))
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 750, 350], fill=(220, 200, 180), outline=(100, 50, 0), width=4)
    draw.text((100, 150), "WELCOME TO COLOSSEUM", fill=(80, 20, 0))
    draw.text((100, 220), "PIAZZA DEL COLOSSEO, ROME, ITALY", fill=(50, 50, 50))

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    img_bytes = img_byte_arr.getvalue()

    files = {"file": ("colosseum_rome_photo.jpg", img_bytes, "image/jpeg")}
    res = requests.post(f"{BASE_URL}/extract/image", files=files, headers=HEADERS)
    print(f"Status Code: {res.status_code}")
    data = res.json()
    print(f"Destination: {data.get('destination')}")
    print(f"Execution Time: {data.get('execution_time_seconds')} seconds")
    print("Extracted Places:")
    for place in data.get("places", []):
        print(f"  - {place['name']} | City: {place['city']} | Country: {place['country']} | Verified: {place['verified']} | Confidence: {place['confidence']}%")
    print("")

def test_real_universal_multi_source():
    print("--- REAL TEST 3: Real Universal Multi-Source Extraction (Iceland) ---")
    payload = {
        "source_type": "text",
        "content": "Exploring the Blue Lagoon geothermal spa, Skogafoss waterfall, and Gullfoss in Iceland.",
        "context": "Iceland Ring Road Trip"
    }
    res = requests.post(f"{BASE_URL}/extract/universal", json=payload, headers=HEADERS)
    print(f"Status Code: {res.status_code}")
    data = res.json()
    print(f"Destination: {data.get('destination')}")
    print(f"Execution Time: {data.get('execution_time_seconds')} seconds")
    print("Extracted Places:")
    for place in data.get("places", []):
        print(f"  - {place['name']} | City: {place['city']} | Country: {place['country']} | Verified: {place['verified']} | Confidence: {place['confidence']}%")
    print("")

if __name__ == "__main__":
    print("==========================================================")
    print("      EXECUTING REAL TRAVEL CONTENT EXTRACTION TESTS      ")
    print(f"      Target: {BASE_URL}")
    print("==========================================================\n")
    clear_cache()
    test_real_paris_text_extraction()
    test_real_rome_image_extraction()
    test_real_universal_multi_source()
    print("==========================================================")
    print("      REAL EXTRACTION TESTS COMPLETED SUCCESSFULLY! 🎉    ")
    print("==========================================================")
