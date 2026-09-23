"""
Universal Multi-Provider Resilience Mesh for Flare (2026 Edition).
Orchestrates primary execution via Groq LPUs, Cerebras, NVIDIA NIM, and Gemini,
managing cascading failovers and prioritizing lowest Time-to-First-Token (TTFT).
"""

import time
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator
import yaml
from pydantic import BaseModel

import litellm
from litellm import completion

from ..config import ProviderKeys, BrainSettings

# Disable LiteLLM telemetry and verbose logging for clean production output
litellm.telemetry = False
litellm.drop_params = True


class GenerationResult(BaseModel):
    """Result of a generation request through the Provider Mesh."""
    content: str
    tier: str
    model_used: str
    provider_used: str
    latency_ms: float
    ttft_ms: Optional[float] = None
    fallback_occurred: bool
    fallback_depth: int
    raw_response: Optional[Any] = None

    def summary(self) -> str:
        fallback_str = f" [Fallback depth: {self.fallback_depth}]" if self.fallback_occurred else " [Primary]"
        ttft_str = f" | TTFT: {self.ttft_ms:.1f}ms" if self.ttft_ms is not None else ""
        return (
            f"Provider: {self.provider_used.upper()} ({self.model_used}){fallback_str} | "
            f"Total: {self.latency_ms:.1f}ms{ttft_str}"
        )


