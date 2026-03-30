"""Quick test of TikTok video init API."""
import json
import os
import httpx
import keyring

creds = keyring.get_password("clootsuite", "clootsuite_tiktok")
creds = json.loads(creds)
token = creds["access_token"]
video_path = "/Users/Julien/CascadeProjects/gamies/screenshots/marketing/clips/petit_bac_final_promo_es.mp4"
video_size = os.path.getsize(video_path)

print(f"Token: {token[:20]}...")
print(f"Video size: {video_size} bytes")

payload = {
    "post_info": {
        "title": "Test video",
        "privacy_level": "SELF_ONLY",
    },
    "source_info": {
        "source": "FILE_UPLOAD",
        "video_size": video_size,
        "chunk_size": video_size,
        "total_chunk_count": 1,
    },
}

print(f"Payload: {json.dumps(payload, indent=2)}")

r = httpx.post(
    "https://open.tiktokapis.com/v2/post/publish/video/init/",
    json=payload,
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
)
print(f"Status: {r.status_code}")
print(f"Body: {r.text}")
