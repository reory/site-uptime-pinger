import requests
import time
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler

# logging.basicConfig with this "Handler" setup
logger = logging.getLogger("UptimeLogger")
logger.setLevel(logging.INFO)

# Create a handler that rotates at 5MB, keeping 5 backup files
# Then a new file will be created.
handler = RotatingFileHandler(
    'uptime.log', 
    maxBytes=5*1024*1024, 
    backupCount=5,
    encoding="utf-8"
)

# Create a logging format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(handler)

def run_multi_pinger(urls: list, interval: int = 60):
    """
    Monitors a list of websites uptime by sending HTTP GET requests
    """

    print(f"⏲️Starting multi-site monitoring {len(urls)} targets")
    print(f"Checking every {interval} seconds...\n")

    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"⏱️Scan started at {timestamp}....")

        for url in urls:
            try:
               # The Request (with a 5 second timeout)
               response = requests.get(url, timeout=5)
               # Validation
               if response.status_code == 200:
                  status_msg = f"✅ {url} is UP (200)"
                  print(status_msg)
                  logger.info(status_msg) # Saves to a file
               else:
                  status_msg = f"⚠️ {url} returned {response.status_code}"
                  print(status_msg)
                  logger.warning(status_msg) # Saves to a file
        
            except requests.exceptions.RequestException as e:
                # Error handling - for when the site is unreachable
                error_msg = f"🛑 {url} is OFFLINE: {type(e).__name__}"
                print(error_msg)
                logger.error(error_msg) # Saves to a file
        
        print(f"Scan complete😃 Sleeping for {interval}s...\n")
        time.sleep(interval)

if __name__ == "__main__":

    # list of target websites to monitor
    sites_to_watch = [
        "https://www.google.com",
        "https://www.github.com",
        "https://matplotlib.org",
        "https://python.org",
        "https://www.wikipedia.org",
        # fake url to see if the script is working as expected.
        "https://this-site-is-definitely-fake-123.com" 
    ]

    run_multi_pinger(sites_to_watch, interval=60)