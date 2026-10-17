import signal
import subprocess
import sys
import time
from pathlib import Path

root = Path(__file__).resolve().parent
from lab.server import auth_tokens
auth_tokens()
logs = root / 'logs'
logs.mkdir(exist_ok=True)
processes = []
for service in ['dashboard', 'baseline', 'protected']:
    log = (logs / f'{service}.log').open('a')
    proc = subprocess.Popen([sys.executable, '-m', 'lab.server', service], cwd=root, stdout=log, stderr=log)
    processes.append(proc)
    print(f'{service}: pid {proc.pid}, http://127.0.0.1:{8170 + ["dashboard", "baseline", "protected"].index(service)}', flush=True)

def stop(*args):
    for proc in processes:
        proc.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, stop)
signal.signal(signal.SIGTERM, stop)
while True:
    if any(p.poll() is not None for p in processes):
        print('A service exited; inspect logs/', flush=True)
        stop()
    time.sleep(1)
