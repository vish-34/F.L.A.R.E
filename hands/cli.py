"""
Interactive Command Line Interface for F.L.A.R.E Hands.
Allows manual testing of OS tools (app management, Windows search) and the 3-tier Security Guard.
"""

import os
import sys
from pathlib import Path
import json

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure project root is in sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hands.orchestrator import HandsOrchestrator
from hands.registry import ToolRegistry
from hands.security.tiers import get_tier_badge


def print_banner():
    print("=" * 68)
    print("         FLARE HANDS — Advanced Operating Tools & Orchestrator")
    print("         3-Tier Policy: 🟢 SAFE | 🟡 CONFIRM | 🔴 STRICT")
    print("=" * 68)
    print("Natural Language (Speak to Flare like a human):")
    print("  'play eminem without me'   : Open Brave and play on YouTube")
    print("  'write a python script'    : Interactive script creator & editor launcher")
    print("  'set volume to 40%'        : Adjust master audio volume")
    print("  'system health' / 'vitals' : Live CPU, RAM, Disk & Battery HUD")
    print("  'take screenshot'          : Capture desktop screen")
    print("  'organize downloads'       : Group loose files into categorized folders")
    print("  'show desktop'             : Minimize all open windows")
    print("-" * 68)
    print("Direct Tool Commands:")
    print("  apps | open <app> | close <app> | kill <app> | find <query> | audit")
    print("  tools | schemas | exit / quit")
    print("=" * 68)


