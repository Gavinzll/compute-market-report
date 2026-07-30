#!/usr/bin/env python3
"""Push local commit to GitHub via Git Data API (no git protocol)."""
import json, subprocess, urllib.request, os, base64

TOKEN = os.environ.get("GH_TOKEN")
REPO = "Gavinzll/compute-market-report"
BASE = "https://api.github.com"

def req(method, url, body=None):
    data = None if body is None else json.dumps(body).encode()
    r = urllib.request.Request(url, data=data, method=method,
        headers={"Authorization": f"token {TOKEN}",
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "cmis-bot",
                 "Content-Type": "application/json"})
    try:
        return json.loads(urllib.request.urlopen(r, timeout=60).read())
    except urllib.error.HTTPError as e:
        body_e = e.read().decode()
        raise RuntimeError(f"{method} {url} -> {e.code}: {body_e[:300]}")

# Get parent of HEAD
local_head = subprocess.check_output(["git","rev-parse","HEAD"]).decode().strip()
local_msg = subprocess.check_output(["git","log","-1","--format=%B"]).decode().strip()
parent = subprocess.check_output(["git","rev-parse","HEAD^"]).decode().strip()
# Allow overriding parent to remote main tip (when local HEAD^ isn't on remote)
parent = os.environ.get("GH_PARENT", parent)
print(f"local head={local_head[:8]} parent={parent[:8]}")

# Confirm parent exists remotely
parent_remote = req("GET", f"{BASE}/repos/{REPO}/git/commits/{parent}")
print(f"parent on remote OK: {parent_remote['sha'][:8]}")
parent_tree = parent_remote["tree"]["sha"]

# List changed files (diff against local HEAD^, whose tree == remote tip tree)
local_parent = subprocess.check_output(["git","rev-parse","HEAD^"]).decode().strip()
files = subprocess.check_output(
    ["git","diff","--name-only", local_parent, local_head]).decode().splitlines()
files = [f for f in files if f]
print(f"changed files: {len(files)}")

# Upload blobs
tree_entries = []
for fp in files:
    full = os.path.join(os.getcwd(), fp)
    if not os.path.isfile(full):
        continue
    b64 = base64.b64encode(open(full,"rb").read()).decode()
    blob = req("POST", f"{BASE}/repos/{REPO}/git/blobs",
               {"content": b64, "encoding": "base64"})
    tree_entries.append({"path": fp, "mode": "100644", "type": "blob", "sha": blob["sha"]})
    print(f"  blob {fp} -> {blob['sha'][:8]}")

# Build tree
new_tree = req("POST", f"{BASE}/repos/{REPO}/git/trees",
               {"base_tree": parent_tree, "tree": tree_entries})
print(f"new tree: {new_tree['sha'][:8]}")

# Create commit
new_commit = req("POST", f"{BASE}/repos/{REPO}/git/commits", {
    "message": local_msg,
    "tree": new_tree["sha"],
    "parents": [parent],
})
print(f"new commit: {new_commit['sha'][:8]}")

# Update ref
ref = req("PATCH", f"{BASE}/repos/{REPO}/git/refs/heads/main",
          {"sha": new_commit["sha"], "force": False})
print(f"ref updated: {ref['object']['sha'][:8]}")
print("PUSH OK")
