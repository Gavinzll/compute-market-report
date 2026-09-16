#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CMIS Daily 当日产物推送：基于远端 main 树基线（tarball）计算差异，
通过 GitHub Contents API 逐文件 PUT 推送。token 从环境变量 GH_TOKEN 读取。
进度落盘 data/_push_progress_today.jsonl，可幂等续跑。"""
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = "Gavinzll/compute-market-report"
TOKEN = os.environ.get("GH_TOKEN", "")
BRANCH = "main"
ROOT = Path(__file__).resolve().parents[1]
BASE = "https://api.github.com"
PROG = ROOT / "data" / "_push_progress_today.jsonl"

FILES = [
    "assets/charts.js",
    "latest.html",
    "latest-mobile.html",
    "index.html",
    "reports/2026-09-15.html",
    "reports/2026-09-15-mobile.html",
    "data/history.jsonl",
    "data/price_changes.csv",
    "data/audit_2026-09-15.json",
    "data/cmis_snapshot_2026-09-15.json",
    "data/discovered_benchmark_2026-09-15.json",
    "data/discovered_gpu_2026-09-15.json",
    "data/discovered_token_2026-09-15.json",
    "data/fx_rate_2026-09-15.json",
    "data/gitee_ai_2026-09-15.json",
    "data/rejected_2026-09-15.json",
    "data/shengsuanyun_2026-09-15.json",
    "data/raw/gpurentalprices_2026-09-15.json",
    "data/raw/litellm_2026-09-15.json",
    "data/raw/modelsdev_2026-09-15.json",
    "data/raw/openrouter_2026-09-15.json",
]


def api(method, url, data=None, timeout=90):
    headers = {
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "cmis-bot",
    }
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:500]
    except Exception as e:
        return 0, str(e)[:500]


def load_progress():
    done = set()
    if PROG.exists():
        for line in PROG.read_text(encoding="utf-8").splitlines():
            try:
                rec = json.loads(line)
                if rec.get("ok"):
                    done.add(rec["path"])
            except json.JSONDecodeError:
                pass
    return done


def mark(path, ok, detail=""):
    with open(PROG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"path": path, "ok": ok, "detail": detail},
                           ensure_ascii=False) + "\n")


def remote_sha(path):
    st, body = api("GET", f"{BASE}/repos/{REPO}/contents/{path}?ref={BRANCH}")
    if st == 200 and isinstance(body, dict):
        return body.get("sha")
    return None  # 不存在（新文件）


def main():
    if not TOKEN:
        print("GH_TOKEN not set", file=sys.stderr)
        sys.exit(2)
    done = load_progress()
    failures = 0
    for path in FILES:
        if path in done:
            print(f"[skip done] {path}")
            continue
        local = ROOT / path
        if not local.exists():
            print(f"[missing local] {path}", file=sys.stderr)
            mark(path, False, "local missing")
            failures += 1
            continue
        content = base64.b64encode(local.read_bytes()).decode("ascii")
        sha = remote_sha(path)
        payload = {
            "message": f"chore(data): update {path} for CMIS Daily 2026-09-15",
            "content": content,
            "branch": BRANCH,
        }
        if sha:
            payload["sha"] = sha
        st, body = api("PUT", f"{BASE}/repos/{REPO}/contents/{path}", payload,
                       timeout=300)
        if st in (200, 201):
            print(f"[ok {st}] {path}")
            mark(path, True)
        else:
            print(f"[fail {st}] {path} -> {body}", file=sys.stderr)
            mark(path, False, str(body)[:200])
            failures += 1
            time.sleep(3)
    remaining = [p for p in FILES if p not in load_progress()]
    print(f"done, failures={failures}, remaining={len(remaining)}")
    sys.exit(1 if (failures or remaining) else 0)


if __name__ == "__main__":
    main()
