import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

import requests
from rich.console import Console
from rich.live import Live
from rich.table import Table

# Background Logging Setup
logger = logging.getLogger("UptimeLogger")
logger.setLevel(logging.INFO)

handler = RotatingFileHandler(
    'uptime.log', 
    maxBytes=5 * 1024 * 1024, 
    backupCount=5,
    encoding="utf-8"
)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

HEADERS = {
    "User-Agent": "UptimeMonitor/1.0 (+https://github.com/reory/site-uptime-pinger)"
}

def check_single_url(url: str, timeout: int = 5) -> dict:
    """Checks a single URL, tracks latency in ms, and returns formatted table data."""

    start_time = time.perf_counter()
    
    try:
        response = requests.head(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if response.status_code == 405:  # Fallback if HEAD isn't allowed
            response = requests.get(url, headers=HEADERS, timeout=timeout, stream=True)

        elapsed_ms = round((time.perf_counter() - start_time) * 1000)

        if response.ok:
            status_text = f"[bold green]UP ({response.status_code})[/bold green]"
            logger.info(f"✅ {url} is UP ({response.status_code}) - {elapsed_ms}ms")
        else:
            status_text = f"[bold yellow]WARN ({response.status_code})[/bold yellow]"
            logger.warning(f"⚠️ {url} returned {response.status_code} - {elapsed_ms}ms")

        return {
            "url": url,
            "status": status_text,
            "latency": f"{elapsed_ms} ms",
            "last_checked": datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
        }

    except requests.exceptions.RequestException as e:
        status_text = f"[bold red]OFFLINE ({type(e).__name__})[/bold red]"
        logger.error(f"🛑 {url} is OFFLINE: {type(e).__name__}")
        
        return {
            "url": url,
            "status": status_text,
            "latency": "N/A",
            "last_checked": datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
        }

def build_dashboard_table(site_data: dict, status_caption: str) -> Table:
    """Generates a rich Table object using current site states."""

    table = Table(
        title="⏱️ [bold cyan]Site Uptime Pinger Monitor[/bold cyan]",
        caption=status_caption,
        expand=True
    )
    
    table.add_column("Target URL", style="blue", no_wrap=True)
    table.add_column("Status", justify="center")
    table.add_column("Latency", justify="right", style="magenta")
    table.add_column("Last Checked", justify="center", style="dim")

    for info in site_data.values():
        table.add_row(
            info["url"],
            info["status"],
            info["latency"],
            info["last_checked"]
        )

    return table

def run_rich_pinger(urls: list, interval: int = 60, max_workers: int = 10):
    """Monitors sites concurrently and updates a live rich terminal dashboard."""

    # Initialize state dictionary for all sites
    site_status = {
        url: {
            "url": url,
            "status": "[dim]PENDING...[/dim]",
            "latency": "--",
            "last_checked": "Never"
        }
        for url in urls
    }

    console = Console()

    with Live(build_dashboard_table(site_status, "Starting initial scan..."), console=console, refresh_per_second=4) as live:
        while True:

            # Run parallel health checks
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(check_single_url, url) for url in urls]
                
                for future in as_completed(futures):
                    result = future.result()
                    site_status[result["url"]] = result
                    # Refresh dashboard as each thread completes
                    live.update(build_dashboard_table(site_status, "Scan complete. Waiting for next cycle..."))

            # Countdown timer between scans
            for remaining in range(interval, 0, -1):
                caption = f"⏳ Next check in [bold]{remaining}s[/bold] | Press Ctrl+C to exit"
                live.update(build_dashboard_table(site_status, caption))
                time.sleep(1)

if __name__ == "__main__":
    sites_to_watch = [
        "https://www.google.com",
        "https://www.github.com",
        "https://matplotlib.org",
        "https://python.org",
        "https://www.wikipedia.org",
        "https://this-site-is-definitely-fake-123.com" 
    ]

    try:
        run_rich_pinger(sites_to_watch, interval=15)
    except KeyboardInterrupt:
        print("\n[!] Exiting Uptime Monitor. Goodbye!")