def run_cli():
    print_banner()
    registry = ToolRegistry()
    orchestrator = HandsOrchestrator(registry=registry)

    while True:
        try:
            cmd_line = input("\n[Hands] > ").strip()
            if not cmd_line:
                continue

            parts = cmd_line.split(maxsplit=2)
            command = parts[0].lower()

            # 1. Check for immediate meta commands
            if command in ["exit", "quit"]:
                print("\n[Hands] Disengaging OS automation. Goodbye.")
                break

            elif command == "help":
                print_banner()
                continue

            elif command == "tools":
                print("\nRegistered Tools & Security Policies:")
                for t in registry.list_tools():
                    print(f"  {t['badge']} {t['name']:<22} : {t['description']}")
                continue

            elif command == "schemas":
                print("\nLiteLLM / OpenAI Function Calling Schemas:")
                print(json.dumps(registry.export_schemas(), indent=2))
                continue

            elif command == "audit":
                records = registry.guard.audit.get_recent(15)
                if not records:
                    print("\nNo audit records yet.")
                else:
                    print(f"\nRecent Audit Trail ({len(records)} entries):")
                    for r in records:
                        status_icon = "✅" if r.status == "EXECUTED" else ("❌" if r.status == "REJECTED" else "⚠️")
                        print(f"  [{r.timestamp}] {status_icon} {r.tier:<8} | {r.tool_name:<18} | Status: {r.status} | Time: {r.execution_time_ms}ms")
                        if r.reason:
                            print(f"      Note: {r.reason}")
                continue

            elif command == "apps":
                print("\nFetching active GUI applications...")
                result = registry.execute("list_running_apps", include_background=False)
                if result["success"]:
                    apps = result["data"]
                    print(f"\nActive Running Applications ({len(apps)}):")
                    print(f"  {'PID':<8} {'Name':<22} {'Memory (MB)':<12} {'Window Title'}")
                    print("  " + "-" * 62)
                    for a in apps[:20]:
                        title = (a['window_title'][:30] + '...') if len(a['window_title']) > 30 else a['window_title']
                        print(f"  {a['pid']:<8} {a['name']:<22} {a['memory_mb']:<12} {title}")
                else:
                    print(f"Error: {result['error']}")
                continue

            # 2. Try Natural Language Orchestrator first for all conversational phrases
            action_res = orchestrator.handle_natural_input(cmd_line)
            if action_res.get("handled"):
                status_msg = action_res.get("message", "Action completed.")
                print(f"\n✨ [Flare Hands] {status_msg}")
                res_data = action_res.get("result", {})
                if res_data and not res_data.get("success") and res_data.get("error"):
                    print(f"⚠️  Note: {res_data.get('error')}")
                continue

            # 3. Direct Command Fallbacks
            if command == "open":
                if len(parts) < 2:
                    print("Usage: open <app_name> [arguments]")
                    continue
                app_name = parts[1]
                args = parts[2] if len(parts) > 2 else None
                result = registry.execute("open_app", app_identifier=app_name, arguments=args)
                if result["success"]:
                    data = result["data"]
                    if data.get("launched"):
                        print(f"\n✅ {data.get('status', 'Launched successfully.')}")
                    else:
                        print(f"\n❌ Failed to launch: {data.get('error')}")
                else:
                    print(f"\n❌ {result['error']}")

            elif command == "close":
                if len(parts) < 2:
                    print("Usage: close <app_name_or_pid>")
                    continue
                app_target = parts[1]
                result = registry.execute("close_app", app_identifier=app_target)
                if result["success"]:
                    data = result["data"]
                    if data.get("closed"):
                        print(f"\n✅ {data.get('status', 'Closed successfully.')}")
                    else:
                        print(f"\n⚠️ {data.get('error', 'Could not close app.')}")
                else:
                    print(f"\n❌ {result['error']}")

            elif command == "kill":
                if len(parts) < 2:
                    print("Usage: kill <app_name_or_pid>")
                    continue
                app_target = parts[1]
                result = registry.execute("force_kill_app", app_identifier=app_target)
                if result["success"]:
                    data = result["data"]
                    if data.get("killed"):
                        print(f"\n✅ {data.get('status', 'Force-killed successfully.')}")
                    else:
                        print(f"\n⚠️ {data.get('error', 'Could not kill app.')}")
                else:
                    print(f"\n❌ {result['error']}")

            elif command == "find":
                if len(parts) < 2:
                    print("Usage: find <query_or_pattern> [search_root_directory]")
                    continue
                query = parts[1]
                root_dir = parts[2] if len(parts) > 2 else None
                print(f"\nSearching for '{query}'" + (f" in '{root_dir}'" if root_dir else " in user folders") + "...")
                result = registry.execute("search_files", query=query, search_root=root_dir)
                if result["success"]:
                    files = result["data"]
                    print(f"\nFound {len(files)} match(es):")
                    for f in files:
                        print(f"  📄 {f['name']} ({f['size_kb']} KB) -> {f['path']}")
                else:
                    print(f"\n❌ {result['error']}")

            elif command == "find-app":
                if len(parts) < 2:
                    print("Usage: find-app <application_name>")
                    continue
                app_target = parts[1]
                print(f"\nSearching for installed application matching '{app_target}'...")
                result = registry.execute("find_installed_app", app_name=app_target)
                if result["success"]:
                    apps = result["data"]
                    print(f"\nFound {len(apps)} match(es):")
                    for a in apps:
                        print(f"  🚀 [{a['source']}] {a['name']} -> {a['path']}")
                else:
                    print(f"\n❌ {result['error']}")

            elif command == "preview":
                if len(parts) < 2:
                    print("Usage: preview <file_path>")
                    continue
                file_target = parts[1]
                result = registry.execute("read_file_preview", file_path=file_target, max_lines=30)
                if result["success"]:
                    data = result["data"]
                    if "error" in data:
                        print(f"\n❌ {data['error']}")
                    else:
                        print(f"\nPreview of {data['file']} ({data['total_lines_read']} lines):")
                        print("-" * 50)
                        for line in data["lines"]:
                            print(line)
                        print("-" * 50)
                else:
                    print(f"\n❌ {result['error']}")

            else:
                # Attempt to dispatch as human natural language instruction
                action_res = orchestrator.handle_natural_input(cmd_line)
                if action_res.get("handled"):
                    status_msg = action_res.get("message", "Action completed.")
                    print(f"\n✨ [Flare Hands] {status_msg}")
                    res_data = action_res.get("result", {})
                    if res_data and not res_data.get("success") and res_data.get("error"):
                        print(f"⚠️  Note: {res_data.get('error')}")
                else:
                    print(f"Unrecognized command or action: '{cmd_line}'. Type 'help' to see examples.")

        except (KeyboardInterrupt, EOFError):
            print("\n[Hands] Session interrupted. Exiting.")
            break
        except Exception as e:
            print(f"\n[Hands Error] Unexpected error: {str(e)}")


if __name__ == "__main__":
    run_cli()
