#!/usr/bin/env python3
"""
network_diag.py

Simple network diagnostics tool:
- Ping sweep
- TCP port scan
- HTTP checker

Usage examples:
    python network_diag.py ping-sweep --cidr 192.168.1.0/24
    python network_diag.py ping-sweep --network 192.168.1. --start 1 --end 50
    python network_diag.py port-scan --host 192.168.1.10 --ports 22,80,443
    python network_diag.py http-check --urls https://example.com,https://google.com
"""

import argparse
import ipaddress
import logging
import platform
import socket
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple

import requests  # pip install requests

# ---------- Logging setup ----------

def setup_logger(verbosity: int, log_file: str = "network_diag.log") -> logging.Logger:
    logger = logging.getLogger("network_diag")
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Console handler
    ch = logging.StreamHandler()
    if verbosity >= 2:
        ch.setLevel(logging.DEBUG)
    elif verbosity == 1:
        ch.setLevel(logging.INFO)
    else:
        ch.setLevel(logging.WARNING)

    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    ch.setFormatter(fmt)
    fh.setFormatter(fmt)

    logger.addHandler(ch)
    logger.addHandler(fh)

    return logger


# ---------- Ping sweep ----------

def ping_host(host: str, timeout: int = 1) -> bool:
    """
    Returns True if host responds to a ping request.
    Uses system ping for portability.
    """
    system = platform.system().lower()
    if system == "windows":
        cmd = ["ping", "-n", "1", "-w", str(timeout * 1000), host]
    else:
        cmd = ["ping", "-c", "1", "-W", str(timeout), host]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return result.returncode == 0
    except Exception:
        return False


def ping_sweep_cidr(
    cidr: str,
    timeout: int,
    max_workers: int,
    logger: logging.Logger,
) -> List[str]:
    try:
        network = ipaddress.ip_network(cidr, strict=False)
    except ValueError as e:
        logger.error(f"Invalid CIDR {cidr}: {e}")
        return []

    hosts = [str(h) for h in network.hosts()]
    logger.info(f"Starting ping sweep for {len(hosts)} hosts in {cidr}")

    live_hosts = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(ping_host, host, timeout): host for host in hosts
        }
        for future in as_completed(future_map):
            host = future_map[future]
            try:
                up = future.result()
                if up:
                    live_hosts.append(host)
                    logger.info(f"Host UP: {host}")
                else:
                    logger.debug(f"Host DOWN: {host}")
            except Exception as e:
                logger.error(f"Error pinging {host}: {e}")

    logger.info(f"Ping sweep complete. Live hosts: {len(live_hosts)}")
    return live_hosts


def ping_sweep_range(
    base_network: str,
    start: int,
    end: int,
    timeout: int,
    max_workers: int,
    logger: logging.Logger,
) -> List[str]:
    if not base_network.endswith("."):
        logger.error("Base network must end with a dot, e.g., 192.168.1.")
        return []

    hosts = [f"{base_network}{i}" for i in range(start, end + 1)]
    logger.info(f"Starting ping sweep for {len(hosts)} hosts in {base_network}{start}-{end}")

    live_hosts = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(ping_host, host, timeout): host for host in hosts
        }
        for future in as_completed(future_map):
            host = future_map[future]
            try:
                up = future.result()
                if up:
                    live_hosts.append(host)
                    logger.info(f"Host UP: {host}")
                else:
                    logger.debug(f"Host DOWN: {host}")
            except Exception as e:
                logger.error(f"Error pinging {host}: {e}")

    logger.info(f"Ping sweep complete. Live hosts: {len(live_hosts)}")
    return live_hosts


# ---------- Port scanner ----------

