"""
Verification and Test Suite for F.L.A.R.E Hands.
Tests all 3 security tiers, tool registry schemas, Windows search, and app lifecycle.
"""

import sys
import time
from pathlib import Path

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure root directory is on sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hands.file_tools.windows_search import WindowsSearch
from hands.registry import ToolRegistry
from hands.security.audit import AuditLogger
from hands.security.security_guard import SecurityGuard
from hands.security.tiers import SecurityTier, get_tier_badge
from hands.system_control.app_manager import AppManager


def test_security_tiers():
    print("\n--- Test 1: Triple-Tier Security Policies ---")

    # 1. Test SAFE tier (Auto-execution)
    safe_executed = False

    def dummy_safe_action():
        nonlocal safe_executed
        safe_executed = True
        return "SAFE_DONE"

    # Simulated callback that would deny if asked
    def strict_deny_callback(tool, tier, params, desc):
        return False

    guard = SecurityGuard(confirm_callback=strict_deny_callback)
    res_safe = guard.execute_guarded(
        tool_name="test_safe",
        tier=SecurityTier.SAFE,
        func=dummy_safe_action,
        params={},
    )
    assert res_safe["success"] is True, f"SAFE action should succeed automatically: {res_safe}"
    assert safe_executed is True, "SAFE action function should be invoked"
    print("  ✅ 🟢 SAFE tier auto-executes without confirmation prompt.")

    # 2. Test CONFIRM tier (User Denies)
    confirm_executed = False

    def dummy_confirm_action():
        nonlocal confirm_executed
        confirm_executed = True
        return "CONFIRM_DONE"

    res_denied = guard.execute_guarded(
        tool_name="test_confirm_deny",
        tier=SecurityTier.CONFIRM,
        func=dummy_confirm_action,
        params={},
    )
    assert res_denied["success"] is False, "CONFIRM action must fail if user denies"
    assert "Security Guard Blocked" in res_denied["error"]
    assert confirm_executed is False, "Function must NOT be called when denied"
    print("  ✅ 🟡 CONFIRM tier successfully blocks action when user denies.")

    # 3. Test CONFIRM tier (User Approves)
    def allow_callback(tool, tier, params, desc):
        return True

    guard_allow = SecurityGuard(confirm_callback=allow_callback)
    res_approved = guard_allow.execute_guarded(
        tool_name="test_confirm_allow",
        tier=SecurityTier.CONFIRM,
        func=dummy_confirm_action,
        params={},
    )
    assert res_approved["success"] is True, f"CONFIRM action should succeed when approved: {res_approved}"
    assert confirm_executed is True
    print("  ✅ 🟡 CONFIRM tier executes successfully upon user approval.")

    # 4. Test STRICT tier (Audit status and rejection)
    strict_executed = False

    def dummy_strict_action():
        nonlocal strict_executed
        strict_executed = True
        return "STRICT_DONE"

    res_strict_denied = guard.execute_guarded(
        tool_name="test_strict_deny",
        tier=SecurityTier.STRICT,
        func=dummy_strict_action,
        params={},
    )
    assert res_strict_denied["success"] is False
    assert strict_executed is False
    print("  ✅ 🔴 STRICT tier enforces explicit confirmation and blocks on refusal.")


def test_registry_and_schemas():
    print("\n--- Test 2: Tool Registry & LiteLLM/OpenAI Function Calling Schemas ---")
    registry = ToolRegistry(security_guard=SecurityGuard(allow_all_for_testing=True))
    tools = registry.list_tools()
    assert len(tools) >= 7, f"Expected at least 7 tools, found {len(tools)}"

    tool_names = [t["name"] for t in tools]
    expected = [
        "open_app",
        "list_running_apps",
        "close_app",
        "force_kill_app",
        "search_files",
        "find_installed_app",
        "read_file_preview",
    ]
    for exp in expected:
        assert exp in tool_names, f"Missing tool: {exp}"
    print(f"  ✅ All {len(expected)} expected tools registered with security tiers.")

    schemas = registry.export_schemas()
    assert len(schemas) == len(tools)
    for s in schemas:
        assert s["type"] == "function"
        assert "name" in s["function"]
        assert "description" in s["function"]
        assert "parameters" in s["function"]
    print("  ✅ LiteLLM / OpenAI tool calling JSON schemas generated and validated.")


def test_windows_search():
    print("\n--- Test 3: Windows Search Capabilities ---")
    # Search for plan.md in current workspace
    results = WindowsSearch.search_files(
        query="plan.md",
        search_root=str(ROOT),
        max_results=5,
    )
    assert len(results) > 0, "Failed to find plan.md in workspace!"
    first = results[0]
    assert "plan.md" in first["name"].lower()
    assert first["size_bytes"] > 0
    print(f"  ✅ Found file: {first['name']} ({first['size_kb']} KB) at {first['path']}")

    # Preview file
    preview = WindowsSearch.read_file_preview(first["path"], max_lines=5)
    assert preview["total_lines_read"] > 0
    assert len(preview["lines"]) > 0
    print(f"  ✅ File preview read {preview['total_lines_read']} lines successfully.")

    # Find installed app
    apps = WindowsSearch.find_installed_app("cmd")
    assert len(apps) > 0, "Expected to find cmd in PATH"
    print(f"  ✅ Located system app: {apps[0]['name']} via {apps[0]['source']}.")


def test_app_lifecycle():
    print("\n--- Test 4: Application Lifecycle (Launch & Close) ---")
    # Launch notepad in headless test mode
    launch_res = AppManager.open_app("notepad")
    assert launch_res["launched"] is True, f"Failed to launch notepad: {launch_res}"
    pid = launch_res.get("pid")
    print(f"  ✅ Launched Notepad (PID: {pid}). Waiting for process window...")
    time.sleep(1.0)

    # Verify process is visible
    procs = AppManager._find_processes("notepad")
    assert len(procs) > 0, "Notepad process should be detectable"
    print(f"  ✅ Verified Notepad is running ({len(procs)} instance(s) found).")

    # Gracefully close
    close_res = AppManager.close_app("notepad")
    assert close_res["closed"] is True, f"Failed to close notepad: {close_res}"
    time.sleep(0.5)
    remaining = AppManager._find_processes("notepad")
    print(f"  ✅ Gracefully closed Notepad. Remaining instances: {len(remaining)}")


def run_all_tests():
    print("=" * 65)
    print("       RUNNING F.L.A.R.E HANDS VERIFICATION SUITE")
    print("=" * 65)

    test_security_tiers()
    test_registry_and_schemas()
    test_windows_search()
    test_app_lifecycle()

    print("\n" + "=" * 65)
    print("🎉 ALL TESTS PASSED SUCCESSFULLY! F.L.A.R.E Hands is operational.")
    print("=" * 65)


if __name__ == "__main__":
    run_all_tests()
