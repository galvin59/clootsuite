"""Test different privacy levels for TikTok sandbox."""
import json
import os
import httpx
import keyring

creds = keyring.get_password("clootsuite", "clootsuite_tiktok")
creds = json.loads(creds)
token = creds["access_token"]
video_path = "/Users/Julien/CascadeProjects/gamies/screenshots/marketing/clips/petit_bac_final_promo_es.mp4"
video_size = os.path.getsize(video_path)

for privacy in ["SELF_ONLY", "FOLLOWER_OF_CREATOR", "MUTUAL_FOLLOW_FRIENDS"]:
    payload = {
        "post_info": {
            "title": "Test video",
            "privacy_level": privacy,
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": video_size,
            "chunk_size": video_size,
            "total_chunk_count": 1,
        },
    }

    r = httpx.post(
        "https://open.tiktokapis.com/v2/post/publish/video/init/",
        json=payload,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    print(f"privacy_level={privacy}: {r.status_code} => {r.json().get('error', {}).get('code', 'ok')}")
    if r.status_code == 200 and r.json().get("error", {}).get("code") == "ok":
        print(f"  SUCCESS! Data: {json.dumps(r.json()['data'], indent=2)}")
        break
