import subprocess
import time

from rich import print

from utils import get_now

while True:
    subprocess.call(["python", "main.py"])
    print(f"{get_now()} Processo terminato. Riavvio...")
    time.sleep(0.1)