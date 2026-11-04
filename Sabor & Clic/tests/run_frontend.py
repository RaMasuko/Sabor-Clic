"""Executa as telas contra servidor local e banco descartável no mesmo processo pai."""

import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

root = Path(__file__).resolve().parents[1]
server = subprocess.Popen(
    [sys.executable, str(root / "tests" / "serve_browser.py")],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
try:
    for _ in range(100):
        if server.poll() is not None:
            raise RuntimeError(
                "O servidor de teste não iniciou. Verifique a porta 5001."
            )
        try:
            urllib.request.urlopen("http://127.0.0.1:5001/login", timeout=1).close()
            break
        except OSError:
            time.sleep(0.05)
    else:
        raise RuntimeError("O servidor de teste não respondeu.")
    result = subprocess.run(
        ["node", str(root / "tests" / "frontend_dom.cjs")], cwd=root
    )
finally:
    server.terminate()
    server.wait(timeout=10)
sys.exit(result.returncode)
