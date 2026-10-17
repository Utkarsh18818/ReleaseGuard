# Configuration verification — October 15, 2026

## Verified

- Root `.env` Gemini credential was used successfully without printing it or placing it in a URL.
- First successful bounded Interactions probe: `gemini-3.8-flash`, completed response `RELEASEGUARD_OK`, 7217.8164 ms, 131 total tokens. Raw sanitized metadata: `gemini-check.json`.
- Application adapter probe: same model and expected response, 13146.1014 ms, 131 total tokens. Metadata: `gemini-adapter-check.json`. These are individual live probes, not a latency benchmark.
- A transient HTTP 503 was observed before the successful adapter probe. The adapter caps attempts at three and sanitizes provider failures.
- Configuration and real local graph tests: 27 passed, one Starlette HTTPX deprecation warning, 7.66 seconds. Evidence: `test-results.xml`.
- Free cloud subscription activation was observed as an Unsubscribe control after explicit user authorization. No paid plan selected.

## Cloud verification after user creation

The user created Free instance `instance-6q80dafwe` in AWS `ap-south-1`. Observed username is `ReleaseGuard`. Endpoint, port and username were saved in ignored `.env`. Password was supplied locally by the user and was never displayed.

- TCP connected. Verified TLS handshake timed out. Credential-free plaintext Redis PING returned NOAUTH, establishing the actual protocol. Authenticated GRAPH.LIST then succeeded with zero initial graphs (490.99 ms for one request).
- Loaded the synthetic Northstar fixture and ran the real application investigator: Blocked through `checkout -> payments -> inc-12`, with historical attempts and one Money-owned persisted blocker.
- Initial seed plus assessment took 3626.91 ms. Assessment request alone took 869.97 ms, including 868.87 ms graph client time, 6.90 ms graph server time and 1.09 ms other application time. No model call is involved. These individual samples are configuration checks, not comparative benchmarks.
- Restarted API against cloud. Health reachable, assessment replay Blocked, exactly one Money-owned task, seed replay `applied=false`. Evidence: `cloud-check.json`, `cloud-assessment.json`, `cloud-api-check.json`.
- Workspace selects cloud with explicit plaintext transport. Local graph remains preserved; switch `FALKORDB_TARGET=local` to use it.

## Pending / limitations

- Dashboard subsequently confirmed Running/Healthy with Connect enabled. Screenshot: `cloud-instance-connected.png`. This confirms provisioning completion, not sustained availability.
- Free instance plaintext transport, disabled HA/backups/autoscaling: synthetic evaluation only. Cloud restart persistence and disaster recovery are not verified.
- Native tool-using Gemini investigator and separate verifier are implemented; deterministic policy still controls release decisions. See docs/Gemini-Agent-Workflow.md for live successes, provider failures and recovery limits.

## Configuration changes

Root `.env` support, secret-free Settings representation, explicit cloud target with required host/password, configurable username/TLS, verified TLS certificates when enabled, Gemini Interactions adapter, updated health status and runtime HTTPX dependency. Configuration tests cover credentials in repr, local target preservation and required cloud settings.

Provider documentation: https://ai.google.dev/gemini-api/docs/get-started

## October 17 update

Cloud DNS temporarily failed, then recovered after the user confirmed Healthy. Existing graph and generation were preserved. The queued cloud API/worker returned a real completed Ready workflow; isolated local real-Gemini/RQ validation completed Blocked with one owner-assigned task. See docs/Durable-Investigations.md for the measured results, 48 passing tests, queue persistence check and explicit visual/recovery limits.
