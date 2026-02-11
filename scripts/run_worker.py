
import os
import sys
import subprocess

def run_worker():
    """
    Runs the RQ worker with the appropriate arguments for the operating system.
    """
    cmd = ["rq", "worker", "resumes", "--url", "redis://localhost:6379/0"]
    
    if os.name == 'nt':
        print("Detected Windows. Using rq.SimpleWorker to avoid os.fork() issues.")
        cmd.extend(["--worker-class", "rq.SimpleWorker"])
    
    print(f"Running command: {' '.join(cmd)}")
    
    # Pass environment variable to trigger file logging in worker
    env = os.environ.copy()
    env["RQ_WORKER_LOGGING"] = "true"
    
    try:
        subprocess.run(cmd, check=True, env=env)
    except KeyboardInterrupt:
        print("\nWorker stopped.")
    except Exception as e:
        print(f"Error running worker: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_worker()
