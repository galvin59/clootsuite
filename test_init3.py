"""Test with PUBLIC_TO_EVERYONE since creator_info says it's available."""
import json
import os
import httpx
import keyring

creds = keyring.get_password("clootsuite", "clootsuite_tiktok")
creds = json.loads(creds)
token = creds["access_token"]
video_path = "/Users/Julien/CascadeProjects/gamies/screenshots/marketing/clips/petit_bac_final_promo_es.mp4"
video_size = os.path.getsize(video_path)

# Try with the exact minimal payload
payload = {
    "post_info": {
        "title": "Test video #test",
        "privacy_level": "PUBLIC_TO_EVERYONE",
    },
    "source_info": {
        "source": "FILE_UPLOAD",
        "video_size": video_size,
        "chunk_size": video_size,
        "total_chunk_count": 1,
    },
}

print(f"Sending init request...")
r = httpx.post(
    "https://open.tiktokapis.com/v2/post/publish/video/init/",
    json=payload,
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
)
print(f"Status: {r.status_code}")
print(f"Body: {json.dumps(r.json(), indent=2)}")

if r.status_code == 200 and r.json().get("error", {}).get("code") == "ok":
    data = r.json()["data"]
    upload_url = data["upload_url"]
    publish_id = data["publish_id"]
    print(f"\nSUCCESS! Upload URL received.")
    print(f"Publish ID: {publish_id}")

    # Upload the video
    print(f"\nUploading video ({video_size} bytes)...")
    with open(video_path, "rb") as f:
        video_data = f.read()

    r2 = httpx.put(
        upload_url,
        content=video_data,
        headers={
            "Content-Range": f"bytes 0-{video_size-1}/{video_size}",
            "Content-Type": "video/mp4",
        },
        timeout=120,
    )
    print(f"Upload Status: {r2.status_code}")
    print(f"Upload Body: {r2.text[:500]}")

    if r2.status_code in (200, 201, 202, 204, 206):
        print("\nUpload complete! Checking publish status...")
        import time
        for i in range(6):
            time.sleep(5)
            r3 = httpx.post(
                "https://open.tiktokapis.com/v2/post/publish/status/fetch/",
                json={"publish_id": publish_id},
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            )
            status_data = r3.json()
            print(f"  Poll {i+1}: {json.dumps(status_data, indent=2)}")
            pub_status = status_data.get("data", {}).get("status", "")
            if pub_status in ("PUBLISH_COMPLETE", "FAILED", "PUBLISH_FAILED"):
                break
