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
from hands.orchestrator import HandsOrchestrator


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
        if self.generation.provider_used == "LOCAL_OS":
            return (
                f"\n--- [Flare OS Hands Telemetry] ---\n"
                f"Action:       {self.intent.source}\n"
                f"Tokens Spent: 0 (Zero-Token Fast System Path)\n"
                f"Engine:       LOCAL_OS [{self.generation.model_used}]\n"
                f"Latency:      {self.total_time_ms:.1f}ms\n"
                f"----------------------------------"
            )
        elif self.is_dual_model and self.spokesperson_generation:
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
    Coordinates:
    - Zero-Token Local OS Action Engine (Hands)
    - Sub-10ms Local Intent Classification (Semantic Router)
    - Dual-Model Execution (Groq LPU spokesperson + Specialist models)
    """

    def __init__(self):
        print(f"[FlareBrain] Initializing Flare AI Operating System for {BrainSettings.USER_NAME}...")
        self.hands = HandsOrchestrator()
        self.intent_router = IntentRouter()
        self.mesh = ProviderMesh()
        
        active = list_configured_providers()
        print(f"[FlareBrain] Active configured providers ({len(active)}): {', '.join(active) if active else 'None yet (add keys in .env)'}")
        print(f"[FlareBrain] Hands OS Automation online (22 tools registered across 3 security tiers).")
        print(f"[FlareBrain] Online and ready, {BrainSettings.USER_NAME}.\n")

    def think(
        self,
        user_input: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        force_tier: Optional[str] = None
    ) -> FlareResponse:
        """
        Process user query through Flare's intelligence cascade:
        1. STAGE 0: Zero-Token Hands Interceptor (sub-5ms local Windows OS execution)
        2. STAGE 1: Sub-10ms Local Intent Classification (semantic-router)
        3. STAGE 2: Dual-Model Execution (Groq spokesperson + specialist workhorse) or Direct Path
        """
        start_time = time.perf_counter()

        # --- STAGE 0: Zero-Token OS Hands Fast Interceptor ---
        # Direct system tasks (open brave, play music, volume, vitals, desktop, tabs, screenshots, organize, code assistant)
        # execute locally via Windows APIs with ZERO external LLM tokens spent.
        hands_result = self.hands.handle_natural_input(user_input)
        if hands_result.get("handled"):
            latency = (time.perf_counter() - start_time) * 1000
            intent_res = IntentResult(
                route="system_control",
                tier="hands-local",
                confidence=1.0,
                latency_ms=latency,
                source=f"hands_fast_path ({hands_result.get('intent', 'system_action')})"
            )
            gen_res = GenerationResult(
                content=hands_result.get("message", "Task completed."),
                tier="hands-local",
                model_used="flare-hands-v2",
                provider_used="LOCAL_OS",
                latency_ms=latency,
                ttft_ms=0.0,
                fallback_occurred=False,
                fallback_depth=0
            )
            return FlareResponse(
                reply=hands_result.get("message", "Action completed."),
                intent=intent_res,
                generation=gen_res,
                spokesperson_generation=None,
                is_dual_model=False,
                total_time_ms=latency
            )

        # Step 1: Sub-10ms Local Intent Classification
        intent = self.intent_router.classify(user_input)
        selected_tier = force_tier or intent.tier

        # Step 1.5: If classified as system_control, attempt semantic cleanup and tool dispatch
        if intent.route == "system_control":
            # Strip conversational fluff (e.g. "flare please", "could you please", "can you")
            import re
            cleaned_command = re.sub(r"^(?:flare\s+)?(?:please\s+)?(?:could\s+you\s+)?(?:can\s+you\s+)?(?:i\s+want\s+to\s+)?", "", user_input, flags=re.IGNORECASE).strip()
            retry_hands = self.hands.handle_natural_input(cleaned_command)
            if retry_hands.get("handled"):
                latency = (time.perf_counter() - start_time) * 1000
                intent_res = IntentResult(
                    route="system_control",
                    tier="hands-local",
                    confidence=intent.confidence,
                    latency_ms=latency,
                    source=f"hands_semantic_normalized ({retry_hands.get('intent')})"
                )
                gen_res = GenerationResult(
                    content=retry_hands.get("message", "Task completed."),
                    tier="hands-local",
                    model_used="flare-hands-v2",
                    provider_used="LOCAL_OS",
                    latency_ms=latency,
                    ttft_ms=0.0,
                    fallback_occurred=False,
                    fallback_depth=0
                )
                return FlareResponse(
                    reply=retry_hands.get("message", "Action completed."),
                    intent=intent_res,
                    generation=gen_res,
                    spokesperson_generation=None,
                    is_dual_model=False,
                    total_time_ms=latency
                )

            # Complex system tool request fallback via Groq with Hands Tool Schemas
            try:
                import json
                tool_schemas = self.hands.registry.export_schemas()
                tool_gen = self.mesh.generate(
                    tier="flare-tools",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are FLARE Hands tool dispatcher. Select the exact tool that satisfies the user's OS operating request. "
                                "Only call a tool if there is a direct match."
                            ),
                        },
                        {"role": "user", "content": user_input}
                    ],
                    override_kwargs={
                        "tools": tool_schemas,
                        "tool_choice": "auto",
                        "max_tokens": 200,
                    }
                )
                raw_resp = tool_gen.raw_response
                if raw_resp and hasattr(raw_resp, "choices") and raw_resp.choices:
                    choice = raw_resp.choices[0]
                    if hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
                        tc = choice.message.tool_calls[0]
                        tool_name = tc.function.name
                        tool_args = json.loads(tc.function.arguments or "{}")
                        exec_res = self.hands.registry.execute(tool_name, **tool_args)
                        status_msg = (
                            exec_res.get("data", {}).get("status")
                            or exec_res.get("status")
                            or f"Executed tool '{tool_name}'."
                        )
                        latency = (time.perf_counter() - start_time) * 1000
                        return FlareResponse(
                            reply=f"Right away. {status_msg}",
                            intent=intent,
                            generation=tool_gen,
                            spokesperson_generation=None,
                            is_dual_model=False,
                            total_time_ms=latency
                        )
            except Exception:
                pass

        # Step 2: Automatic Complexity-Aware Routing
        # Dual-model execution is reserved ONLY for heavy workloads (marked with '-heavy')
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
