"""
Sub-10ms Local Intent Classification Engine for Flare.
Powered by Semantic Router with local ONNX vector embeddings.
Zero API tokens spent, zero external network dependency.
"""

import time
import re
from typing import Optional, Dict
from pydantic import BaseModel

from semantic_router import Route, SemanticRouter
from semantic_router.encoders import FastEmbedEncoder

from .routes import ROUTES, ROUTE_TIER_MAPPING
from ..config import BrainSettings


class IntentResult(BaseModel):
    """Structured classification result from the Intent Router."""
    route: str
    tier: str
    confidence: float
    latency_ms: float
    source: str

    def __str__(self) -> str:
        return (
            f"[Route: {self.route} -> Tier: {self.tier} | "
            f"Conf: {self.confidence:.2f} | Time: {self.latency_ms:.2f}ms | via: {self.source}]"
        )


class IntentRouter:
    """
    High-speed, multi-tier intent classifier for Flare.
    1. Microsecond Pattern Shortcut (for common greetings like 'hey flare', 'hi')
    2. Semantic Router with local FastEmbed ONNX encoder (<10ms)
    3. Safe fallback to default tier if query is ambiguous
    """

    def __init__(self, confidence_threshold: Optional[float] = None):
        self.threshold = confidence_threshold or BrainSettings.CONFIDENCE_THRESHOLD
        
        # 1. Microsecond pattern shortcuts for instant wake responses
        self.wake_patterns = re.compile(
            r"^(hey|hi|hello|yo|sup|good morning|good evening|good afternoon|wake up)?\s*(flare)?[\s\!\?\.]*$",
            re.IGNORECASE
        )

        # 2. Build Semantic Router routes
        self.route_objects = [
            Route(name=name, utterances=utterances)
            for name, utterances in ROUTES.items()
        ]

        # 3. Local ONNX FastEmbed Encoder (runs on CPU with 0 API costs)
        print("[IntentRouter] Initializing local ONNX FastEmbed encoder...")
        self.encoder = FastEmbedEncoder(name="BAAI/bge-small-en-v1.5")
        
        # 4. Initialize Semantic Router
        self.router = SemanticRouter(
            encoder=self.encoder,
            routes=self.route_objects,
            auto_sync="local"
        )
        print("[IntentRouter] Sub-10ms semantic routing engine ready.")

    def classify(self, text: str) -> IntentResult:
        """Classify user input into a route and tier in sub-10ms."""
        start_time = time.perf_counter()
        cleaned_text = text.strip()

        if not cleaned_text:
            return IntentResult(
                route="greeting_chitchat",
                tier=ROUTE_TIER_MAPPING["greeting_chitchat"],
                confidence=1.0,
                latency_ms=(time.perf_counter() - start_time) * 1000,
                source="empty_input_fallback"
            )

        # Stage 1: Ultra-fast regex shortcut (<0.1ms)
        if self.wake_patterns.match(cleaned_text) and len(cleaned_text) < 25:
            latency = (time.perf_counter() - start_time) * 1000
            return IntentResult(
                route="greeting_chitchat",
                tier=ROUTE_TIER_MAPPING["greeting_chitchat"],
                confidence=0.99,
                latency_ms=latency,
                source="instant_pattern"
            )

        # Stage 2: Semantic Router local embedding match (<10ms)
        try:
            match = self.router(cleaned_text)
            latency = (time.perf_counter() - start_time) * 1000

            if match and match.name:
                route_name = match.name
                # In semantic-router, match.similarity or confidence score
                score = getattr(match, "similarity_score", None) or getattr(match, "score", None) or 0.85
                tier = ROUTE_TIER_MAPPING.get(route_name, "flare-fast")

                return IntentResult(
                    route=route_name,
                    tier=tier,
                    confidence=float(score),
                    latency_ms=latency,
                    source="semantic_router"
                )

        except Exception as e:
            print(f"[WARN] [IntentRouter] Semantic router lookup notice: {e}")

        # Stage 3: Graceful fallback
        latency = (time.perf_counter() - start_time) * 1000
        return IntentResult(
            route="greeting_chitchat",
            tier="flare-fast",
            confidence=0.50,
            latency_ms=latency,
            source="default_fallback"
        )
