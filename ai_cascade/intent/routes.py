"""
Route Definitions for Flare's Local Intent Classification.
Provides rich, curated sample utterances across all operational domains.
"""

from typing import List, Dict

ROUTES: Dict[str, List[str]] = {
    "greeting_chitchat": [
        "hey flare",
        "hi flare",
        "hello",
        "good morning flare",
        "good evening",
        "sup flare",
        "are you there flare",
        "wake up flare",
        "who are you",
        "what can you do",
        "tell me a joke",
        "how are you doing today",
        "thanks flare",
        "thank you",
        "what is your name",
        "you awake",
        "flare you with me",
    ],
    "system_control": [
        "open brave",
        "launch brave",
        "open spotify",
        "close chrome",
        "launch notepad",
        "open visual studio code",
        "open vs code",
        "close all windows",
        "turn up the volume",
        "turn down the volume",
        "mute the computer",
        "unmute",
        "set volume to 50 percent",
        "set volume to 40",
        "take a screenshot",
        "capture my screen",
        "minimize this window",
        "show desktop",
        "minimize the screen",
        "switch tabs",
        "next tab",
        "close tab",
        "switch window",
        "how is my pc health",
        "system vitals",
        "organize downloads",
        "clean desktop",
        "play eminem without me",
        "play music on youtube",
        "play loser by dino james",
        "play songs on youtube",
        "pause the music",
        "next song",
        "write a python script",
        "write python code",
        "write me code to download youtube video",
        "code",
        "script",
        "open file explorer",
        "open task manager",
        "restart my computer",
        "shutdown my computer",
    ],
    "web_search": [
        "what is the latest news in ai today",
        "search the web for the newest deepseek models",
        "who won the match yesterday",
        "what is the current price of bitcoin",
        "lookup the weather forecast for tomorrow",
        "search google for latest tech announcements",
        "check the stock market today",
        "find recent articles about quantum computing",
        "what happened in the world today",
        "search duckduckgo for python documentation",
    ],
    "coding_light": [
        "write a python function to reverse a string",
        "write a simple script to add two numbers",
        "give me a regex for email validation",
        "how do i print in python",
        "syntax for for-loop in javascript",
        "quick command to find files on linux",
        "convert this string to uppercase in python",
        "how to read a text file in python line by line",
        "write a quick function to check if number is even",
        "simple bash script to create a folder if not exists",
    ],
    "coding_complex": [
        "architect and build a full asynchronous websocket server with authentication and rate limiting",
        "debug this memory leak and race condition in my multi-threaded python backend",
        "write a full microservice with database migrations, jwt auth, and integration tests",
        "implement a custom neural network from scratch in pytorch with custom backward pass",
        "refactor this 500-line legacy monolithic class into clean domain-driven design",
        "implement a distributed b-tree indexing structure with concurrency control",
        "debug why my distributed celery workers are deadlocking under high redis load",
    ],
    "reasoning_light": [
        "what is the difference between synchronous and asynchronous programming",
        "explain recursion simply in plain english",
        "why is water boiling at lower temperatures at high altitudes",
        "compare list vs tuple in python with pros and cons",
        "what is the difference between http and https",
        "explain how transformers and attention mechanisms work simply",
        "why do leaves change color in autumn",
        "how does compound interest work with an example",
        "summarize the main differences between sql and nosql databases",
        "explain the difference between process and thread in operating systems",
    ],
    "reasoning_heavy": [
        "analyze the architectural tradeoffs between microservices, modular monoliths, and serverless",
        "solve this complex mathematical logic puzzle step by step showing all rigorous proofs",
        "conduct an in-depth failure mode and effects analysis for an autonomous aerospace control system",
        "evaluate byzantine fault tolerance and network partition handling in raft vs paxos",
        "break down a 6-month enterprise cloud migration plan with risk mitigation matrices",
    ],
}

# Route metadata mapping to LiteLLM model tier
# Automatic Complexity Routing:
# Light tasks -> Fast, zero-overhead models (Groq / Cerebras)
# Heavy tasks -> Dual-Model execution (Groq spokesperson + NVIDIA DeepSeek/Qwen Coder)
ROUTE_TIER_MAPPING: Dict[str, str] = {
    "greeting_chitchat": "flare-fast",             # Fast conversational banter (Groq)
    "system_control": "flare-tools",               # Fast tool caller
    "web_search": "flare-tools",                   # Fast tool caller / search
    "reasoning_light": "flare-reasoner-light",     # High-intellect direct reasoning (Groq 70B, no slow <think> lag)
    "reasoning_heavy": "flare-reasoner-heavy",     # Deep reasoning workhorse (NVIDIA DeepSeek-R1 full)
    "coding_light": "flare-coder-light",           # Fast direct code (Groq Llama 70B/8B, no heavy model)
    "coding_complex": "flare-coder-heavy",         # Heavy coding specialist (NVIDIA Qwen Coder 32B / DeepSeek)
}
