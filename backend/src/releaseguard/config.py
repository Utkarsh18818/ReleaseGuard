import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def local_environment() -> dict[str, str]:
    values = {}
    for path in (ROOT / ".local" / ".env", ROOT / ".env"):
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.removeprefix("export ").split("=", 1)
            value = value.strip()
            if len(value) > 1 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            else:
                value = value.split(" #", 1)[0].strip()
            values[key.strip()] = value
    return values


@dataclass(frozen=True)
class Settings:
    graph: str = "releaseguard_northstar"
    host: str = "127.0.0.1"
    port: int = 6380
    password: str = field(default="", repr=False)
    demo_enabled: bool = False
    gemini_api_key: str = field(default="", repr=False)
    gemini_model: str = "gemini-3.8-flash"
    username: str | None = None
    ssl: bool = False
    target: str = "local"
    queue_host: str = "127.0.0.1"
    queue_port: int = 6381
    queue_password: str = field(default="", repr=False)
    public_demo: bool = False

    @classmethod
    def load(cls):
        values = local_environment()

        def get(name, default=""):
            return os.environ.get(name, values.get(name, default))

        target = get("FALKORDB_TARGET", "local")
        if target not in {"local", "cloud"}:
            raise ValueError("FALKORDB_TARGET must be local or cloud")
        if target == "cloud":
            host, password = get("FALKORDB_CLOUD_HOST"), get("FALKORDB_CLOUD_PASSWORD")
            if not host or not password:
                raise ValueError("Cloud host/password not configured locally")
            port = int(get("FALKORDB_CLOUD_PORT", "6379"))
            username = get("FALKORDB_CLOUD_USERNAME", "falkordb")
            ssl = get("FALKORDB_CLOUD_SSL", "true").lower() == "true"
        else:
            host, port = get("FALKORDB_HOST", "127.0.0.1"), int(get("FALKORDB_PORT", "6380"))
            password, username, ssl = get("FALKORDB_PASSWORD"), None, False
        return cls(
            graph=get("FALKORDB_GRAPH", "releaseguard_northstar"),
            password=password,
            host=host,
            port=port,
            username=username,
            ssl=ssl,
            target=target,
            queue_host=get("QUEUE_HOST", "127.0.0.1"),
            queue_port=int(get("QUEUE_PORT", "6381")),
            queue_password=get("QUEUE_PASSWORD"),
            public_demo=get("RELEASEGUARD_PUBLIC_DEMO", "0") == "1",
            demo_enabled=os.environ.get("RELEASEGUARD_DEMO", "0") == "1",
            gemini_api_key=os.environ.get("GEMINI_API_KEY", values.get("GEMINI_API_KEY", "")),
            gemini_model=os.environ.get(
                "GEMINI_MODEL", values.get("GEMINI_MODEL", "gemini-3.8-flash")
            ),
        )
