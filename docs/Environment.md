# ReleaseGuard environment

Project location: `A:\ReleaseGuard`.

Prepared October 12, 2026: isolated Python 3.12.14 environment, pip 25.0.1, initialized local Git repository, copied project plan and workspace instructions. Existing Node.js 24.15.0 and npm 11.12.1 are available.

PowerShell:

```powershell
Set-Location A:\ReleaseGuard
.\.venv\Scripts\Activate.ps1
```

If activation is blocked, use `A:\ReleaseGuard\.venv\Scripts\python.exe` directly. Setup details are in `A:\ReleaseGuard\README.md`.

Historical observation, October 12: Docker Engine 29.9.0 and Compose 5.6.0 were installed in Ubuntu WSL 2. Initial authenticated graph operations and restart checks passed. These infrastructure checks do not establish application persistence or current service health. Secrets and local state are Git-ignored.

October 14 audit: Docker was stopped on arrival; documented startup restored it. The server is now healthy, authenticated connectivity passes, and GRAPH.LIST contains zero graphs. AOF is enabled and the data directory resolves to the A: bind mount. No application memory or tenant isolation exists to test. See `outputs/audit` for measurements and limitations.

Use the version-control-eligible `environment/compose.yaml` and the README setup commands for reproducible infrastructure. The older ignored `.local/compose.yaml` below is retained for continuity; do not run both configurations concurrently.

Start after a WSL shutdown:

```powershell
wsl -d Ubuntu -u root -- service docker start
wsl -d Ubuntu -u root -- docker compose -f /mnt/a/ReleaseGuard/.local/compose.yaml up -d --wait
```

Check or stop:

```powershell
wsl -d Ubuntu -u root -- docker compose -f /mnt/a/ReleaseGuard/.local/compose.yaml ps
wsl -d Ubuntu -u root -- docker compose -f /mnt/a/ReleaseGuard/.local/compose.yaml stop
```

Database password: `A:\ReleaseGuard\.local\.env`. Do not expose it in chat or commit it. No LLM API key was detected among common key variables in this shell; configure a provider locally when implementation begins.

Docker image storage remains inside the existing WSL filesystem; project files and FalkorDB persistence are on A:. Application packages and main implementation are deferred until October 15, 12:01 AM IST, per the event rule. The virtual environment depends on the bundled Codex Python runtime; recreate it with standalone Python for portability.

Future implementation should use the A: workspace and its `docs/ReleaseGuard-Project-Plan.md`, synchronizing material changes with the canonical chat plan.
