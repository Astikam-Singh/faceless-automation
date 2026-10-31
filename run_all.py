import subprocess
import sys
import os

def run_parallel():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    env = os.environ.copy()
    env["PYTHONPATH"] = project_dir
    longform = subprocess.Popen(
        [sys.executable, "src/longform_pipeline.py"], env=env, cwd=project_dir
    )
    shortform = subprocess.Popen(
        [sys.executable, "src/shortform_pipeline.py"], env=env, cwd=project_dir
    )
    
    longform.wait()
    shortform.wait()
    failures = []
    if longform.returncode != 0:
        failures.append(f"long-form (exit code {longform.returncode})")
    if shortform.returncode != 0:
        failures.append(f"short-form (exit code {shortform.returncode})")

    if failures:
        print("Pipeline failure: " + ", ".join(failures))
        return 1

    print("Both pipelines completed successfully.")
    return 0

if __name__ == "__main__":
    raise SystemExit(run_parallel())
