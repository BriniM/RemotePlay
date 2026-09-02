import argparse
import statistics
import subprocess
import sys
import time
from pathlib import Path


def run_once(target: Path) -> tuple[float, int, str, str]:
    start = time.perf_counter()
    result = subprocess.run(
        [sys.executable, str(target)],
        capture_output=True,
        text=True,
    )
    elapsed = time.perf_counter() - start
    return elapsed, result.returncode, result.stdout, result.stderr


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Time how long fit_image_to_video_frame.py takes to run."
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="How many timed runs to execute (default: 1)",
    )
    args = parser.parse_args()

    if args.runs < 1:
        print("Error: --runs must be >= 1", file=sys.stderr)
        return 2

    script_path = Path(__file__).with_name("fit_image_to_video_frame.py")
    if not script_path.exists():
        print(f"Error: {script_path} not found", file=sys.stderr)
        return 2

    timings: list[float] = []
    last_code = 0
    last_stdout = ""
    last_stderr = ""

    for i in range(1, args.runs + 1):
        elapsed, code, out, err = run_once(script_path)
        timings.append(elapsed)
        last_code = code
        last_stdout = out
        last_stderr = err
        print(f"Run {i}: {elapsed:.6f} s (exit code {code})")

    print("\nSummary")
    print(f"  Runs: {args.runs}")
    print(f"  Mean: {statistics.mean(timings):.6f} s")
    print(f"  Min : {min(timings):.6f} s")
    print(f"  Max : {max(timings):.6f} s")

    if args.runs > 1:
        print(f"  Std : {statistics.pstdev(timings):.6f} s")

    if last_code != 0:
        print("\nLast run failed. stderr:")
        print(last_stderr.strip() or "<empty>")

    return last_code


if __name__ == "__main__":
    raise SystemExit(main())
