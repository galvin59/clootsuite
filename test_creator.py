"""Check creator info and available privacy options."""
import json
import httpx
import keyring

creds = keyring.get_password("clootsuite", "clootsuite_tiktok")
creds = json.loads(creds)
token = creds["access_token"]

# Check creator info (available privacy levels, etc.)
r = httpx.post(
    "https://open.tiktokapis.com/v2/post/publish/creator_info/query/",
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    json={},
)
print(f"Creator Info Status: {r.status_code}")
print(f"Creator Info Body: {json.dumps(r.json(), indent=2)}")
