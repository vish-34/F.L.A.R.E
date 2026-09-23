"""
Script Runner and Self-Healing Code Diagnostic Engine for F.L.A.R.E Hands.
Runs scripts safely, captures stdout/stderr, and diagnoses runtime tracebacks with actionable fix suggestions.
"""

import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class ScriptRunner:
    """Executes Python scripts and terminal commands safely."""

    @staticmethod
    def run_python_script(
        script_path: str,
        arguments: Optional[str] = None,
        timeout_sec: float = 30.0,
    ) -> Dict[str, Any]:
        """
        Execute a Python script with the current Python environment.
        Tier: 🟡 CONFIRM
        """
        path_obj = Path(script_path).resolve()
        if not path_obj.exists():
            return {"success": False, "error": f"Script not found at: {script_path}"}

        cmd = [sys.executable, str(path_obj)]
        if arguments:
            cmd.extend(arguments.split())

        start_time = time.perf_counter()
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                cwd=str(path_obj.parent),
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            success = res.returncode == 0
            diagnosis = None
            if not success and res.stderr:
                diagnosis = ScriptRunner.diagnose_error(str(path_obj), res.stderr)

            return {
                "success": success,
                "script": str(path_obj),
                "exit_code": res.returncode,
                "stdout": res.stdout,
                "stderr": res.stderr,
                "execution_time_ms": round(elapsed_ms, 2),
                "diagnosis": diagnosis,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "script": str(path_obj),
                "error": f"Script execution timed out after {timeout_sec} seconds.",
                "timeout": True,
            }
        except Exception as e:
            return {
                "success": False,
                "script": str(path_obj),
                "error": f"Failed to execute script: {str(e)}",
            }

    @staticmethod
    def diagnose_error(script_path: str, stderr: str) -> Dict[str, Any]:
        """
        Analyze a Python stderr traceback and extract the root cause and proposed fix.
        """
        # 1. Check for missing module
        mod_match = re.search(r"ModuleNotFoundError:\s+No module named ['\"]([^'\"]+)['\"]", stderr)
        if mod_match:
            missing_pkg = mod_match.group(1)
            return {
                "error_type": "ModuleNotFoundError",
                "missing_package": missing_pkg,
                "root_cause": f"The Python package '{missing_pkg}' is not installed in the environment.",
                "suggested_fix": f"pip install {missing_pkg}",
                "auto_fixable": True,
            }

        # 2. Check for FileNotFoundError
        fnf_match = re.search(r"FileNotFoundError:\s+\[Errno 2\]\s+No such file or directory:\s+['\"]([^'\"]+)['\"]", stderr)
        if fnf_match:
            missing_file = fnf_match.group(1)
            return {
                "error_type": "FileNotFoundError",
                "missing_path": missing_file,
                "root_cause": f"The script expected a file at '{missing_file}' which does not exist.",
                "suggested_fix": f"Verify file path or create '{missing_file}'.",
                "auto_fixable": False,
            }

        # 3. Check for Indentation / Syntax error
        if "IndentationError:" in stderr or "SyntaxError:" in stderr:
            lines = [l.strip() for l in stderr.strip().splitlines() if l.strip()]
            last_line = lines[-1] if lines else "Syntax Error"
            return {
                "error_type": "SyntaxError",
                "root_cause": last_line,
                "suggested_fix": "Inspect indentation and syntax at the reported line.",
                "auto_fixable": False,
            }

        return {
            "error_type": "RuntimeError",
            "root_cause": "Unhandled exception during script execution.",
            "suggested_fix": "Review the traceback above.",
            "auto_fixable": False,
        }
