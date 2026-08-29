import os
import signal
import subprocess
import tarfile
import tempfile
import threading
from pathlib import Path
from urllib.parse import quote

import requests

DATA_DIR = Path(os.getenv("LNCRAWL_DATA_PATH", "/data"))
PORT = os.getenv("PORT", "8181")
INTERVAL = max(300, int(os.getenv("BACKUP_INTERVAL_SECONDS", "900")))

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY", "")
BUCKET = os.getenv("LNCRAWL_BACKUP_BUCKET", "lncrawl-backup")
OBJECT = os.getenv("LNCRAWL_BACKUP_OBJECT", "server/data.tar.gz")

stop_event = threading.Event()


def enabled():
    return bool(SUPABASE_URL and SUPABASE_KEY and BUCKET and OBJECT)


def headers(content_type=None):
    h = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apikey": SUPABASE_KEY,
    }
    if content_type:
        h["Content-Type"] = content_type
    return h


def auth_object_url():
    return (
        f"{SUPABASE_URL}/storage/v1/object/authenticated/"
        f"{quote(BUCKET, safe='')}/{quote(OBJECT, safe='/')}"
    )


def upload_object_url():
    return (
        f"{SUPABASE_URL}/storage/v1/object/"
        f"{quote(BUCKET, safe='')}/{quote(OBJECT, safe='/')}"
    )


def safe_extract(tf, dest):
    base = dest.resolve()
    for member in tf.getmembers():
        target = (dest / member.name).resolve()
        if target != base and base not in target.parents:
            raise RuntimeError(f"Unsafe path in backup: {member.name}")
    tf.extractall(dest)


def restore():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not enabled():
        print("[komiz-backup] Supabase backup disabled; missing env vars.", flush=True)
        return

    if any(DATA_DIR.iterdir()):
        print("[komiz-backup] /data is not empty; restore skipped.", flush=True)
        return

    try:
        r = requests.get(auth_object_url(), headers=headers(), timeout=120)
        if r.status_code in (400, 404):
            print("[komiz-backup] No previous backup found; starting fresh.", flush=True)
            return
        r.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
            tmp.write(r.content)
            tmp_path = tmp.name

        try:
            with tarfile.open(tmp_path, "r:gz") as tf:
                safe_extract(tf, DATA_DIR)
            print("[komiz-backup] Backup restored into /data.", flush=True)
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    except Exception as exc:
        print(f"[komiz-backup] Restore failed, continuing fresh: {exc}", flush=True)


def make_archive(path):
    with tarfile.open(path, "w:gz") as tf:
        for child in DATA_DIR.iterdir():
            tf.add(child, arcname=child.name, recursive=True)


def backup():
    if not enabled() or not DATA_DIR.exists() or not any(DATA_DIR.iterdir()):
        return
    try:
        with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            make_archive(tmp_path)
            size = Path(tmp_path).stat().st_size
            with open(tmp_path, "rb") as f:
                r = requests.post(
                    upload_object_url(),
                    headers={
                        **headers("application/gzip"),
                        "x-upsert": "true",
                        "cache-control": "no-cache",
                    },
                    data=f,
                    timeout=300,
                )
            r.raise_for_status()
            print(f"[komiz-backup] Backup uploaded ({size} bytes).", flush=True)
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    except Exception as exc:
        print(f"[komiz-backup] Backup failed: {exc}", flush=True)


def backup_loop():
    while not stop_event.wait(INTERVAL):
        backup()


restore()

cmd = [
    "/app/.venv/bin/python",
    "-m",
    "lncrawl",
    "-ll",
    "server",
    "--port",
    PORT,
]

print(f"[komiz] Starting LNCrawl on PORT={PORT}", flush=True)
proc = subprocess.Popen(cmd)

threading.Thread(target=backup_loop, name="backup-loop", daemon=True).start()


def shutdown(signum, _frame):
    print(f"[komiz] Signal {signum}; saving backup...", flush=True)
    stop_event.set()
    backup()
    if proc.poll() is None:
        proc.terminate()


signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)

exit_code = proc.wait()
stop_event.set()
backup()
raise SystemExit(exit_code)