class ProviderMesh:
    """
    High-availability LLM Router and Cascading Failover Mesh (2026 Edition).
    Loads modernized tiers from providers.yaml and dynamically filters based on available .env keys.
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path(__file__).resolve().parent.parent / "providers.yaml"
        self.tiers_config: Dict[str, Any] = {}
        self.key_map = {
            "groq": ProviderKeys.GROQ,
            "cerebras": ProviderKeys.CEREBRAS,
            "nvidia": ProviderKeys.NVIDIA,
            "gemini": ProviderKeys.GEMINI,
            "mistral": ProviderKeys.MISTRAL,
            "openrouter": ProviderKeys.OPENROUTER,
            "cloudflare": ProviderKeys.CLOUDFLARE_TOKEN,
            "sambanova": ProviderKeys.SAMBANOVA,
            "huggingface": ProviderKeys.HF,
            "cohere": ProviderKeys.COHERE,
            "ollama": "local",  # Does not require key
        }
        self.load_config()

    def load_config(self) -> None:
        """Parse providers.yaml configuration."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            self.tiers_config = data.get("tiers", {})

    def get_key_for_provider(self, provider: str) -> Optional[str]:
        """Fetch corresponding API key from environment."""
        return self.key_map.get(provider.lower())

    def get_candidate_chain(self, tier: str) -> List[Dict[str, Any]]:
        """
        Assemble the active failover candidate list for a given tier.
        Only candidates with an available API key (or local Ollama) are included.
        Primary is always evaluated first.
        """
        tier_data = self.tiers_config.get(tier)
        if not tier_data:
            tier_data = self.tiers_config.get("flare-fast", {})

        raw_candidates = []
        if "primary" in tier_data:
            raw_candidates.append(tier_data["primary"])
        if "fallbacks" in tier_data:
            raw_candidates.extend(tier_data["fallbacks"])

        active_chain = []
        for candidate in raw_candidates:
            provider = candidate.get("provider", "").lower()
            key = self.get_key_for_provider(provider)

            if provider == "ollama":
                active_chain.append(candidate)
            elif key and key.strip():
                active_chain.append(candidate)

        return active_chain

    def generate(
        self,
        tier: str,
        messages: List[Dict[str, str]],
        stream: bool = False,
        **override_kwargs
    ) -> GenerationResult:
        """
        Execute completion with automatic cascading failover across providers.
        Captures Time-to-First-Token (TTFT) and total generation latency.
        """
        candidates = self.get_candidate_chain(tier)
        
        if not candidates:
            return GenerationResult(
                content=(
                    "Boss, no API keys are currently configured in your .env file. "
                    "Please add at least your GROQ_API_KEY to get started."
                ),
                tier=tier,
                model_used="none",
                provider_used="none",
                latency_ms=0.0,
                fallback_occurred=False,
                fallback_depth=0
            )

        errors_encountered = []
        start_total = time.perf_counter()

        for depth, candidate in enumerate(candidates):
            provider = candidate.get("provider", "unknown")
            model = candidate.get("model")
            api_base = candidate.get("api_base")
            temperature = override_kwargs.get("temperature", candidate.get("temperature", 0.7))
            max_tokens = override_kwargs.get("max_tokens", candidate.get("max_tokens", 1000))
            api_key = self.get_key_for_provider(provider)

            call_kwargs: Dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "timeout": BrainSettings.DEFAULT_TIMEOUT_SECONDS,
            }
            if "tools" in override_kwargs:
                call_kwargs["tools"] = override_kwargs["tools"]
            if "tool_choice" in override_kwargs:
                call_kwargs["tool_choice"] = override_kwargs["tool_choice"]

            if api_key and provider != "ollama":
                call_kwargs["api_key"] = api_key
            if api_base:
                call_kwargs["api_base"] = api_base
            if provider == "ollama":
                call_kwargs["api_base"] = ProviderKeys.OLLAMA_BASE
            if provider == "cloudflare":
                if ProviderKeys.CLOUDFLARE_ID:
                    call_kwargs["api_base"] = f"https://api.cloudflare.com/client/v4/accounts/{ProviderKeys.CLOUDFLARE_ID}/ai/run"
                if ProviderKeys.CLOUDFLARE_TOKEN:
                    call_kwargs["api_key"] = ProviderKeys.CLOUDFLARE_TOKEN

            try:
                candidate_start = time.perf_counter()
                
                if stream:
                    call_kwargs["stream"] = True
                    response_stream = completion(**call_kwargs)
                    first_token_time = None
                    chunks = []

                    for chunk in response_stream:
                        if first_token_time is None:
                            first_token_time = time.perf_counter()
                        delta = chunk.choices[0].delta.content if chunk.choices else ""
                        if delta:
                            chunks.append(delta)

                    content = "".join(chunks)
                    total_lat = (time.perf_counter() - candidate_start) * 1000
                    ttft = ((first_token_time - candidate_start) * 1000) if first_token_time else total_lat

                    return GenerationResult(
                        content=content.strip(),
                        tier=tier,
                        model_used=model,
                        provider_used=provider,
                        latency_ms=total_lat,
                        ttft_ms=ttft,
                        fallback_occurred=(depth > 0),
                        fallback_depth=depth,
                    )

                else:
                    response = completion(**call_kwargs)
                    latency = (time.perf_counter() - candidate_start) * 1000

                    content = ""
                    if hasattr(response, "choices") and len(response.choices) > 0:
                        content = response.choices[0].message.content or ""

                    return GenerationResult(
                        content=content.strip(),
                        tier=tier,
                        model_used=model,
                        provider_used=provider,
                        latency_ms=latency,
                        ttft_ms=None,
                        fallback_occurred=(depth > 0),
                        fallback_depth=depth,
                        raw_response=response,
                    )

            except Exception as e:
                err_msg = str(e)
                short_err = err_msg.split("\n")[0][:120]
                print(f"[Mesh Warning] Provider '{provider.upper()}' failed ({short_err}). Cascading to next candidate...")
                errors_encountered.append(f"{provider}: {short_err}")
                continue

        # If all candidates in chain failed
        total_time = (time.perf_counter() - start_total) * 1000
        error_summary = " | ".join(errors_encountered)
        return GenerationResult(
            content=(
                f"Boss, I encountered an issue connecting to the inference providers: {error_summary}. "
                "Please verify your internet connection or API quotas in .env."
            ),
            tier=tier,
            model_used="all_failed",
            provider_used="none",
            latency_ms=total_time,
            fallback_occurred=True,
            fallback_depth=len(candidates)
        )
