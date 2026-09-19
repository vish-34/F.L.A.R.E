"""
AI Cascade Configuration & Environment Manager (2026 Edition)
Loads and validates API keys from .env for the modernized 2026 provider lineup.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Search for .env in current directory, parent directory, and workspace root
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

ENV_PATHS = [
    CURRENT_DIR / ".env",
    PROJECT_ROOT / ".env",
    Path.cwd() / ".env"
]

for env_path in ENV_PATHS:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)
        break
else:
    load_dotenv()


class ProviderKeys:
    """Central store for all configured provider API keys."""
    
    # ⚡ Primary & Ultra-Fast Inference
    GROQ: Optional[str] = os.getenv("GROQ_API_KEY")
    CEREBRAS: Optional[str] = os.getenv("CEREBRAS_API_KEY")
    
    # 🧠 Flagship Reasoning & Coding Workhorses
    NVIDIA: Optional[str] = os.getenv("NVIDIA_API_KEY")
    GEMINI: Optional[str] = os.getenv("GEMINI_API_KEY")
    MISTRAL: Optional[str] = os.getenv("MISTRAL_API_KEY")
    
    # 🔀 Free Model Aggregators & Edge
    OPENROUTER: Optional[str] = os.getenv("OPENROUTER_API_KEY")
    CLOUDFLARE_ID: Optional[str] = os.getenv("CLOUDFLARE_ACCOUNT_ID")
    CLOUDFLARE_TOKEN: Optional[str] = os.getenv("CLOUDFLARE_API_TOKEN")
    
    # 🌐 Secondary Fallbacks
    SAMBANOVA: Optional[str] = os.getenv("SAMBANOVA_API_KEY")
    HF: Optional[str] = os.getenv("HF_TOKEN")
    COHERE: Optional[str] = os.getenv("COHERE_API_KEY")
    
    # 🏠 Local Offline Fallback
    OLLAMA_BASE: str = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")


class BrainSettings:
    """Core settings for Flare Brain and Intent Router."""
    ASSISTANT_NAME: str = os.getenv("FLARE_ASSISTANT_NAME", "Flare")
    USER_NAME: str = os.getenv("FLARE_USER_NAME", "Boss")
    CONFIDENCE_THRESHOLD: float = float(os.getenv("FLARE_INTENT_CONFIDENCE_THRESHOLD", "0.65"))
    DEFAULT_TIMEOUT_SECONDS: float = float(os.getenv("FLARE_DEFAULT_TIMEOUT", "15.0"))
    MAX_FALLBACK_RETRIES: int = int(os.getenv("FLARE_MAX_RETRIES", "3"))


def get_active_providers() -> Dict[str, bool]:
    """Returns a dictionary mapping provider name to availability."""
    return {
        "groq": bool(ProviderKeys.GROQ and ProviderKeys.GROQ.strip()),
        "cerebras": bool(ProviderKeys.CEREBRAS and ProviderKeys.CEREBRAS.strip()),
        "nvidia": bool(ProviderKeys.NVIDIA and ProviderKeys.NVIDIA.strip()),
        "gemini": bool(ProviderKeys.GEMINI and ProviderKeys.GEMINI.strip()),
        "mistral": bool(ProviderKeys.MISTRAL and ProviderKeys.MISTRAL.strip()),
        "openrouter": bool(ProviderKeys.OPENROUTER and ProviderKeys.OPENROUTER.strip()),
        "cloudflare": bool(ProviderKeys.CLOUDFLARE_TOKEN and ProviderKeys.CLOUDFLARE_TOKEN.strip()),
        "sambanova": bool(ProviderKeys.SAMBANOVA and ProviderKeys.SAMBANOVA.strip()),
        "huggingface": bool(ProviderKeys.HF and ProviderKeys.HF.strip()),
        "cohere": bool(ProviderKeys.COHERE and ProviderKeys.COHERE.strip()),
        "ollama": True,  # Always available as an offline candidate
    }


def list_configured_providers() -> List[str]:
    """Returns a list of providers that have an API key configured."""
    active = get_active_providers()
    return [name for name, is_active in active.items() if is_active and name != "ollama"]
