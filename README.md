# 🌟 F.L.A.R.E — Personal AI Operating Layer

> **F.L.A.R.E** (*Fast Localized Adaptive Routing Engine* / Personal AI Operating Layer) is an intelligent, high-availability assistant and autonomous orchestration engine inspired by Jarvis / FRIDAY. It features sub-10ms local intent classification, a dual-model execution loop, and an automatic cascading multi-provider resilience mesh.

---

## 📑 Table of Contents
- [Architecture Overview](#-architecture-overview)
- [The AI Cascade Deep Dive](#-the-ai-cascade-deep-dive)
  - [1. Sub-10ms Local Intent Classification](#1-sub-10ms-local-intent-classification)
  - [2. Dual-Model Architecture & Synthesis](#2-dual-model-architecture--synthesis)
  - [3. Multi-Provider Resilience Mesh](#3-multi-provider-resilience-mesh)
  - [4. Six-Tier Model Hierarchy](#4-six-tier-model-hierarchy)
- [Open-Source GitHub Repositories Used](#-open-source-github-repositories-used)
- [Project Directory Structure](#-project-directory-structure)
- [Quick Start Guide](#-quick-start-guide)
  - [Installation](#installation)
  - [Environment Setup](#environment-setup)
  - [Running the Interactive CLI](#running-the-interactive-cli)
  - [Running Automated Benchmarks & Tests](#running-automated-benchmarks--tests)
- [Roadmap (The 6-Phase Vision)](#-roadmap-the-6-phase-vision)

---

## 🏛️ Architecture Overview

```
                                  YOU (BOSS)
                                       │
                             🎤 💬 🖥️ (CLI / Voice / HUD)
                                       │
                                       ▼
                       F.L.A.R.E BRAIN (ai_cascade/brain.py)
                                       │
                  ┌────────────────────┴────────────────────┐
                  ▼                                         ▼
   ⚡ Stage 1: Local Intent Router            🎯 Stage 2: Automatic Complexity Routing
    • Microsecond Wake Regex (<0.1ms)          • Light / Direct: Groq / Cerebras LPUs
    • FastEmbed ONNX Embedding (<10ms)         • Heavy: Dual-Model Execution Loop
    • 0 External API Tokens Spent                       │
                                                        ▼
                                          🔄 Multi-Provider Resilience Mesh
                                           (LiteLLM Cascading Failover)
                                           Groq ──► Cerebras ──► NVIDIA NIM
                                           ──► Gemini ──► Mistral ──► Ollama (Local)
```

---

## ⚡ The AI Cascade Deep Dive

The **AI Cascade** solves the core dilemma of modern AI assistants: *How do you get instant voice-speed response times (<200ms) without sacrificing the deep reasoning capabilities of 70B–671B parameter models?*

F.L.A.R.E accomplishes this through a three-layer cascade:

### 1. Sub-10ms Local Intent Classification
- **Files**: [ai_cascade/intent/router.py](file:///c:/Users/vishal/Documents/F.L.A.R.E/ai_cascade/intent/router.py) | [ai_cascade/intent/routes.py](file:///c:/Users/vishal/Documents/F.L.A.R.E/ai_cascade/intent/routes.py)
- **Zero API Tokens & Zero External Latency**: Every incoming prompt is classified strictly on the local CPU before any network calls are initiated.
- **Two-Stage Detection**:
  1. **Regex Pattern Shortcut (<0.1ms)**: Immediate pattern match for wake phrases (`"hey flare"`, `"good morning"`, `"wake up"`).
  2. **Semantic Vector Routing (<10ms)**: Uses `semantic-router` powered by local ONNX vector embeddings (`BAAI/bge-small-en-v1.5` via `fastembed`).
- **Mapped Intents**:
  - `greeting_chitchat` ➔ `flare-fast`
  - `system_control` & `web_search` ➔ `flare-tools`
  - `coding_light` ➔ `flare-coder-light`
  - `coding_complex` ➔ `flare-coder-heavy`
  - `reasoning_light` ➔ `flare-reasoner-light`
  - `reasoning_heavy` ➔ `flare-reasoner-heavy`

---

### 2. Dual-Model Architecture & Synthesis
- **File**: [ai_cascade/brain.py](file:///c:/Users/vishal/Documents/F.L.A.R.E/ai_cascade/brain.py)
- When a task is tagged with a heavy tier (e.g. `flare-coder-heavy` or `flare-reasoner-heavy`), Flare splits execution into parallel specialized roles:
  - **Stage 2A: Front-of-House Spokesperson (Groq LPU)**: Instantly generates a witty, conversational Jarvis-style verbal acknowledgement in <200ms (*"Right away, Boss. Initializing the neural network architecture now..."*).
  - **Stage 2B: Specialist Workhorse (NVIDIA NIM / DeepSeek-R1 / Qwen 2.5 Coder)**: Concurrently generates complete, production-grade code, math, or architectural planning.
  - **Stage 2C: Synthesis**: Assembles both streams into a unified response with full telemetry.
- **Lightweight Path**: General conversations, system tools, and simple code snippets bypass the dual-model overhead and are delivered straight from ultra-low-latency LPUs.

---

### 3. Multi-Provider Resilience Mesh
- **Files**: [ai_cascade/mesh/provider_pool.py](file:///c:/Users/vishal/Documents/F.L.A.R.E/ai_cascade/mesh/provider_pool.py) | [ai_cascade/providers.yaml](file:///c:/Users/vishal/Documents/F.L.A.R.E/ai_cascade/providers.yaml)
- **Dynamic Failover & Load Balancing**: Powered by `litellm`. If the primary provider suffers a rate limit (HTTP 429), outage (HTTP 500/503), or timeout, the mesh automatically cascades down to the next candidate model in the chain within milliseconds.
- **Zero-Config Key Filtering**: Flare inspects available API keys dynamically at startup. Only providers with active keys (or local Ollama instances) enter the candidate chain. You only need **one** API key (such as Groq) to get started!

---

### 4. Six-Tier Model Hierarchy

| Tier | Purpose | Primary Engine | Fallback Sequence |
| :--- | :--- | :--- | :--- |
| **`flare-fast`** | Instant conversational banter & greetings | Groq (`gpt-oss-20b`) | Cerebras ➔ Groq (`qwen3.6-27b`) ➔ Gemini 3.5 Flash-Lite ➔ OpenRouter ➔ Local Ollama |
| **`flare-tools`** | System tools, window control, web search | Groq (`gpt-oss-120b`) | Gemini 3.5 Flash ➔ Cerebras ➔ Mistral Small ➔ OpenRouter ➔ Local Ollama |
| **`flare-coder-light`** | Regex, quick scripts, simple functions | Groq (`qwen3.6-27b`) | Cerebras (`glm-4.7`) ➔ Mistral Devstral Small ➔ Gemini 3.5 Flash ➔ Local Ollama |
| **`flare-coder-heavy`** | Full-stack architecture, concurrency, debugging | NVIDIA NIM (`deepseek-v4-pro`) | NVIDIA (`kimi-k3`) ➔ NVIDIA (`nemotron-3-ultra`) ➔ Cerebras (`glm-4.7`) ➔ Mistral Devstral ➔ Local Ollama |
| **`flare-reasoner-light`** | Conceptual explanations, logic comparisons | Groq (`qwen3.6-27b`) | Cerebras ➔ Gemini 3.5 Flash ➔ OpenRouter ➔ Local Ollama |
| **`flare-reasoner-heavy`** | Deep multi-step reasoning & system architecture | NVIDIA NIM (`deepseek-v4-pro`) | NVIDIA (`nemotron-3-ultra`) ➔ NVIDIA (`kimi-k3`) ➔ Gemini 3.1 Pro ➔ OpenRouter ➔ Cerebras ➔ Local Ollama |

---

## 🔗 Open-Source GitHub Repositories Used

The F.L.A.R.E ecosystem is built upon leading open-source libraries and frameworks:

### Core AI Cascade & Routing
- [**aurelio-labs/semantic-router**](https://github.com/aurelio-labs/semantic-router)
  *Superfast, local vector-based semantic routing for LLMs to classify prompts in milliseconds without token costs.*
- [**qdrant/fastembed**](https://github.com/qdrant/fastembed)
  *Fast, lightweight Python library by Qdrant for generating vector embeddings via ONNX runtime on CPU.*
- [**BerriAI/litellm**](https://github.com/BerriAI/litellm)
  *Universal LLM interface providing standardized OpenAI-format calls to 100+ LLM providers with automatic retry, load-balancing, and fallback logic.*
- [**pydantic/pydantic**](https://github.com/pydantic/pydantic)
  *High-performance data validation and settings management utilizing Python type hints.*
- [**theskumar/python-dotenv**](https://github.com/theskumar/python-dotenv)
  *Seamless management of environment variables and API keys from `.env` files.*
- [**yaml/pyyaml**](https://github.com/yaml/pyyaml)
  *YAML parser and emitter for configuring model provider tiers in `providers.yaml`.*

### Local Offline Model Serving
- [**ollama/ollama**](https://github.com/ollama/ollama)
  *Local execution engine for running open-weight models (Qwen, DeepSeek, Gemma) completely offline as an ultimate fallback tier.*

### Planned Audio, Vision & Hands Capabilities (Phases 2–5)
- [**SYSTRAN/faster-whisper**](https://github.com/SYSTRAN/faster-whisper)
  *High-speed local speech-to-text transcription powered by CTranslate2.*
- [**snakers4/silero-vad**](https://github.com/snakers4/silero-vad)
  *Pre-trained enterprise-grade Voice Activity Detector (VAD) with sub-millisecond precision.*
- [**rany2/edge-tts**](https://github.com/rany2/edge-tts)
  *Python module for high-fidelity neural text-to-speech generation.*
- [**microsoft/playwright-python**](https://github.com/microsoft/playwright-python)
  *Cross-browser web automation and data extraction library for autonomous browser tools.*

---

## 🗂️ Project Directory Structure

```
c:\Users\vishal\Documents\F.L.A.R.E\
├── .env.example                     # Sample configuration for API providers
├── .gitignore                       # Git ignore list
├── plan.md                          # Master architectural blueprint & 6-phase plan
├── README.md                        # Project documentation (this file)
└── ai_cascade/                      # 🧠 The Central AI Cascade Engine
    ├── brain.py                     # Master FlareBrain interface (Dual-model coordinator)
    ├── cli.py                       # Interactive terminal interface with live telemetry
    ├── config.py                    # Environment key loader and availability inspector
    ├── providers.yaml               # 2026 Model Provider Registry and fallback chains
    ├── test_brain.py                # Automated benchmark and validation suite
    ├── intent/                      # ⚡ Sub-10ms Intent Classification
    │   ├── router.py                # IntentRouter class (Regex + Semantic Router + ONNX)
    │   └── routes.py                # Route utterances & tier mapping definitions
    ├── mesh/                        # 🔄 Multi-Provider Resilience Mesh
    │   └── provider_pool.py         # ProviderMesh class (LiteLLM cascading execution)
    └── persona/                     # 🎭 Persona & System Prompt Templates
        └── flare_prompts.py         # Jarvis persona prompts & spokesperson generator
```

---

## 🚀 Quick Start Guide

### Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd F.L.A.R.E
   ```

2. **Create and activate a virtual environment**:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install the required packages**:
   ```powershell
   pip install semantic-router fastembed litellm pydantic python-dotenv pyyaml
   ```

---

### Environment Setup

1. Copy the example configuration to `.env`:
   ```powershell
   copy ai_cascade\.env.example .env
   ```

2. Add your provider API keys to `.env`. Only one provider is needed to begin:
   ```env
   GROQ_API_KEY=gsk_...
   NVIDIA_API_KEY=nvapi-...
   CEREBRAS_API_KEY=csk-...
   GEMINI_API_KEY=AIza...
   ```

---

### Running the Interactive CLI

Launch the interactive console with live telemetry:

```powershell
python ai_cascade/cli.py
```

**Commands inside the CLI**:
- `keys`: Display all currently detected and active API providers.
- `clear`: Reset the conversation buffer.
- `exit` or `quit`: Cleanly shut down Flare.

---

### Running Automated Benchmarks & Tests

Verify intent classification speeds and fallback chains:

```powershell
python ai_cascade/test_brain.py
```

This runs:
1. **Sub-10ms Intent Benchmarks**: Evaluates speed across greetings, coding queries, tools, and reasoning.
2. **Provider Mesh Verification**: Confirms candidate chain ordering across all tiers.
3. **End-to-End Execution**: Validates inference and displays telemetry metrics.

---

## 🗺️ Roadmap (The 6-Phase Vision)

As outlined in [plan.md](file:///c:/Users/vishal/Documents/F.L.A.R.E/plan.md), F.L.A.R.E evolves through six modular phases:

- **Phase 1: Core Foundation** (Brain, Task Orchestrator, Basic Tools, 3-Tier Security Gateway)
- **Phase 2: Give Flare Hands** (File Search, Safe Terminal Runner, Playwright Browser Automation)
- **Phase 3: Autonomy & Continuity** (DeepSeek Execution Harness, Pause/Resume State Vault)
- **Phase 4: Audio Pipeline** (Wake Word, Silero VAD, Faster-Whisper STT, Edge-TTS with Barge-In)
- **Phase 5: Screen Vision** (Desktop Capture, Visual Debugging, Cross-Tool Diagnostic Chaining)
- **Phase 6: Daily Companion** (Persistent Vector Memory Graph, Cron Scheduler, Morning Briefings)
