"""Gemini Interactions client. Credentials never enter URLs, logs or results."""

import time
from dataclasses import dataclass

import httpx
from releaseguard.config import Settings


class ProviderUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class Generation:
    text: str
    model: str
    elapsed_ms: float
    usage: dict


class GeminiProvider:
    def __init__(self, settings: Settings):
        self.settings = settings

    def generate(self, prompt: str, max_output_tokens: int = 512) -> Generation:
        turn = self.interact(prompt, [], max_output_tokens=max_output_tokens)
        if turn["status"] != "completed" or not turn["text"].strip():
            raise ProviderUnavailable("Gemini did not produce completed visible output")
        return Generation(
            turn["text"], self.settings.gemini_model, turn["elapsed_ms"], turn["usage"]
        )

    def interact(self, input, tools, previous=None, max_output_tokens=2048, timeout=15):
        if not self.settings.gemini_api_key:
            raise ProviderUnavailable("Gemini key is not configured locally")
        if not 1 <= max_output_tokens <= 2048:
            raise ValueError("Output token budget must be between 1 and 2048")
        started = time.perf_counter()
        payload = {
            "model": self.settings.gemini_model,
            "input": input,
            "tools": tools,
            "generation_config": {"temperature": 0, "max_output_tokens": max_output_tokens},
        }
        # Every agent turn has a structured tool contract. AUTO also permits prose,
        # which cannot be verified or used as a findings/review submission.
        if tools:
            payload["generation_config"]["tool_choice"] = "any"
            # The bounded structured response shares its output cap with reasoning.
            # Default effort exhausted that cap with no function output in live QA.
            payload["generation_config"]["thinking_level"] = "low"
        if previous:
            payload["previous_interaction_id"] = previous
        with httpx.Client(timeout=httpx.Timeout(timeout, connect=min(5, timeout))) as client:
            response = None
            for attempt in range(1 if tools else 3):
                if time.perf_counter() - started > 45:
                    raise ProviderUnavailable("Gemini retry budget exhausted")
                try:
                    response = client.post(
                        "https://generativelanguage.googleapis.com/v1beta/interactions",
                        headers={"x-goog-api-key": self.settings.gemini_api_key},
                        json=payload,
                    )
                except httpx.HTTPError:
                    if tools or attempt == 2:
                        raise ProviderUnavailable("Gemini connection failed") from None
                    time.sleep(0.5 * (2**attempt))
                    continue
                if response.status_code not in {502, 503, 504} or attempt == 2:
                    break
                time.sleep(0.5 * (2**attempt))
        if response is None:
            raise ProviderUnavailable("Gemini connection failed")
        if response.status_code != 200:
            raise ProviderUnavailable(f"Gemini request failed (HTTP {response.status_code})")
        try:
            body = response.json()
        except ValueError:
            raise ProviderUnavailable("Gemini returned invalid JSON") from None
        text = "".join(
            part.get("text", "")
            for step in body.get("steps", [])
            if step.get("type") == "model_output"
            for part in step.get("content", [])
        )
        usage = {
            key: value
            for key, value in body.get("usage", {}).items()
            if key
            in {"total_tokens", "total_input_tokens", "total_output_tokens", "total_thought_tokens"}
        }
        calls = [
            {k: step.get(k) for k in ("id", "name", "arguments")}
            for step in body.get("steps", [])
            if step.get("type") == "function_call"
        ]
        return {
            "id": body.get("id"),
            "status": body.get("status"),
            "calls": calls,
            "text": text,
            "elapsed_ms": (time.perf_counter() - started) * 1000,
            "usage": usage,
        }
