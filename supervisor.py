import subprocess
import time
import logging

from utils import get_now

# Logging setup
log_level = logging.INFO
logger = logging.getLogger()
logger.setLevel(log_level)
fh = logging.handlers.RotatingFileHandler('logs/log.log', maxBytes=1000000, backupCount=5)
fh.setLevel(log_level)
formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='[%Y-%m-%d %H:%M:%S]')
fh.setFormatter(formatter)
logger.addHandler(fh)

while True:
    subprocess.call(["python", "main.py"])  #nosec
    logger.info('This is the supervisor speaking. I am commanding you to RAISE AGAIN!')
    print(f"{get_now()} Processo terminato. Riavvio...")
    time.sleep(0.5)