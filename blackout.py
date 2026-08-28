import sys
import argparse
import time
from concurrent.futures import ThreadPoolExecutor
import requests
from rich.console import Console
from rich.table import Table

console = Console()

def send_request(target_url):
    """Sends a single HTTP GET request and tracks status and latency."""
    start_time = time.time()
    try:
        response = requests.get(target_url, timeout=5)
        latency = (time.time() - start_time) * 1000  # in milliseconds
        return response.status_code, latency
    except requests.exceptions.RequestException:
        return "Error", 0

def run_load_test(target_url, num_requests, concurrency):
    """Executes multiple requests concurrently using a thread pool."""
    results = {"200": 0, "302": 0, "403": 0, "404": 0, "5xx": 0, "Error": 0}
    latencies = []

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(send_request, target_url) for _ in range(num_requests)]
        
        for future in futures:
            status, latency = future.result()
            if status == 200:
                results["200"] += 1
            elif status == 302:
                results["302"] += 1
            elif status == 403:
                results["403"] += 1
            elif status == 404:
                results["404"] += 1
            elif isinstance(status, int) and 500 <= status < 600:
                results["5xx"] += 1
            else:
                results["Error"] += 1
                
            if latency > 0:
                latencies.append(latency)

    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    return results, avg_latency

def main():
    parser = argparse.ArgumentParser(description="HTTP Load and Performance Stress Tester")
    parser.add_argument("url", help="Target URL (e.g., http://zero.webappsecurity.com)")
    parser.add_argument("-n", "--requests", type=int, default=50, help="Total number of requests")
    parser.add_argument("-c", "--concurrency", type=int, default=10, help="Concurrent threads")
    args = parser.parse_args()

    console.print(f"[bold cyan][+] Launching load test against:[/bold cyan] {args.url}")
    console.print(f"[bold]Total Requests:[/bold] {args.requests} | [bold]Concurrency:[/bold] {args.concurrency}\n")

    start_total = time.time()
    with console.status("[bold green]Sending traffic spike..."):
        stats, avg_latency = run_load_test(args.url, args.requests, args.concurrency)
    total_time = time.time() - start_total

    table = Table(title="Load Test Performance Summary")
    table.add_column("Metric", style="bold cyan")
    table.add_column("Value", style="bold yellow")

    table.add_row("Total Time Elapsed", f"{total_time:.2f} seconds")
    table.add_row("Average Latency", f"{avg_latency:.2f} ms")
    table.add_row("HTTP 200 OK", str(stats["200"]))
    table.add_row("HTTP 302 Redirect", str(stats["302"]))
    table.add_row("HTTP 403 Forbidden", str(stats["403"]))
    table.add_row("HTTP 404 Not Found", str(stats["404"]))
    table.add_row("HTTP 5xx Server Errors", str(stats["5xx"]))
    table.add_row("Connection Errors", str(stats["Error"]))

    console.print(table)

if __name__ == "__main__":
    main()
