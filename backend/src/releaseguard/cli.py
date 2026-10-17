import argparse
import json
from uuid import uuid4

from releaseguard.adapters.falkordb import GraphStore
from releaseguard.adapters.gemini import GeminiProvider
from releaseguard.application.agent_investigation import AgentInvestigator
from releaseguard.application.ingestion import load_dataset, seed
from releaseguard.application.investigation import Investigator
from releaseguard.application.mutations import apply_event
from releaseguard.application.recovery import recover
from releaseguard.config import ROOT, Settings
from releaseguard.domain.models import DemoEvent


def main():
    parser = argparse.ArgumentParser(description="ReleaseGuard deterministic graph core")
    parser.add_argument(
        "command", choices=["seed", "assess", "latest", "event", "recover", "agent", "agent-latest"]
    )
    parser.add_argument("--release", default="checkout-v2.4")
    parser.add_argument("--event-json")
    parser.add_argument("--request-key", default=None)
    parser.add_argument("--resume-verifier", action="store_true")
    args = parser.parse_args()
    store = GraphStore(Settings.load())
    if args.command == "agent":
        result = AgentInvestigator(store, GeminiProvider(store.settings)).investigate(
            args.release, args.request_key or str(uuid4()), resume_verifier=args.resume_verifier
        )
    elif args.command == "agent-latest":
        result = AgentInvestigator(store, GeminiProvider(store.settings)).latest(args.release)
    elif args.command == "seed":
        result = {"applied": seed(store, load_dataset(ROOT / "fixtures" / "northstar.json"))}
    elif args.command == "recover":
        result = recover(store)
    elif args.command == "event":
        result = apply_event(store, DemoEvent.model_validate_json(args.event_json))
    elif args.command == "latest":
        result = Investigator(store).latest(args.release)
    else:
        result = Investigator(store).assess(args.release, str(uuid4()))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
