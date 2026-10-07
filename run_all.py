import subprocess
import sys
import os

def run_parallel():
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    longform = subprocess.Popen([sys.executable, "src/longform_pipeline.py"], env=env)
    shortform = subprocess.Popen([sys.executable, "src/shortform_pipeline.py"], env=env)
    
    longform.wait()
    shortform.wait()
    print("All parallel pipelines finished.")

if __name__ == "__main__":
    run_parallel()
