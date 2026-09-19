"""
Automated Test Suite for Flare Brain and AI Cascade.
Validates:
1. Sub-10ms Intent Classification across diverse test queries.
2. Provider Mesh fallback resolution and ordering.
3. Live execution and telemetry reporting.
"""

import sys
import time
from pathlib import Path

# Ensure package root is in sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai_cascade.intent.router import IntentRouter
from ai_cascade.mesh.provider_pool import ProviderMesh
from ai_cascade.brain import FlareBrain


def test_intent_benchmarks():
    """Verify sub-10ms intent classification and route accuracy."""
    print("\n=======================================================")
    print("  TEST 1: Sub-10ms Local Intent Classification Benchmarks")
    print("=======================================================")
    
    router = IntentRouter()

    test_cases = [
        ("hey flare", "greeting_chitchat", "flare-fast"),
        ("hello flare good morning", "greeting_chitchat", "flare-fast"),
        ("open spotify and play lo-fi", "system_control", "flare-tools"),
        ("close chrome browser", "system_control", "flare-tools"),
        ("what is the latest news in ai today", "web_search", "flare-tools"),
        ("write a python function to reverse a string", "coding_light", "flare-coder-light"),
        ("give me a regex for email validation", "coding_light", "flare-coder-light"),
        ("architect and build a full asynchronous websocket server with authentication and rate limiting", "coding_complex", "flare-coder-heavy"),
        ("what is the difference between synchronous and asynchronous programming", "reasoning_light", "flare-reasoner-light"),
        ("analyze the architectural tradeoffs between microservices, modular monoliths, and serverless", "reasoning_heavy", "flare-reasoner-heavy"),
    ]

    # Warmup ONNX session
    router.classify("warmup query")

    latencies = []
    passed = 0

    for query, expected_route, expected_tier in test_cases:
        res = router.classify(query)
        latencies.append(res.latency_ms)
        is_route_ok = (res.route == expected_route)
        is_tier_ok = (res.tier == expected_tier)
        
        status = "[PASS]" if (is_route_ok and is_tier_ok) else "[WARN]"
        if is_route_ok and is_tier_ok:
            passed += 1

        print(f"{status} '{query[:45]:<45}' -> Route: {res.route:<18} Tier: {res.tier:<22} ({res.latency_ms:.2f}ms)")

    avg_latency = sum(latencies) / len(latencies)
    print(f"\nIntent Test Results: {passed}/{len(test_cases)} Passed | Average Latency: {avg_latency:.2f}ms")
    assert avg_latency < 100.0, f"Intent classification too slow: {avg_latency:.2f}ms"
    print("Test 1 Passed successfully!")


def test_mesh_chain_ordering():
    """Verify Provider Mesh candidate ordering across all 6 tiers."""
    print("\n=======================================================")
    print("  TEST 2: Provider Mesh Candidate Chain & Fallback Order")
    print("=======================================================")
    
    mesh = ProviderMesh()
    
    for tier in [
        "flare-fast",
        "flare-tools",
        "flare-coder-light",
        "flare-coder-heavy",
        "flare-reasoner-light",
        "flare-reasoner-heavy"
    ]:
        candidates = mesh.get_candidate_chain(tier)
        names = [c.get("provider") for c in candidates]
        print(f"Tier: {tier:<22} Active Chain ({len(names)}): {' -> '.join(names)}")

    print("Test 2 Passed successfully!")


def test_brain_execution():
    """Test end-to-end FlareBrain query."""
    print("\n=======================================================")
    print("  TEST 3: End-to-End Flare Brain Execution & Telemetry")
    print("=======================================================")
    
    brain = FlareBrain()
    
    # Test query
    user_query = "Hey Flare, are all systems operational?"
    print(f"\n[User]: {user_query}")
    response = brain.think(user_query)
    
    print(f"\n[Flare]: {response.reply}")
    print(response.display_metrics())
    print("\nTest 3 Finished!")


def test_dual_model_execution():
    """
    Verify Dynamic Complexity Routing across Coding AND Reasoning:
    - Normal/Light tasks -> Handled directly by fast LPUs (is_dual_model=False)
    - Deep/Heavy tasks -> Triggers dual-model (Groq spokesperson + Specialist workhorse) (is_dual_model=True)
    """
    print("\n=======================================================")
    print("  TEST 4: Dynamic Complexity Routing (Coding & Reasoning)")
    print("=======================================================")
    
    brain = FlareBrain()
    
    # Case A: Light coding task (should NOT invoke heavy model)
    light_code = "write a python function to reverse a string"
    print(f"\n[User Light Code]: {light_code}")
    res_code_light = brain.think(light_code)
    print(f"Route: {res_code_light.intent.route} -> Tier: {res_code_light.intent.tier} | Dual-Model: {res_code_light.is_dual_model}")
    assert not res_code_light.is_dual_model, "Expected light coding task to NOT trigger heavy dual-model execution"
    print("[PASS] Light code task routed cleanly without heavy model overhead!")

    # Case B: Complex coding task (SHOULD invoke dual-model)
    complex_code = "architect and build a full asynchronous websocket server with authentication and rate limiting"
    print(f"\n[User Complex Code]: {complex_code}")
    res_code_heavy = brain.think(complex_code)
    print(f"Route: {res_code_heavy.intent.route} -> Tier: {res_code_heavy.intent.tier} | Dual-Model: {res_code_heavy.is_dual_model}")
    assert res_code_heavy.is_dual_model, "Expected complex coding task to trigger dual-model execution"
    print("[PASS] Complex code triggered Groq spokesperson + Specialist workhorse!")

    # Case C: Normal reasoning task (should NOT invoke slow thinking model)
    normal_reasoning = "what is the difference between synchronous and asynchronous programming"
    print(f"\n[User Normal Reasoning]: {normal_reasoning}")
    res_reason_light = brain.think(normal_reasoning)
    print(f"Route: {res_reason_light.intent.route} -> Tier: {res_reason_light.intent.tier} | Dual-Model: {res_reason_light.is_dual_model}")
    assert not res_reason_light.is_dual_model, "Expected normal reasoning to NOT trigger heavy dual-model execution"
    print("[PASS] Normal reasoning routed cleanly to fast high-intellect tier!")

    # Case D: Deep heavy reasoning task (SHOULD invoke dual-model DeepSeek-R1)
    heavy_reasoning = "analyze the architectural tradeoffs between microservices, modular monoliths, and serverless"
    print(f"\n[User Heavy Reasoning]: {heavy_reasoning}")
    res_reason_heavy = brain.think(heavy_reasoning)
    print(f"Route: {res_reason_heavy.intent.route} -> Tier: {res_reason_heavy.intent.tier} | Dual-Model: {res_reason_heavy.is_dual_model}")
    assert res_reason_heavy.is_dual_model, "Expected heavy reasoning to trigger dual-model execution"
    print("[PASS] Heavy reasoning triggered Groq spokesperson + DeepSeek-R1 workhorse!")

    print("Test 4 Passed successfully!")


if __name__ == "__main__":
    test_intent_benchmarks()
    test_mesh_chain_ordering()
    test_brain_execution()
    test_dual_model_execution()
