"""Single-container evaluation deployment; graph is canonical, Redis is replaceable transport."""

import os
import secrets
import signal
import subprocess
import sys
import time

from redis import Redis
from redis.exceptions import ConnectionError

children = []


def stop(signum=None, frame=None):
    for child in reversed(children):
        if child.poll() is None:
            child.terminate()
    deadline = time.monotonic() + 15
    for child in children:
        try:
            child.wait(timeout=max(0.1, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            child.kill()


def main():
    signal.signal(signal.SIGTERM, lambda *args: sys.exit(0))
    signal.signal(signal.SIGINT, lambda *args: sys.exit(0))
    os.environ.update(
        QUEUE_HOST="127.0.0.1", QUEUE_PORT="6379", QUEUE_PASSWORD=secrets.token_urlsafe(32),
        RELEASEGUARD_PUBLIC_DEMO="1", RELEASEGUARD_DEMO="0",
    )
    # New code revisions get separate graphs, avoiding overlapping deployment writers.
    revision = os.environ.get("RENDER_GIT_COMMIT", "localverify")[:12]
    if not revision.isalnum():
        raise ValueError("Invalid hosting revision")
    os.environ["FALKORDB_GRAPH"] = "releaseguard_public_" + revision
    children.append(subprocess.Popen([
        "redis-server", "--bind", "127.0.0.1", "--port", "6379", "--save", "",
        "--appendonly", "no", "--maxmemory", "64mb", "--maxmemory-policy", "noeviction",
        "--requirepass", os.environ["QUEUE_PASSWORD"],
    ], stdout=subprocess.DEVNULL))
    queue = Redis(host="127.0.0.1", port=6379, password=os.environ["QUEUE_PASSWORD"])
    for attempt in range(50):
        try:
            if queue.ping():
                break
        except ConnectionError:
            pass
        time.sleep(0.1)
    from releaseguard.adapters.falkordb import GraphStore
    from releaseguard.application.ingestion import load_dataset, seed
    from releaseguard.application.investigation import Investigator
    from releaseguard.config import ROOT, Settings

    store = GraphStore(Settings.load())
    seed(store, load_dataset(ROOT / "fixtures" / "northstar.json"))
    if Investigator(store).latest("checkout-v2.4") is None:
        Investigator(store).assess("checkout-v2.4", "hosted-initial-policy")
    for command in (
        [sys.executable, "-m", "releaseguard.worker"],
        [sys.executable, "-m", "releaseguard.worker", "--reconcile-only"],
        [sys.executable, "-m", "uvicorn", "releaseguard.api:app", "--host", "0.0.0.0",
         "--port", os.environ.get("PORT", "10000"), "--no-access-log"],
    ):
        children.append(subprocess.Popen(command))
    while all(child.poll() is None for child in children):
        time.sleep(1)
    raise RuntimeError("A hosted process exited; restarting the service is required")


if __name__ == "__main__":
    try:
        main()
    finally:
        stop()
