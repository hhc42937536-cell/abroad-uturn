"""
Vercel 自動部署腳本 — 出國優轉 AbroadUturn
==========================================
用 Vercel API 直接上傳檔案並部署，不需要 git 或 Vercel CLI。

使用方式：
  python deploy_vercel.py

環境變數（或直接填在下方）：
  VERCEL_TOKEN=你的_Vercel_Token
  VERCEL_PROJECT_ID=你的_Project_ID
  VERCEL_TEAM_ID=你的_Team_ID（個人帳號不需要）
"""

import os, sys, json, hashlib, time
import urllib.request, urllib.error
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ── 設定（優先讀環境變數，否則用下方預設值）──────────
VERCEL_TOKEN = os.environ.get("VERCEL_TOKEN", "")
VERCEL_PROJECT_ID = os.environ.get("VERCEL_PROJECT_ID", "")
VERCEL_TEAM_ID = os.environ.get("VERCEL_TEAM_ID", "")  # 個人帳號留空

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 要上傳的檔案清單（自動掃描 bot/ 和 data/）
def _build_file_list():
    files = [
        "api/webhook.py",
        "requirements.txt",
        "vercel.json",
    ]
    # 加入 pyproject.toml（如果存在）
    if os.path.exists(os.path.join(BASE_DIR, "pyproject.toml")):
        files.append("pyproject.toml")
    # 掃描 bot/ 目錄
    for root, dirs, fnames in os.walk(os.path.join(BASE_DIR, "bot")):
        for fname in fnames:
            if fname.endswith(".py"):
                rel = os.path.relpath(os.path.join(root, fname), BASE_DIR).replace("\\", "/")
                files.append(rel)
    # 掃描 data/ 目錄
    for root, dirs, fnames in os.walk(os.path.join(BASE_DIR, "data")):
        for fname in fnames:
            if fname.endswith(".json"):
                rel = os.path.relpath(os.path.join(root, fname), BASE_DIR).replace("\\", "/")
                files.append(rel)
    return files

DEPLOY_FILES = _build_file_list()


def api_request(method: str, path: str, body=None) -> dict:
    url = f"https://api.vercel.com{path}"
    if VERCEL_TEAM_ID:
        sep = "&" if "?" in url else "?"
        url += f"{sep}teamId={VERCEL_TEAM_ID}"

    headers = {
        "Authorization": f"Bearer {VERCEL_TOKEN}",
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        err = json.loads(e.read())
        raise RuntimeError(f"Vercel API {e.code}: {err.get('error', {}).get('message', str(e))}")


def upload_file(file_path: str) -> str:
    with open(os.path.join(BASE_DIR, file_path), "rb") as f:
        content = f.read()

    sha1 = hashlib.sha1(content).hexdigest()
    size = len(content)

    url = "https://api.vercel.com/v2/files"
    if VERCEL_TEAM_ID:
        url += f"?teamId={VERCEL_TEAM_ID}"

    headers = {
        "Authorization": f"Bearer {VERCEL_TOKEN}",
        "Content-Type": "application/octet-stream",
        "x-vercel-digest": sha1,
        "Content-Length": str(size),
    }
    req = urllib.request.Request(url, data=content, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            pass
    except urllib.error.HTTPError as e:
        if e.code != 409:
            raise
    return sha1


def deploy():
    print("=" * 50)
    print("\u2708\ufe0f \u51fa\u570b\u512a\u8f49 Vercel \u90e8\u7f72")
    print("=" * 50)

    if not VERCEL_TOKEN:
        print("\n[ERROR] \u7f3a\u5c11 VERCEL_TOKEN\uff01")
        print("\u8acb\u5230 Vercel \u2192 Account Settings \u2192 Tokens \u2192 Create Token")
        print("\u7136\u5f8c\u8a2d\u5b9a\u74b0\u5883\u8b8a\u6578\uff1a")
        print("  set VERCEL_TOKEN=\u4f60\u7684token")
        return False

    if not VERCEL_PROJECT_ID:
        print("\n[ERROR] \u7f3a\u5c11 VERCEL_PROJECT_ID\uff01")
        print("\u8acb\u5148\u5728 Vercel \u7db2\u7ad9\u5efa\u7acb\u5c08\u6848\uff0c\u7136\u5f8c\u5230 Settings \u2192 General \u2192 Project ID")
        return False

    # 1. 上傳所有檔案
    print("\n[1/3] \u4e0a\u50b3\u6a94\u6848...")
    file_meta = []
    for rel_path in DEPLOY_FILES:
        full_path = os.path.join(BASE_DIR, rel_path)
        if not os.path.exists(full_path):
            print(f"  \u8df3\u904e\uff08\u4e0d\u5b58\u5728\uff09: {rel_path}")
            continue
        try:
            sha1 = upload_file(rel_path)
            size = os.path.getsize(full_path)
            file_meta.append({"file": rel_path, "sha": sha1, "size": size})
            print(f"  \u2705 {rel_path} ({size:,} bytes)")
        except Exception as e:
            print(f"  \u274c {rel_path}: {e}")
            return False

    # 2. 建立 deployment
    print("\n[2/3] \u5efa\u7acb\u90e8\u7f72...")
    deploy_body = {
        "name": VERCEL_PROJECT_ID,
        "files": file_meta,
        "projectSettings": {
            "framework": None,
            "buildCommand": None,
            "outputDirectory": None,
        },
        "target": "production",
    }
    try:
        result = api_request("POST", f"/v13/deployments?projectId={VERCEL_PROJECT_ID}", deploy_body)
        deploy_id = result.get("id", "")
        deploy_url = result.get("url", "")
        print(f"  \u90e8\u7f72 ID: {deploy_id}")
        print(f"  URL: https://{deploy_url}")
    except Exception as e:
        print(f"  \u274c \u5efa\u7acb\u90e8\u7f72\u5931\u6557: {e}")
        return False

    # 3. 等待部署完成
    print("\n[3/3] \u7b49\u5f85\u90e8\u7f72\u5b8c\u6210...")
    for attempt in range(20):
        time.sleep(10)
        try:
            status_result = api_request("GET", f"/v13/deployments/{deploy_id}")
            state = status_result.get("readyState", "UNKNOWN")
            print(f"  \u72c0\u614b: {state} ({attempt+1}/20)...")
            if state == "READY":
                print(f"\n\u2705 \u90e8\u7f72\u6210\u529f\uff01")
                print(f"   \u7db2\u5740: https://{deploy_url}")
                print(f"   Webhook: https://{deploy_url}/api/webhook")
                return True
            elif state in ("ERROR", "CANCELED"):
                print(f"\n\u274c \u90e8\u7f72\u5931\u6557: {state}")
                return False
        except Exception as e:
            print(f"  \u67e5\u8a62\u72c0\u614b\u5931\u6557: {e}")

    print("\n\u26a0\ufe0f \u90e8\u7f72\u8d85\u6642\uff0c\u8acb\u5230 Vercel \u7db2\u7ad9\u78ba\u8a8d")
    return False


if __name__ == "__main__":
    success = deploy()
    sys.exit(0 if success else 1)