def scan_port(host: str, port: int, timeout: float = 1.0) -> bool:
    """
    Returns True if TCP port is open on host.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        try:
            result = s.connect_ex((host, port))
            return result == 0
        except Exception:
            return False


def port_scan(
    host: str,
    ports: List[int],
    timeout: float,
    max_workers: int,
    logger: logging.Logger,
) -> List[int]:
    try:
        target_ip = socket.gethostbyname(host)
    except socket.gaierror as e:
        logger.error(f"Cannot resolve host {host}: {e}")
        return []

    logger.info(f"Starting port scan on {host} ({target_ip}) for {len(ports)} ports")

    open_ports = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(scan_port, target_ip, port, timeout): port for port in ports
        }
        for future in as_completed(future_map):
            port = future_map[future]
            try:
                is_open = future.result()
                if is_open:
                    open_ports.append(port)
                    logger.info(f"Port OPEN: {port}")
                else:
                    logger.debug(f"Port CLOSED: {port}")
            except Exception as e:
                logger.error(f"Error scanning port {port} on {target_ip}: {e}")

    logger.info(f"Port scan complete. Open ports: {open_ports}")
    return open_ports


# ---------- HTTP checker ----------

def check_http_url(
    url: str,
    timeout: float,
    logger: logging.Logger,
) -> Tuple[str, bool, int, str]:
    """
    Returns (url, accessible, status_code, error_message).
    """
    try:
        resp = requests.get(url, timeout=timeout)
        accessible = resp.status_code < 400
        logger.info(f"HTTP {url} -> {resp.status_code}")
        return url, accessible, resp.status_code, ""
    except requests.exceptions.RequestException as e:
        logger.warning(f"HTTP error for {url}: {e}")
        return url, False, 0, str(e)


def http_check(
    urls: List[str],
    timeout: float,
    max_workers: int,
    logger: logging.Logger,
) -> List[Tuple[str, bool, int, str]]:
    logger.info(f"Starting HTTP checks for {len(urls)} URLs")
    results: List[Tuple[str, bool, int, str]] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(check_http_url, url, timeout, logger): url for url in urls
        }
        for future in as_completed(future_map):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                url = future_map[future]
                logger.error(f"Unhandled exception checking {url}: {e}")

    logger.info("HTTP checks complete")
    return results


# ---------- Argument parsing & main ----------

def parse_ports(ports_str: str) -> List[int]:
    """
    Parse a port string like "22,80,1000-1010" into a list of ints.
    """
    ports: List[int] = []
    for part in ports_str.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            start = int(start_s)
            end = int(end_s)
            if start > end:
                start, end = end, start
            ports.extend(range(start, end + 1))
        else:
            ports.append(int(part))
    # Remove duplicates and sort
    return sorted(set(ports))


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Network diagnostics tool: ping sweep, port scan, HTTP checker"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (e.g., -v, -vv)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=64,
        help="Maximum number of worker threads (default: 64)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Ping sweep
    ping_parser = subparsers.add_parser("ping-sweep", help="Perform ping sweep")
    group = ping_parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--cidr", type=str, help="CIDR, e.g., 192.168.1.0/24")
    group.add_argument(
        "--network",
        type=str,
        help="Base network with trailing dot, e.g., 192.168.1.",
    )
    ping_parser.add_argument(
        "--start",
        type=int,
        help="Start host number when using --network",
    )
    ping_parser.add_argument(
        "--end",
        type=int,
        help="End host number when using --network",
    )
    ping_parser.add_argument(
        "--timeout",
        type=int,
        default=1,
        help="Ping timeout in seconds (default: 1)",
    )

    # Port scan
    port_parser = subparsers.add_parser("port-scan", help="Perform TCP port scan")
    port_parser.add_argument(
        "--host",
        type=str,
        required=True,
        help="Hostname or IP to scan",
    )
    port_parser.add_argument(
        "--ports",
        type=str,
        required=True,
        help='Ports, e.g., "22,80,443" or "1-1024,8080"',
    )
    port_parser.add_argument(
        "--timeout",
        type=float,
        default=1.0,
        help="Port connect timeout in seconds (default: 1.0)",
    )

    # HTTP checker
    http_parser = subparsers.add_parser("http-check", help="Check HTTP URLs")
    http_parser.add_argument(
        "--urls",
        type=str,
        required=True,
        help='Comma-separated URLs, e.g., "https://example.com,https://google.com"',
    )
    http_parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="HTTP request timeout in seconds (default: 5.0)",
    )

    return parser


def main(argv=None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    logger = setup_logger(args.verbose)

    try:
        if args.command == "ping-sweep":
            if args.cidr:
                live_hosts = ping_sweep_cidr(
                    cidr=args.cidr,
                    timeout=args.timeout,
                    max_workers=args.workers,
                    logger=logger,
                )
            else:
                if args.start is None or args.end is None:
                    logger.error("--start and --end are required when using --network")
                    return 1
                live_hosts = ping_sweep_range(
                    base_network=args.network,
                    start=args.start,
                    end=args.end,
                    timeout=args.timeout,
                    max_workers=args.workers,
                    logger=logger,
                )

            for host in live_hosts:
                print(host)

        elif args.command == "port-scan":
            ports = parse_ports(args.ports)
            if not ports:
                logger.error("No valid ports specified")
                return 1

            open_ports = port_scan(
                host=args.host,
                ports=ports,
                timeout=args.timeout,
                max_workers=args.workers,
                logger=logger,
            )

            for port in open_ports:
                print(port)

        elif args.command == "http-check":
            urls = [u.strip() for u in args.urls.split(",") if u.strip()]
            if not urls:
                logger.error("No valid URLs specified")
                return 1

            results = http_check(
                urls=urls,
                timeout=args.timeout,
                max_workers=args.workers,
                logger=logger,
            )

            for url, accessible, status_code, error in results:
                if accessible:
                    print(f"{url} OK (status={status_code})")
                else:
                    if status_code:
                        print(f"{url} FAIL (status={status_code})")
                    else:
                        print(f"{url} ERROR ({error})")

    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        return 130
    except Exception as e:
        logger.exception(f"Unhandled exception: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
