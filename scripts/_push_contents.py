#!/usr/bin/env python3
"""Push changed files to GitHub main via Contents API (per-file PUT).
Git protocol fails in sandbox; Git Data API (blobs) 403s on this PAT.
Contents API PUT (201) is the only working path for compute-market-report.
"""
import base64, json, os, subprocess, urllib.error, urllib.request, sys

TOKEN = os.environ["GH_TOKEN"]
REPO = "Gavinzll/compute-market-report"
BASE = "https://api.github.com"
HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "cmis-bot",
}

def api(method, url, body=None):
    data = None if body is None else json.dumps(body).encode()
    r = urllib.request.Request(url, data=data, method=method, headers=HEADERS)
    try:
        return json.loads(urllib.request.urlopen(r, timeout=60).read())
    except urllib.error.HTTPError as e:
        return {"_status": e.code, "_body": e.read().decode()[:300]}

local_head = subprocess.check_output(["git","rev-parse","HEAD"]).decode().strip()
local_parent = subprocess.check_output(["git","rev-parse","HEAD^"]).decode().strip()
files = [f for f in subprocess.check_output(
    ["git","diff","--name-only", local_parent, local_head]).decode().splitlines() if f]
print(f"changed files: {len(files)}")

ok = 0
for fp in files:
    full = os.path.join(os.getcwd(), fp)
    if not os.path.isfile(full):
        print(f"  SKIP (not a file): {fp}")
        continue
    content_b = open(full,"rb").read()
    b64 = base64.b64encode(content_b).decode()
    # GET current file sha (for update) — 404 means create
    get = api("GET", f"{BASE}/repos/{REPO}/contents/{fp}?ref=main")
    sha = get.get("sha") if isinstance(get, dict) else None
    body = {"message": f"chore(data): update {fp} for CMIS Daily {os.popen('date +%F').read().strip()}",
            "content": b64, "branch": "main",
            "committer": {"name":"Gavin","email":"Gavinzll@users.noreply.github.com"}}
    if sha:
        body["sha"] = sha
    res = api("PUT", f"{BASE}/repos/{REPO}/contents/{fp}", body)
    st = res.get("_status") or res.get("content",{}).get("sha","")
    if isinstance(res, dict) and res.get("content"):
        print(f"  OK  {fp} -> {res['content']['sha'][:8]}")
        ok += 1
    else:
        print(f"  FAIL {fp} -> {res.get('_status')} {str(res.get('_body',''))[:120]}")
print(f"pushed {ok}/{len(files)} files")
sys.exit(0 if ok==len(files) else 1)
