#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通过 GitHub Contents API 逐文件 PUT 推送到 compute-market-report main 分支。
用于 git 协议在本沙箱故障时的回退方案。token 从环境变量 GH_TOKEN 读取。
"""
import base64
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

REPO = "Gavinzll/compute-market-report"
TOKEN = os.environ.get("GH_TOKEN", "")
BRANCH = "main"
ROOT = Path(__file__).resolve().parents[1]

FILES = [
    "assets/charts.js",
    "latest.html",
    "latest-mobile.html",
    "index.html",
    "reports/2026-08-23.html",
    "reports/2026-08-23-mobile.html",
    "data/cmis_snapshot_2026-08-23.json",
    "data/audit_2026-08-23.json",
    "data/rejected_2026-08-23.json",
    "data/history.jsonl",
    "data/discovered_token_2026-08-23.json",
    "data/discovered_gpu_2026-08-23.json",
    "data/discovered_benchmark_2026-08-23.json",
    "data/fx_rate_2026-08-23.json",
    "data/gitee_ai_2026-08-23.json",
    "data/shengsuanyun_2026-08-23.json",
]

PROG = ROOT / "data" / "_push_progress.jsonl"


def api(method, url, data=None, timeout=60):
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        return e.code, raw
    except Exception as e:
        return -1, str(e)


def get_sha(path):
    url = f"https://api.github.com/repos/{REPO}/contents/{path}?ref={BRANCH}"
    code, data = api("GET", url, timeout=30)
    if code == 200 and isinstance(data, dict):
        return data.get("sha")
    return None  # new file


def put_file(path, message, content_b64, sha=None):
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    payload = {"message": message, "content": content_b64, "branch": BRANCH}
    if sha:
        payload["sha"] = sha
    return api("PUT", url, data=payload, timeout=120)


def main():
    if not TOKEN:
        print("ERROR: GH_TOKEN not set"); sys.exit(1)
    done = set()
    if PROG.exists():
        for line in PROG.read_text().splitlines():
            try:
                done.add(json.loads(line)["path"])
            except Exception:
                pass
    total = len(FILES)
    for i, rel in enumerate(FILES, 1):
        if rel in done:
            print(f"[{i}/{total}] SKIP (done): {rel}"); continue
        local = ROOT / rel
        if not local.exists():
            print(f"[{i}/{total}] MISSING local: {rel}"); continue
        raw = local.read_bytes()
        b64 = base64.b64encode(raw).decode("ascii")
        print(f"[{i}/{total}] GET sha: {rel} ...", end=" ", flush=True)
        sha = get_sha(rel)
        print(f"sha={'upd' if sha else 'new'}")
        msg = f"chore(data): update {rel} for CMIS Daily 2026-08-23"
        print(f"[{i}/{total}] PUT: {rel} ({len(raw)} bytes) ...", end=" ", flush=True)
        code, data = put_file(rel, msg, b64, sha)
        if code in (200, 201):
            print(f"OK ({code})")
            with open(PROG, "a") as f:
                f.write(json.dumps({"path": rel, "code": code}) + "\n")
            done.add(rel)
        else:
            print(f"FAIL ({code}): {str(data)[:200]}")
        time.sleep(1)
    print(f"DONE: {len(done)}/{total} files pushed")


if __name__ == "__main__":
    main()
