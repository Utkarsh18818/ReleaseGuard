import hashlib
import json
import re
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from falkordb import FalkorDB
from releaseguard.config import ROOT, Settings

_locks: dict[str, threading.RLock] = {}
_registry_lock = threading.Lock()
_held_locks = threading.local()


class GraphStore:
    """Single-host serialized access. External writers/HA are unsupported."""

    def __init__(self, settings: Settings, lock_directory: Path | None = None):
        if not re.fullmatch(r"releaseguard_[a-zA-Z0-9_]+", settings.graph):
            raise ValueError("Graph is not an allowed ReleaseGuard graph")
        self.name = settings.graph
        self.settings = settings
        self._client = None
        self._graph = None
        self.timings: list[dict] = []
        directory = lock_directory or ROOT / ".local" / "locks"
        directory.mkdir(parents=True, exist_ok=True)
        self.lock_path = directory / (hashlib.sha256(self.name.encode()).hexdigest() + ".lock")
        with _registry_lock:
            self.lock = _locks.setdefault(str(self.lock_path), threading.RLock())

    @property
    def client(self):
        if self._client is None:
            from redis.backoff import NoBackoff
            from redis.retry import Retry

            self._client = FalkorDB(
                host=self.settings.host,
                port=self.settings.port,
                password=self.settings.password,
                username=self.settings.username,
                ssl=self.settings.ssl,
                ssl_cert_reqs="required",
                ssl_check_hostname=self.settings.ssl,
                socket_timeout=5,
                socket_connect_timeout=2,
                max_connections=8,
                retry=Retry(NoBackoff(), 0),
            )
        return self._client

    @property
    def graph(self):
        if self._graph is None:
            self._graph = self.client.select_graph(self.name)
        return self._graph

    @contextmanager
    def serialized(self):
        # API reads, assessments and mutations share the same lock, including CLI processes.
        with self.lock:
            held = getattr(_held_locks, "paths", None)
            if held is None:
                held = _held_locks.paths = set()
            if str(self.lock_path) in held:
                yield
                return
            with self.lock_path.open("a+b") as file:
                file.seek(0, 2)
                if file.tell() == 0:
                    file.write(b"0")
                    file.flush()
                file.seek(0)
                if __import__("os").name == "nt":
                    import msvcrt

                    msvcrt.locking(file.fileno(), msvcrt.LK_LOCK, 1)
                else:
                    import fcntl

                    fcntl.flock(file.fileno(), fcntl.LOCK_EX)
                held.add(str(self.lock_path))
                try:
                    yield
                finally:
                    held.remove(str(self.lock_path))
                    file.seek(0)
                    if __import__("os").name == "nt":
                        msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        fcntl.flock(file.fileno(), fcntl.LOCK_UN)

    def _query(self, query, params, write):
        start = time.perf_counter()
        result = (self.graph.query if write else self.graph.ro_query)(
            query, params or {}, timeout=2000
        )
        self.timings.append(
            {
                "kind": "write" if write else "read",
                "client_ms": (time.perf_counter() - start) * 1000,
                "server_ms": float(result.run_time_ms),
                "rows": len(result.result_set),
            }
        )
        return result.result_set

    def read(self, query, params=None):
        return self._query(query, params, False)

    def write(self, query, params=None):
        return self._query(query, params, True)

    def initialize(self):
        self.write(
            "MERGE (s:DomainState {id:'domain'}) ON CREATE SET s.revision=0, "
            "s.generation=$generation, s.dirty=false RETURN s.revision",
            {"generation": str(uuid4())},
        )

    def state(self):
        rows = self.read(
            "MATCH (s:DomainState {id:'domain'}) RETURN s.revision,s.generation,s.dirty"
        )
        if not rows:
            raise ValueError("Graph not initialized; run seed")
        return dict(zip(("revision", "generation", "dirty"), rows[0], strict=True))

    def journal(self, key: str, payload: dict, apply):
        """Caller must hold serialized(). Dirty remains durable if apply raises."""
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        checksum = hashlib.sha256(encoded.encode()).hexdigest()
        existing = self.read("MATCH (c:Command {id:$key}) RETURN c.checksum,c.status", {"key": key})
        if existing and existing[0][0] != checksum:
            raise ValueError("Idempotency key conflicts with a different payload")
        if existing and existing[0][1] == "completed":
            state = self.state()
            if state["dirty"]:
                pending = self.read("MATCH (s:DomainState {id:'domain'}) RETURN s.command_id")
                if pending[0][0] == key:
                    self.write(
                        "MATCH (s:DomainState {id:'domain'}) SET s.dirty=false,s.command_id=''"
                    )
            return False
        state = self.state()
        if state["dirty"]:
            pending = self.read("MATCH (s:DomainState {id:'domain'}) RETURN s.command_id")
            if pending[0][0] != key:
                raise ValueError("Pending mutation must be recovered first")
        target = state["revision"] + 1
        self.write(
            "MATCH (s:DomainState {id:'domain'}) MERGE (c:Command {id:$key}) "
            "ON CREATE SET c.target_revision=$target "
            "SET c.checksum=$checksum,c.payload=$payload,c.status='pending', "
            "s.dirty=true,s.command_id=$key RETURN c.target_revision",
            {"key": key, "checksum": checksum, "payload": encoded, "target": target},
        )
        apply()
        self.write(
            "MATCH (s:DomainState {id:'domain'}),(c:Command {id:$key}) "
            "SET s.revision=c.target_revision,c.status='completed' RETURN s.revision",
            {"key": key},
        )
        # Clearing dirty is intentionally the last command, not an assumed multi-query transaction.
        self.write("MATCH (s:DomainState {id:'domain'}) SET s.dirty=false,s.command_id=''", {})
        return True
