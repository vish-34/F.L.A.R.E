"""
Interactive Command Line Interface for Flare AI.
Provides a rich terminal conversation loop with real-time routing telemetry.
"""

import sys
from pathlib import Path

# Ensure root directory is on sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai_cascade.brain import FlareBrain
from ai_cascade.config import BrainSettings, list_configured_providers


def print_banner():
    print("=" * 68)
    print(f"        FLARE — AI Operating System ({BrainSettings.USER_NAME})")
    print("        The Master Brain & Autonomous Hands (2026 Edition)")
    print("=" * 68)
    print("System Actions (⚡ 0 Tokens Spent | Local Windows Automation):")
    print("  'open brave' / 'open notepad'  : Launch desktop applications")
    print("  'play eminem without me'       : Direct YouTube autoplay in Brave")
    print("  'set volume to 40%' / 'mute'   : Master audio control")
    print("  'show desktop' / 'switch tabs' : Window & tab navigation")
    print("  'system health' / 'vitals'     : CPU, RAM, Disk & Battery diagnostics")
    print("  'write a python script'        : Interactive developer assistant & VS Code")
    print("  'take screenshot'              : Instant desktop screen capture")
    print("  'organize downloads'           : Group loose files into tidy subfolders")
    print("-" * 68)
    print("AI Cascade Intelligence:")
    print("  Ask anything: Coding, system architecture, deep reasoning, chitchat")
    print("-" * 68)
    print("Security: 🟢 SAFE (Auto) | 🟡 CONFIRM (Prompt) | 🔴 STRICT (Verify)")
    print("Commands: 'exit' / 'quit' | 'keys' | 'clear'")
    print("=" * 68)


def run_cli():
    print_banner()
    brain = FlareBrain()
    conversation_history = []

    while True:
        try:
            user_input = input(f"\n[{BrainSettings.USER_NAME}] > ").strip()
            
            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit"]:
                print(f"\n[Flare] Standing by, {BrainSettings.USER_NAME}. Have a good one.")
                break

            if user_input.lower() == "keys":
                active = list_configured_providers()
                print(f"\nActive Providers ({len(active)}):")
                for p in active:
                    print(f"  - {p.upper()}")
                print("Tip: Add more keys to .env anytime to unlock additional fallbacks.\n")
                continue

            if user_input.lower() == "clear":
                conversation_history.clear()
                print("\n[Flare] Conversation buffer cleared.")
                continue

            # Process query through Flare Brain
            response = brain.think(user_input, conversation_history=conversation_history)

            # Record turn
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": response.reply})

            # Print Jarvis response
            print(f"\n[Flare] {response.reply}")
            print(response.display_metrics())

        except (KeyboardInterrupt, EOFError):
            print(f"\n\n[Flare] Session interrupted. Shutting down cleanly, {BrainSettings.USER_NAME}.")
            break
        except Exception as e:
            print(f"\n[Error] Encountered unexpected exception: {e}")


if __name__ == "__main__":
    run_cli()
