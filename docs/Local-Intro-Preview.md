# Local introduction preview — October 18

Selected design: option 3 from the MetaMask-inspired visual exploration. The prototype has a full-width dark introduction, oversized editable HTML type, real recorded product video, full narrated player with captions, an approach section and a button into the existing review dashboard. “Product overview” returns to the introduction.

Open http://127.0.0.1:8002/ for the read-only local design preview. The user approved option 3 and requested production publication on October 18. The live deployment and its verification are recorded in Public-Deployment.md.

## Reproduce locally

```powershell
$env:RELEASEGUARD_PREVIEW_API = 'https://releaseguard-7hx8.onrender.com'
.\.venv\Scripts\python.exe -m uvicorn environment.preview:app --host 127.0.0.1 --port 8002 --no-access-log
```

The preview serves current local files and allows only GET requests to the configured backend. It never opens FalkorDB, writes graph data or starts a model investigation. To read the existing Linux API instead, use `http://127.0.0.1:8000` as the explicit preview backend. The hosted Free backend can take time to wake; the introduction and self-hosted videos work independently of backend availability.

Video preview is derived from the existing real completed Ledger review recording; it is muted, loops only when visible and pauses when the player or workspace is opened. Reduced-motion preferences start with a still poster. Full narration, captions, AI and editing disclosures remain visible in the modal. The recording is historical synthetic data, not the current graph state.

Assets: local Inter and Archivo Black fonts, the existing Lucide icons, a separately generated graph-atmosphere WebP and the project's existing recorded demo. Archivo Black's SIL OFL license is included beside the font. No frontend animation framework, CDN player, analytics or new runtime dependency was introduced.

See [design QA](../design-qa.md) for browser verification and known limits. Render remains configured for explicit manual deployments.
