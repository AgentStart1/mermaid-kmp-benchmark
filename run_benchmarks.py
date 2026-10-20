"""Build, preflight, run isolated JMH forks, and generate an HTML report."""
import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def run(command, **kwargs):
    print("Running:", " ".join(map(str, command)), flush=True)
    return subprocess.run(command, cwd=ROOT, check=True, **kwargs)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=["smoke", "standard"], default="standard")
    parser.add_argument("--prepared", action="store_true", help="Use already verified source checkouts")
    args = parser.parse_args()
    if not args.prepared:
        run([sys.executable, "prepare.py"])
    gradle = str(ROOT / ("gradlew.bat" if os.name == "nt" else "gradlew"))
    run([gradle, ":bench:installDist", "--console=plain"])
    launcher = ROOT / "bench/build/install/bench/bin" / ("bench.bat" if os.name == "nt" else "bench")
    results = ROOT / "results"
    results.mkdir(exist_ok=True)
    run([str(launcher), "preflight"])
    preflight = json.loads((results / "preflight.json").read_text())
    settings = dict(forks=2, warmup=5, iterations=8, seconds=1) if args.profile == "standard" else dict(forks=1, warmup=2, iterations=3, seconds=1)
    metadata = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "profile": args.profile, "settings": settings,
        "os": platform.platform(), "architecture": platform.machine(), "cpu": platform.processor(),
        "toolchain": {"kotlin": "2.3.21", "coroutines": "1.11.0", "rust_kmp": "0.0.1-alpha5 (published JVM binary)"},
        "java": subprocess.check_output(["java", "-version"], stderr=subprocess.STDOUT, text=True),
        "libraries": json.loads((ROOT / "libraries.lock.json").read_text()),
        "inputs": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT / "test-data").glob("*.mmd"))},
        "failures": [],
    }
    combined = []
    # Each valid cell has its own process, timeout, log and result. Partial failures remain visible.
    for row in preflight:
        if row["status"] != "ok":
            continue
        name = row["operation"].replace(":", "-") + "-" + row["caseName"]
        output = results / (name + ".json")
        output.unlink(missing_ok=True)
        command = [str(launcher), "bench.DiagramBenchmark.measure", "-p", "operation=" + row["operation"], "-p", "caseName=" + row["caseName"],
                   "-f", str(settings["forks"]), "-wi", str(settings["warmup"]), "-i", str(settings["iterations"]),
                   "-w", "1s", "-r", "1s", "-rf", "json", "-rff", str(output.relative_to(ROOT)), "-foe", "true", "-prof", "gc"]
        try:
            with (results / (name + ".log")).open("w", encoding="utf-8") as log:
                run(command, stdout=log, stderr=subprocess.STDOUT, timeout=300)
            data = json.loads(output.read_text())
            if len(data) != 1:
                raise RuntimeError("Expected exactly one JMH result")
            combined.extend(data)
        except (subprocess.SubprocessError, ValueError, OSError, RuntimeError) as error:
            metadata["failures"].append({"operation": row["operation"], "caseName": row["caseName"], "error": str(error).replace(str(ROOT), ".")})
        (results / "jmh.json").write_text(json.dumps(combined, indent=2), encoding="utf-8")
        (results / "environment.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    metadata["finished_utc"] = datetime.now(timezone.utc).isoformat()
    (results / "environment.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    run([sys.executable, "generate_report.py"])
    if metadata["failures"] or not combined:
        raise SystemExit("Benchmark failures recorded; inspect report and logs")

if __name__ == "__main__":
    main()
