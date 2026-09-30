"""Automated verification script for CareerMetricX test suites."""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], cwd: Path) -> int:
    print(f"\n[EXEC] {' '.join(cmd)} (cwd: {cwd})")
    res = subprocess.run(cmd, cwd=cwd, check=False)
    return res.returncode


def main():
    root = Path(__file__).resolve().parent.parent
    print("=" * 60)
    print("CareerMetricX — Test Suite Verification")
    print("=" * 60)

    # 1. Backend tests
    backend_exit = run_command([sys.executable, "-m", "pytest", "tests/", "-v"], root)
    if backend_exit != 0:
        print("[FAIL] Backend tests failed.")
        sys.exit(backend_exit)
    print("[PASS] All backend tests passed.")

    # 2. Frontend typecheck / build check
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    frontend_exit = run_command([npm_cmd, "run", "build"], root / "frontend")
    if frontend_exit != 0:
        print("[FAIL] Frontend build failed.")
        sys.exit(frontend_exit)
    print("[PASS] Frontend build succeeded.")

    print("\n" + "=" * 60)
    print("[SUCCESS] All CareerMetricX foundation verification checks passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
