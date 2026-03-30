"""Check which TikTok account the token belongs to."""
import json
import httpx
import keyring

creds = keyring.get_password("clootsuite", "clootsuite_tiktok")
creds = json.loads(creds)
token = creds["access_token"]

r = httpx.get(
    "https://open.tiktokapis.com/v2/user/info/?fields=open_id,display_name,avatar_url",
    headers={"Authorization": f"Bearer {token}"},
)
print(f"Status: {r.status_code}")
print(f"Body: {json.dumps(r.json(), indent=2)}")
