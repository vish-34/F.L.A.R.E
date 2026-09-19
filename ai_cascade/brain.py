"""
Master Flare Brain Interface with Dual-Model Architecture.
Coordinates:
1. Sub-10ms Intent Classification (semantic-router)
2. Front-of-House Conversational Spokesperson (Groq LPU: snappy Jarvis banter)
3. Backend Specialist Workhorse (NVIDIA NIM DeepSeek-R1 / Qwen 2.5 Coder 32B for actual work)
"""

import time
from typing import List, Dict, Optional, Any
from pydantic import BaseModel

from .config import BrainSettings, list_configured_providers
from .intent.router import IntentRouter, IntentResult
from .persona.flare_prompts import get_system_prompt, get_spokesperson_prompt
from .mesh.provider_pool import ProviderMesh, GenerationResult


class FlareResponse(BaseModel):
    """Complete response structure from Flare's Brain."""
    reply: str
    intent: IntentResult
    generation: GenerationResult
    spokesperson_generation: Optional[GenerationResult] = None
    is_dual_model: bool = False
    total_time_ms: float

    def display_metrics(self) -> str:
        """Format metrics for CLI or HUD display."""
        if self.is_dual_model and self.spokesperson_generation:
            spoke = self.spokesperson_generation
            work = self.generation
            return (
                f"\n--- [Flare Dual-Model Telemetry] ---\n"
                f"Routing:       {self.intent.route} -> {self.intent.tier} ({self.intent.latency_ms:.2f}ms via {self.intent.source})\n"
                f"Spokesperson:  {spoke.provider_used.upper()} [{spoke.model_used}] ({spoke.latency_ms:.1f}ms)\n"
                f"Workhorse:     {work.provider_used.upper()} [{work.model_used}] ({work.latency_ms:.1f}ms)\n"
                f"Status:        {'CASCADE FAILOVER (Depth: ' + str(work.fallback_depth) + ')' if work.fallback_occurred else 'PRIMARY WORKHORSE HIT'}\n"
                f"Total Time:    {self.total_time_ms:.1f}ms\n"
                f"------------------------------------"
            )
        else:
            return (
                f"\n--- [Flare Telemetry] ---\n"
                f"Routing:  {self.intent.route} -> {self.intent.tier} ({self.intent.latency_ms:.2f}ms via {self.intent.source})\n"
                f"Engine:   {self.generation.provider_used.upper()} [{self.generation.model_used}]\n"
                f"Status:   {'CASCADE FAILOVER (Depth: ' + str(self.generation.fallback_depth) + ')' if self.generation.fallback_occurred else 'PRIMARY HIT (Groq LPU)'}\n"
                f"Latency:  Intent: {self.intent.latency_ms:.1f}ms | Inference: {self.generation.latency_ms:.1f}ms | Total: {self.total_time_ms:.1f}ms\n"
                f"-------------------------"
            )


class FlareBrain:
    """
    The central intelligence unit for Flare.
    Features Dual-Model Execution:
    - Groq handles the conversation and verbal acknowledgment (<200ms)
    - Specialist models (NVIDIA Qwen Coder, DeepSeek-R1) execute code & deep logic in backend
    """

    def __init__(self):
        print(f"[FlareBrain] Initializing Flare AI Operating System for {BrainSettings.USER_NAME}...")
        self.intent_router = IntentRouter()
        self.mesh = ProviderMesh()
        
        active = list_configured_providers()
        print(f"[FlareBrain] Active configured providers ({len(active)}): {', '.join(active) if active else 'None yet (add keys in .env)'}")
        print(f"[FlareBrain] Online and ready, {BrainSettings.USER_NAME}.\n")

    def think(
        self,
        user_input: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        force_tier: Optional[str] = None
    ) -> FlareResponse:
        """
        Process user query through Flare's two-stage brain:
        1. Classify intent locally in sub-10ms (semantic-router)
        2. If task requires deep work (coding/reasoning):
           - Stage 2A: Front-of-house spokesperson (Groq) acknowledges in <200ms
           - Stage 2B: Specialist workhorse (NVIDIA Coder/DeepSeek) drafts code/reasoning
           - Stage 2C: Return synthesised Jarvis reply
        3. If general chat/system tools:
           - Direct execution via Groq / primary tool tier
        """
        start_time = time.perf_counter()

        # Step 1: Sub-10ms Local Intent Classification
        intent = self.intent_router.classify(user_input)
        selected_tier = force_tier or intent.tier

        # Step 2: Automatic Complexity-Aware Routing
        # Dual-model execution is reserved ONLY for heavy workloads (marked with '-heavy')
        # Simple/light coding or reasoning is routed directly to fast LPUs without wasting heavy model quotas
        is_heavy_task = selected_tier.endswith("-heavy")

        if is_heavy_task:
            task_type = "code" if "coder" in selected_tier else "analysis"
            
            # --- STAGE 2A: Front-of-House Spokesperson (Groq LPU) ---
            spokesperson_prompt = get_spokesperson_prompt(user_input, task_type=task_type)
            spoke_messages = [
                {"role": "system", "content": spokesperson_prompt},
                {"role": "user", "content": user_input}
            ]
            spoke_gen = self.mesh.generate(
                tier="flare-fast",  # Always powered by ultra-fast Groq
                messages=spoke_messages,
                max_tokens=80,
                temperature=0.7
            )

            # --- STAGE 2B: Specialist Workhorse (NVIDIA Qwen Coder / DeepSeek-R1) ---
            work_prompt = get_system_prompt(selected_tier)
            work_messages = [{"role": "system", "content": work_prompt}]
            if conversation_history:
                work_messages.extend(conversation_history[-6:])
            work_messages.append({"role": "user", "content": user_input})

            work_gen = self.mesh.generate(tier=selected_tier, messages=work_messages)

            # --- STAGE 2C: Synthesis ---
            combined_reply = f"{spoke_gen.content.strip()}\n\n{work_gen.content.strip()}".strip()
            total_latency = (time.perf_counter() - start_time) * 1000

            return FlareResponse(
                reply=combined_reply,
                intent=intent,
                generation=work_gen,
                spokesperson_generation=spoke_gen,
                is_dual_model=True,
                total_time_ms=total_latency
            )

        else:
            # --- Standard Direct Path (Greetings, Chitchat, Fast System Tools) ---
            system_prompt = get_system_prompt(selected_tier)
            messages = [{"role": "system", "content": system_prompt}]
            if conversation_history:
                messages.extend(conversation_history[-6:])
            messages.append({"role": "user", "content": user_input})

            generation = self.mesh.generate(tier=selected_tier, messages=messages)
            total_latency = (time.perf_counter() - start_time) * 1000

            return FlareResponse(
                reply=generation.content,
                intent=intent,
                generation=generation,
                spokesperson_generation=None,
                is_dual_model=False,
                total_time_ms=total_latency
            )
