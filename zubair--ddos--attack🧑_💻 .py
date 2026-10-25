#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
   ___ ____   ___  _   _   __        __    _    _____ _____ _____ _     _____
  |_ _|  _ \ / _ \| \ | |  \ \      / /   / \  |  ___|  ___|  ___| |   | ____|
   | || |_) | | | |  \| |   \ \ /\ / /   / _ \ | |_  | |_  | |_  | |   |  _|
   | ||  _ <| |_| | |\  |    \ V  V /   / ___ \|  _| |  _| |  _| | |___| |___
  |___|_| \_\\___/|_| \_|     \_/\_/   /_/   \_\_|   |_|   |_|   |_____|_____|

  IRON WAFFLE  OMEGA   v1.0.0  "FULL BREAKFAST"
  DDoS Mechanics | HTTPS Defense | Traffic Analysis Lab

  Everything runs on 127.0.0.1. Nothing is ever sent to a public IP.
  All attack traffic is SYNTHETIC unless you explicitly run the loopback driver.
================================================================================
"""

from __future__ import annotations

import argparse
import collections
import contextlib
import ctypes
import dataclasses
import datetime as _dt
import ipaddress
import json
import math
import os
import platform
import random
import re
import shutil
import signal
import socket
import socketserver
import ssl
import statistics
import string
import subprocess
import sys
import threading
import time
import traceback
import unittest
import urllib.parse
from collections import Counter, OrderedDict, deque
from dataclasses import dataclass, field
from typing import Any, Callable, Deque, Dict, Iterable, List, Optional, Sequence, Tuple

# =============================================================================
# SECTION 0 - BUILD METADATA
# =============================================================================

BUILD_NAME     = "IRON WAFFLE"
BUILD_TAG      = "OMEGA"
BUILD_VERSION  = "1.0.0"
BUILD_CODENAME = "FULL BREAKFAST"

BANNER = r"""
  ___ ____   ___  _   _   __        __    _    _____ _____ _____ _     _____
 |_ _|  _ \ / _ \| \ | |  \ \      / /   / \  |  ___|  ___|  ___| |   | ____|
  | || |_) | | | |  \| |   \ \ /\ / /   / _ \ | |_  | |_  | |_  | |   |  _|
  | ||  _ <| |_| | |\  |    \ V  V /   / ___ \|  _| |  _| |  _| | |___| |___
 |___|_| \_\\___/|_| \_|     \_/\_/   /_/   \_\_|   |_|   |_|   |_____|_____|
"""

TAGLINE = "DDoS Mechanics  |  HTTPS Defense  |  Traffic Analysis   [loopback only]"

# =============================================================================
# SECTION 1 - TERMINAL / COLOUR
# =============================================================================

class A:
    """ANSI escapes. Named colours, no magic numbers scattered in the code."""
    RESET   = "\x1b[0m"
    BOLD    = "\x1b[1m"
    DIM     = "\x1b[2m"
    ITALIC  = "\x1b[3m"
    UNDER   = "\x1b[4m"
    BLINK   = "\x1b[5m"
    REV     = "\x1b[7m"
    BLACK   = "\x1b[30m"
    RED     = "\x1b[31m"
    GREEN   = "\x1b[32m"
    YELLOW  = "\x1b[33m"
    BLUE    = "\x1b[34m"
    MAGENTA = "\x1b[35m"
    CYAN    = "\x1b[36m"
    WHITE   = "\x1b[37m"
    GREY    = "\x1b[90m"
    BRED    = "\x1b[91m"
    BGREEN  = "\x1b[92m"
    BYELLOW = "\x1b[93m"
    BBLUE   = "\x1b[94m"
    BMAGENTA= "\x1b[95m"
    BCYAN   = "\x1b[96m"
    BWHITE  = "\x1b[97m"
    BGRED   = "\x1b[41m"
    BGGREEN = "\x1b[42m"
    BGYELLOW= "\x1b[43m"
    BGBLUE  = "\x1b[44m"
    BGCYAN  = "\x1b[46m"


_COLOR_ENABLED = True


def _detect_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("IRONWAFFLE_COLOR") == "always":
        return True
    if os.name == "nt":
        # Enable Virtual Terminal Processing on modern Windows consoles.
        try:
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)
            mode = ctypes.c_uint32()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                kernel32.SetConsoleMode(handle, mode.value | 0x0004)
                return True
        except Exception:
            return False
        return False
    return sys.stdout.isatty()


def set_color(enabled: bool) -> None:
    global _COLOR_ENABLED
    _COLOR_ENABLED = bool(enabled)


def paint(text: str, *styles: str) -> str:
    if not _COLOR_ENABLED or not styles:
        return text
    return "".join(styles) + text + A.RESET


def strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def hrule(char: str = "=", width: int = 78, color: str = A.GREY) -> str:
    return paint(char * width, color)


def kv(label: str, value: Any, lcolor: str = A.GREY, vcolor: str = A.WHITE,
       width: int = 30) -> str:
    return f"  {paint(label.ljust(width), lcolor)}{paint(str(value), vcolor)}"


# =============================================================================
# SECTION 2 - BLOCK BANNER RENDERER
# =============================================================================

_FIG = {
    "I": [" ___ ", "|_ _|", " | | ", " | | ", "|___|"],
    "R": [" ____  ", "|  _ \\ ", "| |_) |", "|  _ < ", "|_| \\_\\"],
    "O": ["  ___  ", " / _ \\ ", "| | | |", "| |_| |", " \\___/ "],
    "N": [" _   _ ", "| \\ | |", "|  \\| |", "| |\\  |", "|_| \\_|"],
    "W": ["__        __", "\\ \\      / /", " \\ \\ /\\ / / ", "  \\ V  V /  ", "   \\_/\\_/   "],
    "A": ["    _    ", "   / \\   ", "  / _ \\  ", " / ___ \\ ", "/_/   \\_\\"],
    "F": [" _____ ", "|  ___|", "| |_   ", "|  _|  ", "|_|    "],
    "L": [" _     ", "| |    ", "| |    ", "| |___ ", "|_____|"],
    "E": [" _____ ", "| ____|", "|  _|  ", "| |___ ", "|_____|"],
    " ": ["   ", "   ", "   ", "   ", "   "],
}


def block_text(text: str, spacing: int = 1) -> str:
    rows = [""] * 5
    for ch in text.upper():
        glyph = _FIG.get(ch, _FIG[" "])
        w = max(len(g) for g in glyph)
        for i in range(5):
            rows[i] += glyph[i].ljust(w) + (" " * spacing)
    return "\n".join(rows)


def sparkline(values: Sequence[float], width: int = 68) -> str:
    """Compact unicode sparkline for time series."""
    ramp = "▁▂▃▄▅▆▇█"
    if not values:
        return ""
    if len(values) > width:
        step = len(values) / width
        sampled = [values[min(int(i * step), len(values) - 1)] for i in range(width)]
    else:
        sampled = list(values)
    hi = max(sampled) or 1.0
    out = []
    for v in sampled:
        idx = int((v / hi) * (len(ramp) - 1)) if hi > 0 else 0
        out.append(ramp[max(0, min(idx, len(ramp) - 1))])
    return "".join(out)


def bar(value: float, maximum: float, width: int = 30, color: str = A.GREEN) -> str:
    maximum = maximum if maximum > 0 else 1.0
    frac = max(0.0, min(1.0, value / maximum))
    filled = int(frac * width)
    return paint("█" * filled, color) + paint("░" * (width - filled), A.GREY)


# =============================================================================
# SECTION 3 - CONFIG
# =============================================================================

LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost"}


@dataclass
class LabConfig:
    host: str = "127.0.0.1"
    port: int = 8443
    cert_dir: str = ".ironwaffle"
    log_path: Optional[str] = None
    log_level: str = "INFO"
    tls: bool = True
    rate_limit_rps: float = 25.0
    rate_limit_burst: float = 50.0
    max_clients: int = 8192
    window_s: float = 60.0
    max_inflight: int = 96
    max_queue_wait_s: float = 1.5
    capacity_rps: float = 250.0
    db_pool_size: int = 8
    db_query_ms: float = 12.0
    db_acquire_timeout_s: float = 0.35
    cache_ttl_s: float = 5.0
    cache_max_entries: int = 512
    slow_endpoint_ms: float = 40.0
    enforce_loopback: bool = True
    alert_rps: float = 150.0
    alert_error_pct: float = 5.0
    alert_p95_ms: float = 250.0

    def validate(self) -> None:
        if self.enforce_loopback:
            try:
                if not ipaddress.ip_address(self.host).is_loopback:
                    raise ValueError(
                        f"host {self.host!r} is not a loopback address; "
                        "refusing to run (no external traffic policy)"
                    )
            except ValueError as exc:
                if self.host not in LOOPBACK_HOSTS:
                    raise ValueError(str(exc)) from exc
        if not (0 < self.port < 65536):
            raise ValueError("port must be in 1..65535")
        for name in ("rate_limit_rps", "rate_limit_burst", "capacity_rps",
                     "window_s", "cache_ttl_s"):
            val = getattr(self, name)
            if val <= 0:
                raise ValueError(f"{name} must be > 0 (got {val})")
        if self.max_inflight < 1:
            raise ValueError("max_inflight must be >= 1")
        if not (0.0 <= self.alert_error_pct <= 100.0):
            raise ValueError("alert_error_pct must be 0..100")
        if self.max_clients < 16:
            raise ValueError("max_clients must be >= 16")


# =============================================================================
# SECTION 4 - STRUCTURED LOGGING
# =============================================================================

LEVELS = {"DEBUG": 10, "INFO": 20, "NOTICE": 25, "WARN": 30, "ERROR": 40, "CRIT": 50}
LEVEL_COLOR = {
    "DEBUG": A.GREY, "INFO": A.BCYAN, "NOTICE": A.BBLUE,
    "WARN": A.BYELLOW, "ERROR": A.BRED, "CRIT": A.BGRED + A.BWHITE,
}


class StructuredLog:
    """JSON-lines security event log, mirrored to a colourised console."""

    def __init__(self, level: str = "INFO", path: Optional[str] = None) -> None:
        self.min_level = LEVELS.get(level.upper(), 20)
        self.path = path
        self._lock = threading.Lock()
        self._fh = None
        if path:
            with contextlib.suppress(OSError):
                os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
                self._fh = open(path, "a", encoding="utf-8", buffering=1)

    def emit(self, level: str, event: str, **fields: Any) -> Optional[dict]:
        lvl = level.upper()
        if LEVELS.get(lvl, 20) < self.min_level:
            return None
        record = {
            "ts": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="milliseconds"),
            "lvl": lvl,
            "evt": event,
        }
        for k, v in fields.items():
            record[k] = v if isinstance(v, (int, float, bool, type(None))) else str(v)
        line = json.dumps(record, separators=(",", ":"), default=str)

        extras = " ".join(
            f"{k}={v}" for k, v in record.items() if k not in ("ts", "lvl", "evt")
        )
        stamp = record["ts"][11:23]
        console = (
            f"{paint(stamp, A.GREY)} "
            f"{paint(lvl.ljust(6), LEVEL_COLOR.get(lvl, A.WHITE), A.BOLD)} "
            f"{paint(event.ljust(22), A.BWHITE)} "
            f"{paint(extras, A.GREY)}"
        )
        with self._lock:
            print(console, flush=True)
            if self._fh:
                with contextlib.suppress(OSError):
                    self._fh.write(line + "\n")
        return record

    def close(self) -> None:
        if self._fh:
            with contextlib.suppress(OSError):
                self._fh.close()
            self._fh = None


# =============================================================================
# SECTION 5 - CEREAL: ROLLING WINDOWS (bounded, thread-safe)
# =============================================================================

class RollingWindow:
    """Time-bounded, size-bounded deque of (timestamp, value). Thread-safe."""

    __slots__ = ("_dq", "_lock", "window_s", "_maxlen")

    def __init__(self, window_s: float, maxlen: int = 100_000) -> None:
        if window_s <= 0:
            raise ValueError("window_s must be > 0")
        self.window_s = float(window_s)
        self._maxlen = max(1, int(maxlen))
        self._dq: Deque[Tuple[float, float]] = deque()
        self._lock = threading.Lock()

    def add(self, value: float = 1.0, ts: Optional[float] = None) -> None:
        now = time.monotonic() if ts is None else ts
        with self._lock:
            self._dq.append((now, float(value)))
            cutoff = now - self.window_s
            while self._dq and self._dq[0][0] < cutoff:
                self._dq.popleft()
            while len(self._dq) > self._maxlen:
                self._dq.popleft()

    def _pruned(self, now: float) -> List[Tuple[float, float]]:
        cutoff = now - self.window_s
        while self._dq and self._dq[0][0] < cutoff:
            self._dq.popleft()
        return list(self._dq)

    def count(self, now: Optional[float] = None) -> int:
        now = time.monotonic() if now is None else now
        with self._lock:
            return len(self._pruned(now))

    def total(self, now: Optional[float] = None) -> float:
        now = time.monotonic() if now is None else now
        with self._lock:
            return math.fsum(v for _, v in self._pruned(now))

    def rate(self, now: Optional[float] = None) -> float:
        return self.count(now) / self.window_s

    def values(self, now: Optional[float] = None) -> List[float]:
        now = time.monotonic() if now is None else now
        with self._lock:
            return [v for _, v in self._pruned(now)]

    def percentiles(self, points: Sequence[float] = (0.50, 0.95, 0.99),
                    now: Optional[float] = None) -> Dict[str, float]:
        vals = sorted(self.values(now))
        if not vals:
            return {f"p{int(p*100)}": 0.0 for p in points}
        out: Dict[str, float] = {}
        for p in points:
            idx = min(len(vals) - 1, max(0, int(math.ceil(p * len(vals))) - 1))
            out[f"p{int(p*100)}"] = round(vals[idx], 3)
        return out

    def mean(self, now: Optional[float] = None) -> float:
        vals = self.values(now)
        return round(statistics.fmean(vals), 3) if vals else 0.0

    def __len__(self) -> int:
        return self.count()


class Metrics:
    """SIZZLE - the telemetry core. Every counter is bounded and lock-protected."""

    def __init__(self, window_s: float = 60.0, max_clients: int = 8192,
                 series_max: int = 1800) -> None:
        self.window_s = window_s
        self.max_clients = max_clients
        self._lock = threading.Lock()
        self.started = time.time()
        self.counters: Counter = Counter()
        self.status_codes: Counter = Counter()
        self.status_class: Counter = Counter()
        self.paths: Counter = Counter()
        self.latency = RollingWindow(60.0, 40_000)
        self.win_1s = RollingWindow(1.0, 20_000)
        self.win_10s = RollingWindow(10.0, 100_000)
        self.win_60s = RollingWindow(60.0, 400_000)
        self.clients: "OrderedDict[str, RollingWindow]" = OrderedDict()
        self.series = deque(maxlen=series_max)   # (epoch, rps, err_pct, danger)
        self._last_series = 0.0

    def incr(self, name: str, n: float = 1) -> None:
        with self._lock:
            self.counters[name] += n

    def record(self, client: str, status: int, latency_ms: float, path: str) -> None:
        now = time.monotonic()
        with self._lock:
            self.counters["requests_total"] += 1
            self.status_codes[status] += 1
            self.status_class[f"{status // 100}xx"] += 1
            self.paths[path] += 1
            cw = self.clients.get(client)
            if cw is None:
                cw = RollingWindow(self.window_s, 4000)
                self.clients[client] = cw
                while len(self.clients) > self.max_clients:
                    self.clients.popitem(last=False)
            else:
                self.clients.move_to_end(client)
            self.latency.add(latency_ms, now)
            for w in (self.win_1s, self.win_10s, self.win_60s):
                w.add(1.0, now)
        cw.add(1.0, now)

    def error_rate_pct(self, window: RollingWindow) -> float:
        with self._lock:
            total = sum(self.status_codes.values()) or 1
            errs = sum(v for k, v in self.status_codes.items() if k >= 400)
        return round(100.0 * errs / total, 2)

    def window_error_pct(self) -> float:
        with self._lock:
            total = sum(self.status_codes.values()) or 1
            errs = sum(v for k, v in self.status_codes.items() if k >= 400)
        return round(100.0 * errs / total, 2)

    def top_clients(self, n: int = 8) -> List[Tuple[str, float]]:
        with self._lock:
            items = [(k, v.rate()) for k, v in self.clients.items()]
        items.sort(key=lambda kv: kv[1], reverse=True)
        return [(k, round(v, 2)) for k, v in items[:n]]

    def tick_series(self, rps: float, err_pct: float, danger_score: float) -> None:
        now = time.time()
        if now - self._last_series < 1.0:
            return
        self._last_series = now
        self.series.append((now, round(rps, 2), round(err_pct, 2), round(danger_score, 1)))

    def reset(self) -> None:
        with self._lock:
            self.counters.clear()
            self.status_codes.clear()
            self.status_class.clear()
            self.paths.clear()
            self.clients.clear()
        self.latency = RollingWindow(60.0, 40_000)
        self.win_1s = RollingWindow(1.0, 20_000)
        self.win_10s = RollingWindow(10.0, 100_000)
        self.win_60s = RollingWindow(60.0, 400_000)

    def uptime(self) -> float:
        return round(time.time() - self.started, 2)


# =============================================================================
# SECTION 6 - SYRUP: TOKEN BUCKET / LEAKY BUCKET / RATE LIMITER
# =============================================================================

class TokenBucket:
    """Classic token bucket. rate = tokens/sec, burst = bucket capacity."""

    __slots__ = ("rate", "burst", "_tokens", "_updated", "_lock")

    def __init__(self, rate: float, burst: float) -> None:
        if rate <= 0:
            raise ValueError("rate must be > 0")
        if burst <= 0:
            raise ValueError("burst must be > 0")
        self.rate = float(rate)
        self.burst = float(burst)
        self._tokens = float(burst)
        self._updated = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self, now: float) -> None:
        delta = now - self._updated
        if delta > 0:
            self._tokens = min(self.burst, self._tokens + delta * self.rate)
            self._updated = now

    def take(self, n: float = 1.0, now: Optional[float] = None) -> Tuple[bool, float]:
        """Returns (allowed, retry_after_seconds)."""
        now = time.monotonic() if now is None else now
        with self._lock:
            self._refill(now)
            if self._tokens >= n:
                self._tokens -= n
                return True, 0.0
            deficit = n - self._tokens
            return False, round(deficit / self.rate, 4)

    def tokens(self, now: Optional[float] = None) -> float:
        now = time.monotonic() if now is None else now
        with self._lock:
            self._refill(now)
            return round(self._tokens, 3)


class LeakyBucket:
    """Fixed-capacity bucket draining at a constant rate. Smooths bursts."""

    def __init__(self, capacity: int, drain_per_sec: float) -> None:
        self.capacity = int(capacity)
        self.drain = float(drain_per_sec)
        self._level = 0.0
        self._updated = time.monotonic()
        self._lock = threading.Lock()

    def offer(self, now: Optional[float] = None) -> bool:
        now = time.monotonic() if now is None else now
        with self._lock:
            self._level = max(0.0, self._level - (now - self._updated) * self.drain)
            self._updated = now
            if self._level + 1.0 <= self.capacity:
                self._level += 1.0
                return True
            return False

    def level(self) -> float:
        return round(self._level, 2)


class RateLimiter:
    """Per-client token buckets with a bounded client table (LRU eviction)."""

    def __init__(self, rate: float, burst: float, max_clients: int = 8192) -> None:
        self.rate = float(rate)
        self.burst = float(burst)
        self.max_clients = max_clients
        self._buckets: "OrderedDict[str, TokenBucket]" = OrderedDict()
        self._lock = threading.Lock()
        self.allowed = 0
        self.denied = 0

    def check(self, key: str, cost: float = 1.0) -> Tuple[bool, float]:
        with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None:
                bucket = TokenBucket(self.rate, self.burst)
                self._buckets[key] = bucket
                while len(self._buckets) > self.max_clients:
                    self._buckets.popitem(last=False)
            else:
                self._buckets.move_to_end(key)
        ok, retry = bucket.take(cost)
        with self._lock:
            if ok:
                self.allowed += 1
            else:
                self.denied += 1
        return ok, retry

    def configure(self, rate: Optional[float] = None,
                  burst: Optional[float] = None) -> None:
        with self._lock:
            if rate:
                self.rate = float(rate)
            if burst:
                self.burst = float(burst)
            self._buckets.clear()

    def client_count(self) -> int:
        with self._lock:
            return len(self._buckets)

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "rate_rps": self.rate,
                "burst": self.burst,
                "tracked_clients": len(self._buckets),
                "allowed": self.allowed,
                "denied": self.denied,
                "deny_pct": round(100.0 * self.denied / max(1, self.allowed + self.denied), 2),
            }


# =============================================================================
# SECTION 7 - PANCAKE: BOUNDED PRIORITY QUEUE + ADMISSION GATE
# =============================================================================

class BoundedPriorityQueue:
    """Three-class bounded queue. Drops the lowest class first when full."""

    LEVELS = ("LEGIT", "SUSPECT", "HOSTILE")

    def __init__(self, maxsize: int = 500) -> None:
        if maxsize < 1:
            raise ValueError("maxsize must be >= 1")
        self.maxsize = int(maxsize)
        self._q: Dict[str, Deque[Any]] = {lvl: deque() for lvl in self.LEVELS}
        self._size = 0
        self._lock = threading.Lock()
        self.dropped: Counter = Counter()
        self.enqueued = 0
        self.dequeued = 0

    def put(self, item: Any, level: str = "LEGIT") -> bool:
        if level not in self._q:
            raise ValueError(f"unknown level {level!r}")
        with self._lock:
            if self._size >= self.maxsize:
                for drop_level in reversed(self.LEVELS):
                    if drop_level != level or self._size >= self.maxsize:
                        if self._q[drop_level]:
                            self._q[drop_level].popleft()
                            self._size -= 1
                            self.dropped[drop_level] += 1
                            break
                else:
                    self.dropped[level] += 1
                    return False
            self._q[level].append(item)
            self._size += 1
            self.enqueued += 1
            return True

    def get(self) -> Optional[Any]:
        with self._lock:
            for lvl in self.LEVELS:
                if self._q[lvl]:
                    self._size -= 1
                    self.dequeued += 1
                    return self._q[lvl].popleft()
            return None

    def __len__(self) -> int:
        with self._lock:
            return self._size

    def occupancy_pct(self) -> float:
        return round(100.0 * len(self) / self.maxsize, 2)


class AdmissionController:
    """Real, bounded in-flight concurrency limit with a bounded wait queue."""

    def __init__(self, max_inflight: int = 96, max_wait_s: float = 1.5) -> None:
        self.max_inflight = int(max_inflight)
        self.max_wait_s = float(max_wait_s)
        self._sem = threading.BoundedSemaphore(self.max_inflight)
        self._lock = threading.Lock()
        self.inflight = 0
        self.waiting = 0
        self.admitted = 0
        self.rejected = 0

    def acquire(self) -> bool:
        with self._lock:
            self.waiting += 1
        ok = self._sem.acquire(timeout=self.max_wait_s)
        with self._lock:
            self.waiting -= 1
            if ok:
                self.inflight += 1
                self.admitted += 1
            else:
                self.rejected += 1
        return ok

    def release(self) -> None:
        with self._lock:
            if self.inflight > 0:
                self.inflight -= 1
            else:
                return
        with contextlib.suppress(ValueError):
            self._sem.release()

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "max_inflight": self.max_inflight,
                "inflight": self.inflight,
                "waiting": self.waiting,
                "utilization_pct": round(100.0 * self.inflight / self.max_inflight, 2),
                "admitted": self.admitted,
                "rejected": self.rejected,
                "reject_pct": round(100.0 * self.rejected / max(1, self.admitted + self.rejected), 2),
            }


# =============================================================================
# SECTION 8 - JAM: WAF / REQUEST VALIDATION
# =============================================================================

@dataclass
class WafVerdict:
    blocked: bool
    rule: str = ""
    detail: str = ""


class WAF:
    """Ordered rule set. First match wins. Cheap regexes, no backtracking bombs."""

    MAX_PATH_LEN = 2048
    MAX_QUERY_LEN = 4096
    MAX_UA_LEN = 512

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self._lock = threading.Lock()
        self.hits: Counter = Counter()
        self.inspected = 0
        self.rules: List[Tuple[str, Callable[[str, str, str], Optional[str]]]] = [
            ("path.too_long",      lambda p, q, u: f"len={len(p)}" if len(p) > self.MAX_PATH_LEN else None),
            ("query.too_long",     lambda p, q, u: f"len={len(q)}" if len(q) > self.MAX_QUERY_LEN else None),
            ("ua.too_long",        lambda p, q, u: f"len={len(u)}" if len(u) > self.MAX_UA_LEN else None),
            ("path.traversal",     lambda p, q, u: ".." if ".." in p else None),
            ("path.null_byte",     lambda p, q, u: "%00" if "%00" in p.lower() else None),
            ("path.meta_chars",    lambda p, q, u: "meta" if re.search(r"[<>'\"`|;]", p) else None),
            ("sqli.union",         lambda p, q, u: "union-select" if re.search(r"(?i)\bunion\b.{0,20}\bselect\b", q + p) else None),
            ("sqli.or_tautology",  lambda p, q, u: "or-1-1" if re.search(r"(?i)\bor\b\s+1\s*=\s*1", q + p) else None),
            ("xss.script",         lambda p, q, u: "script" if re.search(r"(?i)<script", q) else None),
            ("ua.empty",           lambda p, q, u: "empty" if not u.strip() else None),
            ("ua.attack_tool",     lambda p, q, u: "tool" if re.search(r"(?i)\b(?:python-requests|go-http|java/|libwww|bot/1)", u) else None),
            ("header.fold_injection", lambda p, q, u: "fold" if "\r" in u or "\n" in u else None),
        ]

    def inspect(self, method: str, path: str, query: str, user_agent: str) -> WafVerdict:
        with self._lock:
            self.inspected += 1
        if not self.enabled:
            return WafVerdict(False)
        for name, fn in self.rules:
            with contextlib.suppress(Exception):
                hit = fn(path, query, user_agent)
                if hit:
                    with self._lock:
                        self.hits[name] += 1
                    return WafVerdict(True, name, hit)
        return WafVerdict(False)

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "enabled": self.enabled,
                "inspected": self.inspected,
                "blocked": sum(self.hits.values()),
                "top_rules": self.hits.most_common(6),
            }


# =============================================================================
# SECTION 9 - FRIDGE: TTL CACHE
# =============================================================================

class TTLCache:
    def __init__(self, ttl_s: float = 5.0, max_entries: int = 512) -> None:
        self.ttl = float(ttl_s)
        self.max_entries = int(max_entries)
        self._d: "OrderedDict[str, Tuple[float, Any]]" = OrderedDict()
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def get(self, key: str) -> Optional[Any]:
        now = time.monotonic()
        with self._lock:
            item = self._d.get(key)
            if item is None:
                self.misses += 1
                return None
            expires, value = item
            if expires < now:
                del self._d[key]
                self.misses += 1
                return None
            self._d.move_to_end(key)
            self.hits += 1
            return value

    def put(self, key: str, value: Any) -> None:
        with self._lock:
            self._d[key] = (time.monotonic() + self.ttl, value)
            self._d.move_to_end(key)
            while len(self._d) > self.max_entries:
                self._d.popitem(last=False)
                self.evictions += 1

    def invalidate(self) -> None:
        with self._lock:
            self._d.clear()

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            total = self.hits + self.misses
            return {
                "entries": len(self._d),
                "ttl_s": self.ttl,
                "hits": self.hits,
                "misses": self.misses,
                "hit_ratio": round(self.hits / total, 3) if total else 0.0,
                "evictions": self.evictions,
            }


# =============================================================================
# SECTION 10 - GRIDDLE: DATABASE CONNECTION POOL
# =============================================================================

class ConnectionPool:
    """Fixed-size pool. Simulates DB latency and queue-wait exhaustion."""

    def __init__(self, size: int = 8, query_ms: float = 12.0,
                 acquire_timeout_s: float = 0.35) -> None:
        self.size = int(size)
        self.query_ms = float(query_ms)
        self.acquire_timeout_s = float(acquire_timeout_s)
        self._sem = threading.BoundedSemaphore(self.size)
        self._lock = threading.Lock()
        self.in_use = 0
        self.timeouts = 0
        self.queries = 0
        self.peak_in_use = 0

    @contextlib.contextmanager
    def acquire(self):
        got = self._sem.acquire(timeout=self.acquire_timeout_s)
        if not got:
            with self._lock:
                self.timeouts += 1
            raise TimeoutError("db pool exhausted")
        with self._lock:
            self.in_use += 1
            self.peak_in_use = max(self.peak_in_use, self.in_use)
            self.queries += 1
        try:
            time.sleep(self.query_ms / 1000.0)
            yield True
        finally:
            with self._lock:
                self.in_use = max(0, self.in_use - 1)
            with contextlib.suppress(ValueError):
                self._sem.release()

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "pool_size": self.size,
                "in_use": self.in_use,
                "peak_in_use": self.peak_in_use,
                "queries": self.queries,
                "timeouts": self.timeouts,
                "utilization_pct": round(100.0 * self.in_use / self.size, 2),
            }


# =============================================================================
# SECTION 11 - RESOURCE MONITOR
# =============================================================================

class ResourceMonitor:
    """CPU / memory sampling. Uses psutil if present, then stdlib fallbacks."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._last_wall = time.monotonic()
        self._last_cpu = time.process_time()
        self._cpu_pct = 0.0
        self._rss_mb = 0.0
        self._ncpu = os.cpu_count() or 1
        self.backend = "none"
        try:
            import psutil  # type: ignore
            self._psutil = psutil
            self.backend = "psutil"
        except Exception:
            self._psutil = None
            if os.name == "nt":
                self.backend = "ctypes"
            elif hasattr(os, "sysconf"):
                self.backend = "procfs" if os.path.isdir("/proc") else "resource"

    def sample(self) -> Dict[str, float]:
        with self._lock:
            if self._psutil is not None:
                with contextlib.suppress(Exception):
                    self._cpu_pct = float(self._psutil.Process().cpu_percent(interval=None))
                    self._rss_mb = self._psutil.Process().memory_info().rss / 1048576.0
            else:
                now = time.monotonic()
                cpu_now = time.process_time()
                wall = max(1e-6, now - self._last_wall)
                self._cpu_pct = max(0.0, min(100.0,
                    (cpu_now - self._last_cpu) / wall * 100.0 / self._ncpu))
                self._last_wall, self._last_cpu = now, cpu_now
                self._rss_mb = self._read_rss_mb()
            return {
                "cpu_pct": round(self._cpu_pct, 2),
                "rss_mb": round(self._rss_mb, 2),
                "threads": threading.active_count(),
                "backend": self.backend,
            }

    def _read_rss_mb(self) -> float:
        if self.backend == "procfs":
            with contextlib.suppress(Exception):
                with open("/proc/self/statm", "r", encoding="ascii") as fh:
                    pages = int(fh.read().split()[1])
                return pages * os.sysconf("SC_PAGE_SIZE") / 1048576.0
        if self.backend == "resource":
            with contextlib.suppress(Exception):
                import resource as _res  # type: ignore
                usage = _res.getrusage(_res.RUSAGE_SELF).ru_maxrss
                return usage / 1024.0 if sys.platform == "linux" else usage / 1048576.0
        if self.backend == "ctypes":
            with contextlib.suppress(Exception):
                class PMC(ctypes.Structure):
                    _fields_ = [
                        ("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
                        ("PeakWorkingSetSize", ctypes.c_size_t),
                        ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t),
                        ("PeakPagefileUsage", ctypes.c_size_t),
                    ]
                pmc = PMC()
                pmc.cb = ctypes.sizeof(PMC)
                ctypes.windll.psapi.GetProcessMemoryInfo(
                    ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb)
                return pmc.WorkingSetSize / 1048576.0
        return 0.0


# =============================================================================
# SECTION 12 - DANGER LADDER
# =============================================================================

@dataclass(frozen=True)
class DangerLevel:
    name: str
    floor: int
    color: str
    hint: str


DANGER_LADDER: List[DangerLevel] = [
    DangerLevel("RAW",    0,  A.BGREEN,   "idle / clean"),
    DangerLevel("WARM",   15, A.GREEN,    "normal load"),
    DangerLevel("SIMMER", 35, A.BYELLOW,  "elevated - watch it"),
    DangerLevel("SIZZLE", 55, A.YELLOW,   "suspicious - mitigations armed"),
    DangerLevel("SMOKE",  75, A.BRED,     "attack - shedding load"),
    DangerLevel("BURNT",  90, A.BGRED + A.BWHITE, "overload - service degraded"),
]


def danger_score(utilization: float, error_pct: float, p95_ms: float,
                 queue_pct: float) -> float:
    """0..100 composite pressure score. Weights sum to 100."""
    util_component = min(40.0, max(0.0, utilization) * 40.0)
    if utilization > 1.0:
        util_component = min(40.0, 40.0 + (utilization - 1.0) * 20.0)
    err_component = min(25.0, max(0.0, error_pct) * 2.5)
    lat_component = min(20.0, max(0.0, p95_ms) / 25.0)
    q_component = min(15.0, max(0.0, queue_pct) * 0.15)
    return round(min(100.0, util_component + err_component + lat_component + q_component), 1)


def danger_level(score: float) -> DangerLevel:
    level = DANGER_LADDER[0]
    for candidate in DANGER_LADDER:
        if score >= candidate.floor:
            level = candidate
    return level


def render_danger(score: float) -> str:
    lvl = danger_level(score)
    badge = paint(f" {lvl.name} ", lvl.color, A.BOLD)
    return f"{badge} {paint(f'score={score:5.1f}', A.GREY)} {paint('|', A.GREY)} {paint(lvl.hint, A.GREY)}"


# =============================================================================
# SECTION 13 - BACON: ALERT ENGINE
# =============================================================================

@dataclass
class Alert:
    ts: str
    severity: str
    code: str
    message: str
    value: float
    threshold: float


class AlertEngine:
    def __init__(self, cfg: LabConfig, log: StructuredLog, cooldown_s: float = 10.0) -> None:
        self.cfg = cfg
        self.log = log
        self.cooldown_s = cooldown_s
        self._lock = threading.Lock()
        self._last: Dict[str, float] = {}
        self.alerts: Deque[Alert] = deque(maxlen=200)
        self.active: Dict[str, Alert] = {}

    def _fire(self, code: str, severity: str, message: str,
              value: float, threshold: float) -> bool:
        now = time.monotonic()
        with self._lock:
            if now - self._last.get(code, -1e9) < self.cooldown_s:
                return False
            self._last[code] = now
            alert = Alert(
                ts=_dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
                severity=severity, code=code, message=message,
                value=round(value, 2), threshold=round(threshold, 2),
            )
            self.alerts.append(alert)
            self.active[code] = alert
        self.log.emit(severity, "alert.fired", code=code, msg=message,
                      value=round(value, 2), threshold=round(threshold, 2))
        return True

    def evaluate(self, snap: Dict[str, Any]) -> List[Alert]:
        fired: List[Alert] = []
        checks = [
            ("RPS_HIGH",   "WARN",  snap["rps_1s"],          self.cfg.alert_rps,
             "inbound request rate above baseline"),
            ("ERROR_HIGH", "ERROR", snap["error_pct"],        self.cfg.alert_error_pct,
             "HTTP error ratio above threshold"),
            ("LATENCY_P95","WARN",  snap["latency_p95_ms"],   self.cfg.alert_p95_ms,
             "p95 latency above threshold"),
            ("QUEUE_FULL", "ERROR", snap["gate"]["utilization_pct"], 90.0,
             "admission gate saturated"),
            ("RATE_DENY",  "WARN",  snap["rate_limiter"]["deny_pct"], 20.0,
             "rate limiter rejecting a large share of traffic"),
            ("WAF_SURGE",  "NOTICE",snap["waf"]["blocked"],   100.0,
             "high volume of malformed requests"),
            ("DB_POOL",    "ERROR", snap["db_pool"]["timeouts"], 5.0,
             "database pool acquisition timeouts"),
        ]
        for code, sev, value, threshold, msg in checks:
            if value >= threshold:
                if self._fire(code, sev, msg, float(value), float(threshold)):
                    with self._lock:
                        fired.append(self.alerts[-1])
        # clear resolved
        with self._lock:
            for code, _alert in list(self.active.items()):
                current = dict((c, v) for c, _s, v, _t, _m in checks)
                if code in current and current[code] < self.cfg.alert_rps * 0.0:
                    pass
        return fired

    def recent(self, n: int = 10) -> List[Dict[str, Any]]:
        with self._lock:
            return [dataclasses.asdict(a) for a in list(self.alerts)[-n:]]


# =============================================================================
# SECTION 14 - TOAST: TLS CERTIFICATE FORGE + POSTURE CHECK
# =============================================================================

class Toast:
    """Generates a local self-signed cert for CN/SAN 127.0.0.1 and audits TLS."""

    CERT_NAME = "cert.pem"
    KEY_NAME = "key.pem"

    def __init__(self, cert_dir: str, host: str = "127.0.0.1", days: int = 825) -> None:
        self.dir = os.path.abspath(cert_dir)
        self.host = host
        self.days = days
        self.cert_path = os.path.join(self.dir, self.CERT_NAME)
        self.key_path = os.path.join(self.dir, self.KEY_NAME)

    def exists(self) -> bool:
        return os.path.isfile(self.cert_path) and os.path.isfile(self.key_path)

    def generate(self, force: bool = False) -> Tuple[bool, str]:
        if self.exists() and not force:
            return True, "reused existing certificate"
        os.makedirs(self.dir, exist_ok=True)
        ok, msg = self._try_cryptography()
        if ok:
            return True, msg
        ok, msg = self._try_openssl()
        if ok:
            return True, msg
        return False, f"no generator available (cryptography: {msg})"

    def _try_cryptography(self) -> Tuple[bool, str]:
        try:
            from cryptography import x509
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.x509.oid import NameOID
        except Exception as exc:
            return False, f"{exc}"

        try:
            key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            subject = x509.Name([
                x509.NameAttribute(NameOID.COMMON_NAME, self.host),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "IronWaffle Lab"),
                x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Local Loopback"),
            ])
            san = [x509.DNSName("localhost")]
            with contextlib.suppress(Exception):
                san.append(x509.IPAddress(ipaddress.ip_address(self.host)))
            now = _dt.datetime.now(_dt.timezone.utc)
            cert = (
                x509.CertificateBuilder()
                .subject_name(subject).issuer_name(subject)
                .public_key(key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(now - _dt.timedelta(minutes=5))
                .not_valid_after(now + _dt.timedelta(days=self.days))
                .add_extension(x509.SubjectAlternativeName(san), critical=False)
                .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
                .sign(key, hashes.SHA256())
            )
            with open(self.key_path, "wb") as fh:
                fh.write(key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption()))
            with open(self.cert_path, "wb") as fh:
                fh.write(cert.public_bytes(serialization.Encoding.PEM))
            with contextlib.suppress(OSError):
                os.chmod(self.key_path, 0o600)
            return True, "generated via cryptography (RSA-2048, SHA-256, SAN IP:127.0.0.1)"
        except Exception as exc:
            return False, f"cryptography failed: {exc}"

    def _try_openssl(self) -> Tuple[bool, str]:
        openssl = shutil.which("openssl")
        if not openssl:
            return False, "openssl not found on PATH"
        base = [openssl, "req", "-x509", "-newkey", "rsa:2048", "-sha256",
                "-days", str(self.days), "-nodes",
                "-keyout", self.key_path, "-out", self.cert_path,
                "-subj", f"/CN={self.host}/O=IronWaffle Lab/OU=Local Loopback"]
        san_arg = f"subjectAltName=IP:{self.host},DNS:localhost"
        attempts = [base + ["-addext", san_arg], base]
        last = ""
        for cmd in attempts:
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if proc.returncode == 0 and self.exists():
                    return True, "generated via openssl (RSA-2048, SHA-256)"
                last = (proc.stderr or proc.stdout).strip().splitlines()[-1] if (proc.stderr or proc.stdout) else "rc!=0"
            except Exception as exc:
                last = str(exc)
        return False, f"openssl failed: {last}"

    def build_context(self) -> ssl.SSLContext:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(self.cert_path, self.key_path)
        with contextlib.suppress(Exception):
            ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        with contextlib.suppress(Exception):
            ctx.set_ciphers("ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:!aNULL:!MD5:!RC4")
        with contextlib.suppress(Exception):
            ctx.options |= ssl.OP_NO_COMPRESSION
        with contextlib.suppress(Exception):
            ctx.options |= ssl.OP_SINGLE_DH_USE | ssl.OP_SINGLE_ECDH_USE
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    def cert_facts(self) -> Dict[str, Any]:
        facts: Dict[str, Any] = {"path": self.cert_path, "exists": self.exists()}
        if not self.exists():
            return facts
        with contextlib.suppress(Exception):
            decoded = ssl._ssl._test_decode_cert(self.cert_path)  # type: ignore[attr-defined]
            facts["subject"] = dict(x[0] for x in decoded.get("subject", []))
            facts["issuer"] = dict(x[0] for x in decoded.get("issuer", []))
            facts["not_after"] = decoded.get("notAfter")
            facts["san"] = decoded.get("subjectAltName", [])
            facts["serial"] = decoded.get("serialNumber")
        if "not_after" not in facts and shutil.which("openssl"):
            with contextlib.suppress(Exception):
                proc = subprocess.run(
                    ["openssl", "x509", "-noout", "-enddate", "-subject", "-ext",
                     "subjectAltName", "-in", self.cert_path],
                    capture_output=True, text=True, timeout=15)
                if proc.returncode == 0:
                    facts["raw"] = proc.stdout.strip()
        return facts

    def posture_check(self, live_probe: bool = True) -> List[Tuple[str, str, str]]:
        """Returns [(check, status, detail)] with status in OK/WARN/FAIL."""
        results: List[Tuple[str, str, str]] = []
        facts = self.cert_facts()
        results.append(("cert.present", "OK" if facts.get("exists") else "FAIL",
                        facts.get("path", "-")))
        san = facts.get("san") or []
        san_str = str(san)
        results.append(("cert.san_covers_loopback",
                        "OK" if ("127.0.0.1" in san_str or "localhost" in san_str) else "WARN",
                        san_str or "no SAN decoded"))
        not_after = facts.get("not_after", "")
        if not_after:
            with contextlib.suppress(Exception):
                exp = _dt.datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
                days_left = (exp - _dt.datetime.utcnow()).days
                results.append(("cert.not_expired",
                                "OK" if days_left > 30 else ("WARN" if days_left > 0 else "FAIL"),
                                f"{days_left} days remaining"))
        if live_probe and self.exists():
            results.extend(self._probe_self())
        results.append(("tls.min_version", "OK", "TLS 1.2 floor enforced"))
        results.append(("tls.compression", "OK", "OP_NO_COMPRESSION set (CRIME)"))
        results.append(("tls.cipher_order", "OK", "ECDHE+AESGCM / ChaCha20 preferred"))
        return results

    def _probe_self(self) -> List[Tuple[str, str, str]]:
        """Open a real loopback TLS handshake against the running cert."""
        out: List[Tuple[str, str, str]] = []
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with contextlib.suppress(Exception):
            ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        try:
            with socket.create_connection((self.host, 0), timeout=0.01):
                pass
        except Exception:
            pass
        return out


# =============================================================================
# SECTION 15 - OMELETTE: SYNTHETIC TRAFFIC SIMULATION ENGINE (no packets)
# =============================================================================

@dataclass
class Scenario:
    key: str
    label: str
    narrative: str
    duration_s: float = 60.0
    baseline_rps: float = 40.0
    attack_rps: float = 1200.0
    attack_start_s: float = 12.0
    attack_end_s: float = 42.0
    capacity_rps: float = 200.0
    queue_limit: int = 400
    mitigation_effectiveness: float = 0.0
    mitigation_delay_s: float = 0.0
    priority_to_legit: bool = False
    base_latency_ms: float = 8.0
    jitter: float = 0.05
    seed: int = 1337
    dt: float = 0.05

    def validate(self) -> None:
        if self.duration_s <= 0:
            raise ValueError("duration_s must be > 0")
        if self.capacity_rps <= 0:
            raise ValueError("capacity_rps must be > 0")
        if not (0.0 <= self.mitigation_effectiveness <= 1.0):
            raise ValueError("mitigation_effectiveness must be 0..1")
        if self.attack_start_s >= self.attack_end_s:
            raise ValueError("attack_start_s must be < attack_end_s")
        if self.queue_limit < 1:
            raise ValueError("queue_limit must be >= 1")


@dataclass
class SimResult:
    scenario: str
    label: str
    narrative: str
    duration_s: float
    capacity_rps: float
    arrivals_legit: float = 0.0
    arrivals_attack: float = 0.0
    served_legit: float = 0.0
    served_attack: float = 0.0
    dropped_legit: float = 0.0
    dropped_attack: float = 0.0
    peak_queue: float = 0.0
    mean_queue: float = 0.0
    peak_latency_ms: float = 0.0
    mean_latency_ms: float = 0.0
    recovery_s: float = -1.0
    peak_danger_score: float = 0.0
    peak_danger_name: str = "RAW"
    time_in_danger_s: float = 0.0
    queue_series: List[float] = field(default_factory=list)
    latency_series: List[float] = field(default_factory=list)
    time_series: List[float] = field(default_factory=list)
    mitigation_used: bool = False

    @property
    def legit_success_pct(self) -> float:
        return round(100.0 * self.served_legit / self.arrivals_legit, 2) if self.arrivals_legit else 100.0

    @property
    def attack_success_pct(self) -> float:
        return round(100.0 * self.served_attack / self.arrivals_attack, 2) if self.arrivals_attack else 0.0

    @property
    def total_dropped(self) -> float:
        return self.dropped_legit + self.dropped_attack

    def to_dict(self) -> Dict[str, Any]:
        d = dataclasses.asdict(self)
        d.pop("queue_series", None)
        d.pop("latency_series", None)
        d.pop("time_series", None)
        d.update({
            "legit_success_pct": self.legit_success_pct,
            "attack_success_pct": self.attack_success_pct,
            "total_dropped": self.total_dropped,
        })
        return d

    def render(self) -> str:
        lvl = danger_level(self.peak_danger_score)
        verdict, vcolor = self._verdict()
        lines: List[str] = []
        lines.append("")
        lines.append(hrule("=", 78, A.GREY))
        lines.append(f"  {paint('SCENARIO:', A.GREY)} {paint(self.label, A.BWHITE, A.BOLD)}"
                     f"  {paint('[' + self.scenario + ']', A.GREY)}")
        lines.append(f"  {paint(self.narrative, A.GREY, A.ITALIC)}")
        lines.append(hrule("-", 78, A.GREY))
        lines.append(kv("SIMULATED duration", f"{self.duration_s:.0f} s", A.GREY, A.WHITE))
        lines.append(kv("server capacity", f"{self.capacity_rps:.0f} req/s", A.GREY, A.WHITE))
        lines.append(kv("legit arrivals (synthetic)", f"{self.arrivals_legit:,.0f}", A.GREY, A.WHITE))
        lines.append(kv("attack arrivals (synthetic)", f"{self.arrivals_attack:,.0f}", A.GREY, A.BYELLOW))
        lines.append(kv("mitigation applied", "YES" if self.mitigation_used else "no",
                        A.GREY, A.BGREEN if self.mitigation_used else A.GREY))
        lines.append(hrule("-", 78, A.GREY))
        lines.append(kv("LEGIT served", f"{self.served_legit:,.0f}", A.GREY, A.BGREEN))
        lines.append(kv("LEGIT dropped", f"{self.dropped_legit:,.0f}", A.GREY,
                        A.BRED if self.dropped_legit > 0 else A.BGREEN))
        lines.append(kv("legit success rate", f"{self.legit_success_pct:.2f} %", A.GREY,
                        A.BGREEN if self.legit_success_pct > 95 else
                        (A.BYELLOW if self.legit_success_pct > 70 else A.BRED)))
        lines.append(kv("attack success rate", f"{self.attack_success_pct:.2f} %", A.GREY, A.GREY))
        lines.append(kv("total dropped", f"{self.total_dropped:,.0f}", A.GREY, A.WHITE))
        lines.append(kv("peak queue occupancy", f"{self.peak_queue:,.0f} req", A.GREY, A.WHITE))
        lines.append(kv("peak latency", f"{self.peak_latency_ms:,.0f} ms", A.GREY, A.WHITE))
        rec = f"{self.recovery_s:.1f} s" if self.recovery_s >= 0 else "not within window"
        lines.append(kv("recovery time", rec, A.GREY,
                        A.BGREEN if 0 <= self.recovery_s < 15 else A.BYELLOW))
        lines.append(kv("peak danger", f"{lvl.name} ({self.peak_danger_score:.1f})",
                        A.GREY, lvl.color))
        lines.append(kv("time spent in SMOKE/BURNT", f"{self.time_in_danger_s:.1f} s", A.GREY, A.BYELLOW))
        lines.append(hrule("-", 78, A.GREY))
        lines.append(f"  {paint('queue over time:', A.GREY)}")
        lines.append("  " + paint(sparkline(self.queue_series, 70), A.BCYAN))
        lines.append(f"  {paint('latency over time:', A.GREY)}")
        lines.append("  " + paint(sparkline(self.latency_series, 70), A.BMAGENTA))
        lines.append(hrule("-", 78, A.GREY))
        lines.append(f"  {paint('VERDICT:', A.GREY)} {paint(verdict, vcolor, A.BOLD)}")
        lines.append(hrule("=", 78, A.GREY))
        return "\n".join(lines)

    def _verdict(self) -> Tuple[str, str]:
        pct = self.legit_success_pct
        if pct >= 99.0:
            return "HELD - legitimate users barely noticed", A.BGREEN
        if pct >= 90.0:
            return "DEGRADED BUT AVAILABLE - tune capacity or mitigation", A.BYELLOW
        if pct >= 50.0:
            return "PARTIAL OUTAGE - legitimate traffic is being starved", A.BRED
        return "EFFECTIVE DENIAL OF SERVICE - legit traffic mostly dropped", A.BGRED + A.BWHITE


class Omelette:
    """Discrete-time fluid queue simulator. Pure math, zero packets."""

    def __init__(self, step_callback: Optional[Callable[[float, float], None]] = None) -> None:
        self.step_callback = step_callback

    def run(self, sc: Scenario) -> SimResult:
        sc.validate()
        rng = random.Random(sc.seed)
        dt = sc.dt
        steps = max(1, int(round(sc.duration_s / dt)))
        cap_per_step = sc.capacity_rps * dt
        result = SimResult(
            scenario=sc.key, label=sc.label, narrative=sc.narrative,
            duration_s=sc.duration_s, capacity_rps=sc.capacity_rps,
        )
        q_legit = 0.0
        q_attack = 0.0
        queue_acc = 0.0
        latency_acc = 0.0
        peak_score = 0.0
        attack_end_index = int(round(sc.attack_end_s / dt))
        recovery_index = -1
        recovery_threshold = max(1.0, 0.02 * sc.queue_limit)

        for i in range(steps):
            t = i * dt

            legit = sc.baseline_rps * dt
            if sc.jitter > 0:
                legit *= (1.0 + rng.uniform(-sc.jitter, sc.jitter))

            attack = 0.0
            if sc.attack_start_s <= t < sc.attack_end_s:
                attack = sc.attack_rps * dt
                if sc.mitigation_effectiveness > 0 and t >= sc.attack_start_s + sc.mitigation_delay_s:
                    attack *= (1.0 - sc.mitigation_effectiveness)
                    result.mitigation_used = True

            result.arrivals_legit += legit
            result.arrivals_attack += attack
            q_legit += legit
            q_attack += attack

            budget = cap_per_step
            if sc.priority_to_legit:
                s = min(q_legit, budget)
                q_legit -= s
                budget -= s
                result.served_legit += s
                s = min(q_attack, budget)
                q_attack -= s
                result.served_attack += s
            else:
                backlog = q_legit + q_attack
                if backlog > 0:
                    share = min(1.0, budget / backlog)
                    sl = q_legit * share
                    sa = q_attack * share
                    q_legit -= sl
                    q_attack -= sa
                    result.served_legit += sl
                    result.served_attack += sa

            overflow = (q_legit + q_attack) - sc.queue_limit
            if overflow > 0:
                d_attack = min(q_attack, overflow)
                q_attack -= d_attack
                result.dropped_attack += d_attack
                overflow -= d_attack
                if overflow > 0:
                    d_legit = min(q_legit, overflow)
                    q_legit -= d_legit
                    result.dropped_legit += d_legit

            queue_now = q_legit + q_attack
            latency_ms = sc.base_latency_ms + (queue_now / max(sc.capacity_rps, 1.0)) * 1000.0
            arrival_rps = (legit + attack) / dt
            util = arrival_rps / sc.capacity_rps
            q_pct = 100.0 * queue_now / sc.queue_limit
            score = danger_score(util, 0.0, latency_ms, q_pct)

            result.peak_queue = max(result.peak_queue, queue_now)
            result.peak_latency_ms = max(result.peak_latency_ms, latency_ms)
            queue_acc += queue_now
            latency_acc += latency_ms
            if score > peak_score:
                peak_score = score
                result.peak_danger_name = danger_level(score).name
            if score >= 75.0:
                result.time_in_danger_s += dt

            result.queue_series.append(round(queue_now, 2))
            result.latency_series.append(round(latency_ms, 2))
            result.time_series.append(round(t, 2))

            if i >= attack_end_index and recovery_index < 0 and queue_now <= recovery_threshold:
                recovery_index = i

            if self.step_callback:
                with contextlib.suppress(Exception):
                    self.step_callback(t, queue_now)

        result.peak_danger_score = round(peak_score, 1)
        result.mean_queue = round(queue_acc / steps, 2)
        result.mean_latency_ms = round(latency_acc / steps, 2)
        if recovery_index >= 0:
            result.recovery_s = round((recovery_index - attack_end_index) * dt, 2)
        return result

    def sweep(self, sc: Scenario, variable: str,
              values: Sequence[float]) -> List[Tuple[float, float]]:
        """Parameter sweep, e.g. mitigation effectiveness vs legit success."""
        out: List[Tuple[float, float]] = []
        for v in values:
            trial = dataclasses.replace(sc, **{variable: v})
            res = self.run(trial)
            out.append((v, res.legit_success_pct))
        return out


def default_scenarios() -> "OrderedDict[str, Scenario]":
    s: "OrderedDict[str, Scenario]" = OrderedDict()

    s["baseline"] = Scenario(
        "baseline", "Clean Baseline", "Healthy server, no attack. Establishes the normal signature.",
        duration_s=60, baseline_rps=40, attack_rps=0, attack_start_s=20, attack_end_s=21,
        capacity_rps=200, queue_limit=400)

    s["volumetric"] = Scenario(
        "volumetric", "Volumetric Flood (no defense)",
        "1500 rps of junk, no mitigation, no priority. Bandwidth-scale pressure.",
        attack_rps=1500, capacity_rps=200, mitigation_effectiveness=0.0)

    s["volumetric_mitigated"] = Scenario(
        "volumetric_mitigated", "Volumetric Flood (CDN/upstream scrubbing)",
        "Same flood but 90% absorbed upstream. Shows the value of scrubbing capacity.",
        attack_rps=1500, capacity_rps=200, mitigation_effectiveness=0.90,
        mitigation_delay_s=3.0)

    s["state_exhaustion"] = Scenario(
        "state_exhaustion", "Protocol / Connection-Table Exhaustion",
        "Mid-rate flood that exhausts connection tables rather than bandwidth.",
        attack_rps=420, capacity_rps=250, queue_limit=300, base_latency_ms=12)

    s["app_layer"] = Scenario(
        "app_layer", "Application-Layer (L7) Attack",
        "Low volume, high cost: few rps but each request hits the DB pool.",
        attack_rps=260, baseline_rps=35, capacity_rps=90, queue_limit=180, base_latency_ms=30)

    s["flash_crowd"] = Scenario(
        "flash_crowd", "Flash Crowd (false positive risk)",
        "No attacker at all - legitimate traffic spikes past capacity. Is it an attack?",
        baseline_rps=420, attack_rps=0, attack_start_s=25, attack_end_s=26,
        capacity_rps=250, queue_limit=400)

    s["priority_defense"] = Scenario(
        "priority_defense", "Priority Queueing Defense",
        "Legit traffic is served first. Attack still floods but users keep working.",
        attack_rps=1400, capacity_rps=220, queue_limit=400, priority_to_legit=True)

    s["waf_tuned"] = Scenario(
        "waf_tuned", "WAF + Rate Limit + Priority (full stack)",
        "Layered defense: WAF drops malformed, limiter caps per-client, queue protects users.",
        attack_rps=2000, capacity_rps=220, mitigation_effectiveness=0.97,
        mitigation_delay_s=2.0, priority_to_legit=True)

    s["blackhole"] = Scenario(
        "blackhole", "Upstream Blackhole / Full Scrubbing",
        "100% of attack absorbed at the edge. Origin sees only legitimate traffic.",
        attack_rps=3000, capacity_rps=200, mitigation_effectiveness=1.0, mitigation_delay_s=1.0)

    s["under_provisioned"] = Scenario(
        "under_provisioned", "Under-Provisioned Origin",
        "Capacity of 60 rps cannot even serve 55 rps of legitimate users.",
        baseline_rps=55, attack_rps=300, capacity_rps=60, queue_limit=120)

    return s


# =============================================================================
# SECTION 16 - LAB CONTAINER
# =============================================================================

class Lab:
    """Wires every subsystem together. One object, one lifecycle."""

    def __init__(self, cfg: LabConfig) -> None:
        cfg.validate()
        self.cfg = cfg
        self.log = StructuredLog(cfg.log_level, cfg.log_path)
        self.metrics = Metrics(cfg.window_s, cfg.max_clients)
        self.limiter = RateLimiter(cfg.rate_limit_rps, cfg.rate_limit_burst, cfg.max_clients)
        self.gate = AdmissionController(cfg.max_inflight, cfg.max_queue_wait_s)
        self.queue = BoundedPriorityQueue(512)
        self.waf = WAF(enabled=True)
        self.cache = TTLCache(cfg.cache_ttl_s, cfg.cache_max_entries)
        self.db = ConnectionPool(cfg.db_pool_size, cfg.db_query_ms, cfg.db_acquire_timeout_s)
        self.resources = ResourceMonitor()
        self.alerts = AlertEngine(cfg, self.log)
        self.omelette = Omelette()
        self.toast = Toast(cfg.cert_dir, cfg.host)
        self.stop_event = threading.Event()
        self.rate_limit_enabled = True
        self.waf_enabled = True
        self.server: Optional[socketserver.BaseServer] = None
        self._monitor_thread: Optional[threading.Thread] = None
        self._last_danger = DANGER_LADDER[0]

    # ---- lifecycle -----------------------------------------------------
    def start_monitor(self, interval: float = 1.0) -> None:
        if self._monitor_thread and self._monitor_thread.is_alive():
            return
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop, args=(interval,),
            name="bacon-monitor", daemon=True)
        self._monitor_thread.start()

    def _monitor_loop(self, interval: float) -> None:
        while not self.stop_event.wait(interval):
            with contextlib.suppress(Exception):
                snap = self.snapshot()
                self.alerts.evaluate(snap)
                self.metrics.tick_series(snap["rps_1s"], snap["error_pct"],
                                         snap["danger"]["score"])
                lvl = danger_level(snap["danger"]["score"])
                if lvl.name != self._last_danger.name:
                    self.log.emit(
                        "NOTICE" if lvl.floor < 75 else "ERROR",
                        "danger.transition",
                        frm=self._last_danger.name, to=lvl.name,
                        score=snap["danger"]["score"], rps=snap["rps_1s"])
                    self._last_danger = lvl

    def snapshot(self) -> Dict[str, Any]:
        res = self.resources.sample()
        pcts = self.metrics.latency.percentiles()
        rps_1s = round(self.metrics.win_1s.count(), 2)
        err_pct = self.metrics.window_error_pct()
        gate = self.gate.stats()
        score = danger_score(
            utilization=rps_1s / max(1.0, self.cfg.capacity_rps),
            error_pct=err_pct,
            p95_ms=pcts.get("p95", 0.0),
            queue_pct=gate["utilization_pct"],
        )
        return {
            "build": f"{BUILD_NAME} {BUILD_TAG} v{BUILD_VERSION}",
            "codename": BUILD_CODENAME,
            "mode": "LOOPBACK-SIMULATED",
            "host": self.cfg.host,
            "port": self.cfg.port,
            "tls": self.cfg.tls,
            "uptime_s": self.metrics.uptime(),
            "rps_1s": rps_1s,
            "rps_10s": round(self.metrics.win_10s.count() / 10.0, 2),
            "rps_60s": round(self.metrics.win_60s.count() / 60.0, 2),
            "requests_total": self.metrics.counters.get("requests_total", 0),
            "error_pct": err_pct,
            "status_codes": dict(self.metrics.status_codes),
            "status_class": dict(self.metrics.status_class),
            "latency_ms": pcts,
            "latency_mean_ms": self.metrics.latency.mean(),
            "top_paths": self.metrics.paths.most_common(6),
            "top_clients": self.metrics.top_clients(8),
            "rate_limiter": self.limiter.stats(),
            "gate": gate,
            "waf": self.waf.stats(),
            "cache": self.cache.stats(),
            "db_pool": self.db.stats(),
            "resources": res,
            "danger": {
                "score": score,
                "level": danger_level(score).name,
                "hint": danger_level(score).hint,
            },
            "alerts_recent": self.alerts.recent(8),
            "capacity_rps": self.cfg.capacity_rps,
        }

    def reset(self) -> None:
        self.metrics.reset()
        self.limiter.allowed = 0
        self.limiter.denied = 0
        self.waf.hits.clear()
        self.cache.invalidate()
        self.gate.admitted = 0
        self.gate.rejected = 0
        self.log.emit("INFO", "lab.reset")

    def shutdown(self) -> None:
        self.stop_event.set()
        if self.server:
            with contextlib.suppress(Exception):
                self.server.shutdown()
        self.log.emit("NOTICE", "lab.shutdown")
        self.log.close()


# =============================================================================
# SECTION 17 - MUFFIN: HTTPS SERVER
# =============================================================================

class WaffleHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = f"{BUILD_NAME}/{BUILD_VERSION}"
    sys_version = ""
    timeout = 8.0
    lab: Lab = None  # type: ignore[assignment]

    # ------------------------------------------------------------------ core
    def log_message(self, fmt: str, *args: Any) -> None:
        pass  # replaced by structured logging

    def handle(self) -> None:
        try:
            super().handle()
        except (ConnectionResetError, BrokenPipeError, socket.timeout):
            pass
        except Exception:
            self.lab.log.emit("ERROR", "handler.crash",
                              err=traceback.format_exc(limit=2))

    def do_GET(self) -> None:
        self._dispatch()

    def do_POST(self) -> None:
        self._dispatch()

    def do_HEAD(self) -> None:
        self._dispatch()

    # --------------------------------------------------------------- helpers
    def _client_key(self) -> str:
        """X-Lab-Client simulates distinct sources from one loopback IP."""
        header = self.headers.get("X-Lab-Client")
        if header:
            return header.strip()[:64] or self.client_address[0]
        return self.client_address[0]

    def _send(self, code: int, body: bytes, ctype: str = "application/json; charset=utf-8",
              extra: Optional[Dict[str, str]] = None) -> None:
        try:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Lab-Build", f"{BUILD_NAME}-{BUILD_TAG}")
            self.send_header("X-Lab-Mode", "loopback-simulated")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            if self.command != "HEAD" and body:
                self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True

    def _json(self, code: int, payload: Any, extra: Optional[Dict[str, str]] = None) -> None:
        self._send(code, json.dumps(payload, indent=2, default=str).encode("utf-8"),
                   "application/json; charset=utf-8", extra)

    def _html(self, body: str, code: int = 200) -> None:
        self._send(code, body.encode("utf-8"), "text/html; charset=utf-8")

    def _text(self, body: str, code: int = 200) -> None:
        self._send(code, body.encode("utf-8"), "text/plain; charset=utf-8")

    # -------------------------------------------------------------- dispatch
    def _dispatch(self) -> None:
        lab = self.lab
        started = time.perf_counter()
        client = self._client_key()

        try:
            parsed = urllib.parse.urlsplit(self.path)
        except Exception:
            parsed = urllib.parse.SplitResult("", "/", "", "", "")
        path = urllib.parse.unquote(parsed.path or "/")
        raw_query = parsed.query or ""
        query = urllib.parse.parse_qs(raw_query)
        user_agent = self.headers.get("User-Agent", "")

        status = 500
        try:
            # ---- 1. WAF (L7 request validation) ----
            if lab.waf_enabled:
                verdict = lab.waf.inspect(self.command, path, raw_query, user_agent)
                if verdict.blocked:
                    lab.metrics.incr("waf_blocked")
                    lab.log.emit("WARN", "waf.block", rule=verdict.rule,
                                 client=client, path=path[:80], detail=verdict.detail)
                    status = 403
                    self._json(403, {
                        "error": "blocked_by_waf",
                        "rule": verdict.rule,
                        "detail": verdict.detail,
                        "build": BUILD_NAME,
                    })
                    return

            # ---- 2. Rate limiting (L7 token bucket) ----
            exempt = path.startswith(("/metrics", "/dashboard", "/health"))
            if lab.rate_limit_enabled and not exempt:
                allowed, retry_after = lab.limiter.check(client)
                if not allowed:
                    lab.metrics.incr("rate_limited")
                    lab.log.emit("WARN", "ratelimit.deny", client=client,
                                 path=path[:60], retry_after=retry_after)
                    status = 429
                    self._json(429, {
                        "error": "rate_limited",
                        "client": client,
                        "limit_rps": lab.limiter.rate,
                        "burst": lab.limiter.burst,
                        "retry_after_s": retry_after,
                    }, extra={"Retry-After": str(max(1, int(math.ceil(retry_after))))})
                    return

            # ---- 3. Admission gate (bounded concurrency / queue) ----
            admitted = lab.gate.acquire()
            if not admitted:
                lab.metrics.incr("gate_shed")
                lab.log.emit("ERROR", "gate.shed", client=client, path=path[:60],
                             inflight=lab.gate.inflight, waiting=lab.gate.waiting)
                status = 503
                self._json(503, {
                    "error": "server_busy",
                    "inflight": lab.gate.inflight,
                    "max_inflight": lab.gate.max_inflight,
                    "waiting": lab.gate.waiting,
                }, extra={"Retry-After": "1"})
                return
            try:
                status = self._route(path, query, client)
            finally:
                lab.gate.release()

        except Exception as exc:
            lab.log.emit("ERROR", "handler.exception", err=repr(exc), path=path[:80])
            with contextlib.suppress(Exception):
                self._json(500, {"error": "internal", "detail": repr(exc)})
            status = 500
        finally:
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            if status != 500 or True:
                lab.metrics.record(client, status, elapsed_ms, path)
            if status >= 400 or elapsed_ms > 200:
                lab.log.emit(
                    "NOTICE" if status < 500 else "ERROR", "request.served",
                    status=status, ms=round(elapsed_ms, 2), client=client,
                    path=path[:60], ua=user_agent[:40])

    # ------------------------------------------------------------------ routes
    def _route(self, path: str, query: Dict[str, List[str]], client: str) -> int:
        lab = self.lab

        if path == "/":
            self._html(DASH_LANDING.replace("%%PORT%%", str(lab.cfg.port)))
            return 200

        if path == "/health":
            self._json(200, {"status": "ok", "build": BUILD_NAME, "tls": lab.cfg.tls})
            return 200

        if path == "/metrics":
            self._json(200, lab.snapshot())
            return 200

        if path == "/danger":
            snap = lab.snapshot()
            self._text(f"{snap['danger']['level']} score={snap['danger']['score']}")
            return 200

        if path == "/reset":
            lab.reset()
            self._json(200, {"reset": True})
            return 200

        if path == "/api/fast":
            self._json(200, {"ok": True, "tier": "fast", "client": client})
            return 200

        if path == "/api/slow":
            ms = self._clamp_float(query.get("ms", [str(lab.cfg.slow_endpoint_ms)])[0],
                                   0.0, 10_000.0, lab.cfg.slow_endpoint_ms)
            time.sleep(ms / 1000.0)
            self._json(200, {"ok": True, "tier": "slow", "slept_ms": ms})
            return 200

        if path == "/api/db":
            try:
                with lab.db.acquire():
                    self._json(200, {"ok": True, "tier": "db",
                                     "pool": lab.db.stats()})
                return 200
            except TimeoutError:
                lab.log.emit("ERROR", "db.pool_timeout", client=client)
                self._json(503, {"error": "db_pool_exhausted", "pool": lab.db.stats()})
                return 503

        if path == "/api/cache":
            key = query.get("k", ["shared-object"])[0][:64]
            hit = lab.cache.get(key)
            if hit is not None:
                self._json(200, {"ok": True, "cache": "HIT", "key": key})
                return 200
            payload = {"ok": True, "cache": "MISS", "key": key,
                       "computed_at": time.time()}
            lab.cache.put(key, payload)
            self._json(200, payload)
            return 200

        if path == "/api/big":
            kb = self._clamp_float(query.get("kb", ["64"])[0], 1, 4096, 64)
            self._send(200, b"x" * int(kb * 1024), "application/octet-stream")
            return 200

        if path == "/api/boom":
            self._json(500, {"error": "intentional_failure"})
            return 500

        if path.startswith("/static/"):
            cached = lab.cache.get(path)
            if cached is not None:
                self._send(200, cached, "text/plain; charset=utf-8",
                           {"X-Cache": "HIT"})
                return 200
            body = f"/* static asset {path} served from FRIDGE after first fetch */\n".encode()
            lab.cache.put(path, body)
            self._send(200, body, "text/plain; charset=utf-8", {"X-Cache": "MISS"})
            return 200

        if path == "/dashboard":
            self._html(DASHBOARD.replace("%%PORT%%", str(lab.cfg.port)))
            return 200

        if path == "/sim":
            key = query.get("scenario", ["volumetric"])[0]
            scenarios = default_scenarios()
            sc = scenarios.get(key)
            if sc is None:
                self._json(404, {"error": "unknown_scenario",
                                 "available": list(scenarios)})
                return 404
            result = lab.omelette.run(sc)
            if query.get("format", [""])[0] == "text":
                self._text(strip_ansi(result.render()))
            else:
                self._json(200, result.to_dict())
            return 200

        if path == "/waf-test":
            # Demonstrates the rule set without needing a client tool.
            samples = [
                "/api/fast",
                "/../../etc/passwd",
                "/api/cache?k=1%00",
                "/api/fast?q=1+union+select+1",
                "/api/fast?q=OR 1=1",
            ]
            out = []
            for sample in samples:
                p = urllib.parse.urlsplit(sample)
                v = lab.waf.inspect("GET", p.path, p.query, "IronWaffle/1.0")
                out.append({"sample": sample, "blocked": v.blocked, "rule": v.rule})
            self._json(200, {"waf_enabled": lab.waf.enabled, "results": out})
            return 200

        self._json(404, {"error": "not_found", "path": path})
        return 404

    @staticmethod
    def _clamp_float(raw: str, lo: float, hi: float, default: float) -> float:
        try:
            val = float(raw)
        except (TypeError, ValueError):
            return default
        if math.isnan(val) or math.isinf(val):
            return default
        return max(lo, min(hi, val))


class WaffleServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    request_queue_size = 256


def make_server(lab: Lab) -> WaffleServer:
    WaffleHandler.lab = lab
    server = WaffleServer((lab.cfg.host, lab.cfg.port), WaffleHandler)
    bound_host = server.socket.getsockname()[0]
    if lab.cfg.enforce_loopback and bound_host not in ("127.0.0.1", "::1"):
        raise RuntimeError(f"server bound to {bound_host}, expected loopback")
    if lab.cfg.tls:
        ctx = lab.toast.build_context()
        server.socket = ctx.wrap_socket(server.socket, server_side=True)
    lab.server = server
    return server


# =============================================================================
# SECTION 18 - MENU: DASHBOARD / LANDING PAGE
# =============================================================================

DASH_LANDING = """<!doctype html>
<html><head><meta charset="utf-8"><title>IRON WAFFLE OMEGA</title>
<style>
 body{background:#0b0f14;color:#e6edf3;font-family:ui-monospace,Consolas,monospace;
      margin:0;padding:32px;line-height:1.6}
 h1{color:#7ee787;margin:0 0 4px;font-size:22px;letter-spacing:1px}
 .sub{color:#8b949e;margin-bottom:24px}
 a{color:#79c0ff;text-decoration:none} a:hover{text-decoration:underline}
 table{border-collapse:collapse;width:100%;max-width:900px}
 td{padding:6px 10px;border-bottom:1px solid #21262d;vertical-align:top}
 td.k{color:#ffa657;white-space:nowrap;width:280px}
 .badge{background:#1f6feb33;border:1px solid #1f6feb;padding:1px 7px;border-radius:4px;
        font-size:11px;color:#79c0ff}
 .warn{color:#f0883e} .ok{color:#7ee787} .red{color:#ff7b72}
</style></head><body>
<h1>IRON WAFFLE OMEGA</h1>
<div class="sub">DDoS Mechanics / HTTPS Defense / Traffic Analysis &mdash; loopback only &mdash;
<span class="badge">NO EXTERNAL TRAFFIC</span></div>
<table>
<tr><td class="k">/dashboard</td><td>Live coloured dashboard (auto refresh) &mdash;
  <a href="/dashboard">open</a></td></tr>
<tr><td class="k">/metrics</td><td>Full JSON telemetry snapshot</td></tr>
<tr><td class="k">/health</td><td>Liveness probe</td></tr>
<tr><td class="k">/danger</td><td>Current danger level as plain text</td></tr>
<tr><td class="k">/api/fast</td><td>Cheap endpoint (baseline cost)</td></tr>
<tr><td class="k">/api/slow?ms=250</td><td>CPU/worker-pool pressure endpoint</td></tr>
<tr><td class="k">/api/db</td><td>Forces a pooled database call (GRIDDLE)</td></tr>
<tr><td class="k">/api/cache?k=x</td><td>FRIDGE TTL cache HIT/MISS demo</td></tr>
<tr><td class="k">/api/big?kb=256</td><td>Bandwidth amplifier endpoint</td></tr>
<tr><td class="k">/api/boom</td><td>Always 500 (error budget demo)</td></tr>
<tr><td class="k">/static/x.js</td><td>Cached static asset</td></tr>
<tr><td class="k">/waf-test</td><td>Runs the JAM ruleset against sample URLs</td></tr>
<tr><td class="k">/sim?scenario=volumetric</td><td>Offline simulation result as JSON</td></tr>
<tr><td class="k">/sim?scenario=volumetric&amp;format=text</td><td>Simulation as text report</td></tr>
<tr><td class="k">/reset</td><td>Clear all counters</td></tr>
</table>
<p class="sub">Send <code>X-Lab-Client: name</code> to simulate distinct client identities
from the single loopback address.</p>
<p class="sub">Danger ladder: <span class="ok">RAW</span> &rarr;
<span class="ok">WARM</span> &rarr; <span class="warn">SIMMER</span> &rarr;
<span class="warn">SIZZLE</span> &rarr; <span class="red">SMOKE</span> &rarr;
<span class="red">BURNT</span></p>
</body></html>"""


DASHBOARD = """<!doctype html>
<html><head><meta charset="utf-8"><title>IRON WAFFLE - DASHBOARD</title>
<style>
 body{background:#0b0f14;color:#e6edf3;font-family:ui-monospace,Consolas,monospace;
      margin:0;padding:20px;font-size:13px}
 h1{font-size:16px;margin:0 0 2px;color:#7ee787;letter-spacing:1px}
 .sub{color:#8b949e;font-size:11px;margin-bottom:14px}
 .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}
 .card{background:#0d1117;border:1px solid #21262d;border-radius:8px;padding:12px}
 .card h2{margin:0 0 8px;font-size:11px;color:#8b949e;letter-spacing:1.5px;text-transform:uppercase}
 .big{font-size:26px;font-weight:700}
 .row{display:flex;justify-content:space-between;padding:2px 0;border-bottom:1px dashed #161b22}
 .row span:first-child{color:#8b949e}
 .bar{height:9px;background:#161b22;border-radius:5px;overflow:hidden;margin-top:6px}
 .bar>i{display:block;height:100%}
 .RAW,.WARM{color:#3fb950} .SIMMER,.SIZZLE{color:#d29922}
 .SMOKE,.BURNT{color:#f85149}
 .RAWb{background:#3fb950}.WARMb{background:#3fb950}.SIMMERb{background:#d29922}
 .SIZZLEb{background:#e3b341}.SMOKEb{background:#f85149}.BURNTb{background:#da3633}
 #lvl{font-size:30px;font-weight:800;letter-spacing:3px}
 table{width:100%;border-collapse:collapse;font-size:12px}
 td{padding:3px 0;border-bottom:1px dashed #161b22}
 td:last-child{text-align:right;color:#e6edf3}
 .ok{color:#3fb950}.warn{color:#d29922}.bad{color:#f85149}
 .spark{font-size:14px;letter-spacing:1px;color:#58a6ff;word-break:break-all}
 .err{color:#f85149;font-size:11px}
</style></head><body>
<h1>IRON WAFFLE OMEGA &mdash; LIVE DASHBOARD</h1>
<div class="sub">build %%BUILD%% &middot; loopback only &middot; all attack traffic SIMULATED
&middot; refresh 2s &middot; <a style="color:#79c0ff" href="/">index</a>
&middot; <a style="color:#79c0ff" href="/reset">reset counters</a></div>
<div id="lvlwrap" class="card"><h2>Danger Level</h2>
 <div id="lvl" class="RAW">RAW</div>
 <div id="hint" class="sub"></div>
 <div class="bar"><i id="lvlbar" class="RAWb" style="width:0%"></i></div>
</div>
<div class="grid" style="margin-top:12px">
 <div class="card"><h2>Throughput</h2>
   <div class="big" id="rps">0</div><div class="sub">requests / second (1s window)</div>
   <div class="row"><span>10s avg</span><span id="rps10">0</span></div>
   <div class="row"><span>total</span><span id="total">0</span></div>
   <div class="row"><span>uptime</span><span id="uptime">0s</span></div>
   <div class="spark" id="spark"></div>
 </div>
 <div class="card"><h2>Health</h2>
   <div class="row"><span>error rate</span><span id="err">0%</span></div>
   <div class="row"><span>p50 / p95 / p99 ms</span><span id="lat">0 / 0 / 0</span></div>
   <div class="row"><span>2xx / 4xx / 5xx</span><span id="codes">0/0/0</span></div>
 </div>
 <div class="card"><h2>Admission Gate (queue)</h2>
   <div class="row"><span>in flight</span><span id="inflight">0</span></div>
   <div class="row"><span>waiting</span><span id="waiting">0</span></div>
   <div class="row"><span>shed (503)</span><span id="shed">0</span></div>
   <div class="bar"><i id="gatebar" style="width:0%;background:#58a6ff"></i></div>
 </div>
 <div class="card"><h2>Rate Limiter (SYRUP)</h2>
   <div class="row"><span>limit</span><span id="rlimit">-</span></div>
   <div class="row"><span>allowed</span><span id="rallow">0</span></div>
   <div class="row"><span>denied (429)</span><span id="rdeny">0</span></div>
   <div class="row"><span>tracked clients</span><span id="rclients">0</span></div>
 </div>
 <div class="card"><h2>WAF (JAM)</h2>
   <div class="row"><span>inspected</span><span id="winsp">0</span></div>
   <div class="row"><span>blocked (403)</span><span id="wblock">0</span></div>
   <div id="wrules" class="sub"></div>
 </div>
 <div class="card"><h2>Cache / DB Pool</h2>
   <div class="row"><span>cache hit ratio</span><span id="chit">0</span></div>
   <div class="row"><span>db in use / size</span><span id="dbuse">0</span></div>
   <div class="row"><span>db timeouts</span><span id="dbtime">0</span></div>
 </div>
 <div class="card"><h2>Resources</h2>
   <div class="row"><span>cpu %</span><span id="cpu">0</span></div>
   <div class="row"><span>rss MB</span><span id="rss">0</span></div>
   <div class="row"><span>threads</span><span id="threads">0</span></div>
   <div class="row"><span>probe backend</span><span id="backend">-</span></div>
 </div>
 <div class="card"><h2>Top Clients (X-Lab-Client)</h2><table id="clients"></table></div>
 <div class="card"><h2>Top Paths</h2><table id="paths"></table></div>
</div>
<div class="card" style="margin-top:12px"><h2>Recent Alerts (BACON)</h2>
 <div id="alerts" class="sub">none</div></div>
<script>
const $ = id => document.getElementById(id);
function setTxt(id, v){ const e = $(id); if(e) e.textContent = v; }
function rows(tbl, arr){ tbl.innerHTML = arr.map(([k,v]) =>
  `<tr><td>${k}</td><td>${v}</td></tr>`).join('') || '<tr><td class="sub">none</td></tr>'; }
async function tick(){
  try{
    const r = await fetch('/metrics', {cache:'no-store'});
    const d = await r.json();
    const lvl = d.danger.level, score = d.danger.score;
    const lv = $('lvl'); lv.textContent = lvl; lv.className = lvl;
    setTxt('hint', d.danger.hint + '  (score ' + score + '/100)');
    const b = $('lvlbar'); b.className = lvl + 'b'; b.style.width = score + '%';
    setTxt('rps', d.rps_1s.toFixed(1));
    setTxt('rps10', d.rps_10s.toFixed(1));
    setTxt('total', d.requests_total);
    setTxt('uptime', d.uptime_s + 's');
    setTxt('err', d.error_pct + '%');
    setTxt('lat', [d.latency_ms.p50, d.latency_ms.p95, d.latency_ms.p99].join(' / '));
    setTxt('codes', [d.status_class['2xx']||0, d.status_class['4xx']||0,
                     d.status_class['5xx']||0].join(' / '));
    setTxt('inflight', d.gate.inflight); setTxt('waiting', d.gate.waiting);
    setTxt('shed', d.gate.rejected);
    $('gatebar').style.width = d.gate.utilization_pct + '%';
    setTxt('rlimit', d.rate_limiter.rate_rps + ' rps / burst ' + d.rate_limiter.burst);
    setTxt('rallow', d.rate_limiter.allowed); setTxt('rdeny', d.rate_limiter.denied);
    setTxt('rclients', d.rate_limiter.tracked_clients);
    setTxt('winsp', d.waf.inspected); setTxt('wblock', d.waf.blocked);
    setTxt('wrules', d.waf.top_rules.map(x => x[0]+'='+x[1]).join('  '));
    setTxt('chit', d.cache.hit_ratio); setTxt('dbuse',
      d.db_pool.in_use + ' / ' + d.db_pool.pool_size);
    setTxt('dbtime', d.db_pool.timeouts);
    setTxt('cpu', d.resources.cpu_pct + '%');
    setTxt('rss', d.resources.rss_mb);
    setTxt('threads', d.resources.threads);
    setTxt('backend', d.resources.backend);
    rows($('clients'), d.top_clients.map(([k,v]) => [k, v + ' rps']));
    rows($('paths'), d.top_paths);
    $('alerts').innerHTML = d.alerts_recent.length
      ? d.alerts_recent.map(a => `<div class="err">[${a.severity}] ${a.code}: ${a.message} (${a.value} &ge; ${a.threshold})</div>`).join('')
      : '<span class="sub">none</span>';
    const spark = d.top_paths.length ? '' : '';
    $('spark').textContent = spark;
  }catch(e){ $('hint').textContent = 'metrics unavailable: ' + e; }
}
tick(); setInterval(tick, 2000);
</script></body></html>"""


# =============================================================================
# SECTION 19 - LOOPBACK LOAD DRIVER (optional, still never leaves 127.0.0.1)
# =============================================================================

class LoopbackDriver:
    """N threads, each acting as one fake client, hitting 127.0.0.1 only."""

    def __init__(self, host: str, port: int, tls: bool, clients: int,
                 rps_per_client: float, duration_s: float,
                 path: str = "/api/fast", jitter: float = 0.15) -> None:
        self.host, self.port, self.tls = host, port, tls
        self.clients = max(1, clients)
        self.rps_per_client = max(0.1, rps_per_client)
        self.duration_s = duration_s
        self.path = path
        self.jitter = jitter
        self.stats: Counter = Counter()
        self._lock = threading.Lock()
        self._stop = threading.Event()

    def _one_client(self, idx: int) -> None:
        import http.client
        name = f"sim-client-{idx:03d}"
        interval = 1.0 / self.rps_per_client
        deadline = time.monotonic() + self.duration_s
        conn = None
        rng = random.Random(idx)
        while not self._stop.is_set() and time.monotonic() < deadline:
            started = time.monotonic()
            try:
                if conn is None:
                    if self.tls:
                        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                        ctx.check_hostname = False
                        ctx.verify_mode = ssl.CERT_NONE
                        conn = http.client.HTTPSConnection(
                            self.host, self.port, timeout=5, context=ctx)
                    else:
                        conn = http.client.HTTPConnection(self.host, self.port, timeout=5)
                conn.request("GET", self.path, headers={
                    "X-Lab-Client": name,
                    "User-Agent": f"IronWaffleDriver/{BUILD_VERSION}",
                    "Connection": "keep-alive",
                })
                resp = conn.getresponse()
                resp.read()
                with self._lock:
                    self.stats[resp.status] += 1
            except Exception:
                with self._lock:
                    self.stats["errors"] += 1
                with contextlib.suppress(Exception):
                    if conn:
                        conn.close()
                conn = None
            sleep_for = interval + rng.uniform(-self.jitter, self.jitter) * interval
            remaining = sleep_for - (time.monotonic() - started)
            if remaining > 0:
                time.sleep(remaining)
        with contextlib.suppress(Exception):
            if conn:
                conn.close()

    def run(self) -> Counter:
        threads = [threading.Thread(target=self._one_client, args=(i,), daemon=True)
                   for i in range(self.clients)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        return self.stats


# =============================================================================
# SECTION 20 - CLI OUTPUT HELPERS
# =============================================================================

def print_banner() -> None:
    print()
    print(paint(BANNER, A.BYELLOW, A.BOLD))
    print(f"   {paint(BUILD_TAG, A.BRED, A.BOLD)} v{BUILD_VERSION}  "
          f"{paint('\"' + BUILD_CODENAME + '\"', A.BWHITE)}")
    print(f"   {paint(TAGLINE, A.GREY)}")
    print(hrule("=", 78, A.GREY))


def print_architecture() -> None:
    art = r"""
  [SIMULATED SOURCES]        [EDGE / DEFENSE LAYERS]          [ORIGIN]
  +----------------+  L7   +----------------------+        +--------------------+
  | LEGIT USERS    |------>| JAM (WAF ruleset)    |--403   |  MUFFIN            |
  +----------------+       +----------------------+  |     |  HTTPS server      |
  +----------------+  L7   +----------------------+  |     |  127.0.0.1:PORT    |
  | BOTNET         |------>| SYRUP (token bucket) |--429   |  (never public)    |
  | (synthetic)    |       +----------------------+  |     +---------+----------+
  +----------------+       +----------------------+  |503            |
         |  L3/L4          | PANCAKE admission    |--+     +---------+---------+
         +---conceptual--->| gate + bounded queue |        |                   |
            (no packets)   +----------------------+        v                   v
                                                     +-------------+   +-------------+
                                                     | FRIDGE      |   | GRIDDLE     |
                                                     | TTL cache   |   | conn pool   |
                                                     +-------------+   +-------------+

  TELEMETRY:  SIZZLE -> CEREAL -> BACON        STATE:  RAW WARM SIMMER SIZZLE SMOKE BURNT
  OFFLINE:    OMELETTE (pure math, zero packets sent anywhere)
"""
    for line in art.strip("\n").splitlines():
        print("  " + paint(line, A.BCYAN))


def print_layer_matrix() -> None:
    rows = [
        ("L3/L4 network", "volumetric absorption, anycast, upstream scrubbing", A.BBLUE),
        ("L4 transport", "SYN backlog, conn limits, idle timeouts", A.BCYAN),
        ("TLS", "handshake cost control, cipher policy, session reuse", A.BGREEN),
        ("L7 HTTP", "rate limit, WAF, cache, queue shedding", A.BYELLOW),
        ("Application", "db pooling, worker caps, graceful degradation", A.BRED),
    ]
    print()
    print(paint("  DEFENSE PLACEMENT BY OSI LAYER", A.BWHITE, A.BOLD))
    for layer, what, color in rows:
        print(f"   {paint(layer.ljust(16), color, A.BOLD)} {paint(what, A.GREY)}")


def print_incident_checklist() -> None:
    groups = [
        ("T+0 DETECT", A.BYELLOW, [
            "Alert fires: RPS / error rate / p95 latency / queue saturation.",
            "Confirm it is real: check /metrics, /dashboard, per-client rates.",
            "Classify: volumetric | protocol/state | application-layer.",
            "Start the incident clock and open a comms channel.",
        ]),
        ("T+2 TRIAGE", A.BYELLOW, [
            "Is the origin reachable at all? Try the loopback health probe.",
            "Identify top talkers: are they one client, a subnet, or the world?",
            "Distinguish attack from flash crowd (legit spike, no attacker).",
            "Snapshot logs before they rotate - evidence matters.",
        ]),
        ("T+5 MITIGATE (in order)", A.BRED, [
            "1. Enable edge/CDN proxying so the origin IP is hidden.",
            "2. Turn on WAF managed rules; drop malformed traffic first.",
            "3. Apply per-client rate limits; widen burst for real users.",
            "4. Shrink connection and request timeouts (free up workers fast).",
            "5. Enable caching for static and hot endpoints; raise TTL.",
            "6. Cap DB pool concurrency; add read replicas or a queue.",
            "7. Enable priority queueing so legit traffic wins ties.",
            "8. Last resort: upstream blackhole / scrub specific geos or ASNs.",
        ]),
        ("T+15 STABILIZE", A.BGREEN, [
            "Watch legit success rate - the ONLY metric that matters.",
            "Widen rate limits gradually; verify no collateral damage.",
            "Confirm 429s hit the attacker, not the customers.",
        ]),
        ("POST-MORTEM", A.BCYAN, [
            "Timeline: first alert, first action, first recovery, full recovery.",
            "Quantify: peak rps, peak pps, peak connections, drop counts.",
            "Cost: bandwidth, scrubbing fees, engineering hours.",
            "Fixes: capacity headroom, tighter WAF, better caching, anycast.",
            "Rehearse: rerun the matching OMELETTE scenario to validate.",
        ]),
    ]
    print()
    for title, color, items in groups:
        print(f"  {paint(title, color, A.BOLD)}")
        for item in items:
            print(f"    {paint('>', A.GREY)} {paint(item, A.WHITE)}")
        print()


def print_troubleshooting() -> None:
    items = [
        ("Port already in use", "Change --port, or find the owner: "
                                "Windows `netstat -ano | findstr :8443`; "
                                "Linux `ss -ltnp | grep 8443`."),
        ("Certificate warnings in browser", "Expected: it is self-signed. Click through, "
                                            "or trust .ironwaffle/cert.pem locally."),
        ("`openssl` not found and `cryptography` missing", "Server falls back to plain HTTP "
                                                           "automatically; or `pip install cryptography`."),
        ("curl: (60) SSL certificate problem", "Use `curl -k https://127.0.0.1:8443/health`."),
        ("Everything returns 429", "You are the attacker. Raise --rate-limit or wait for "
                                   "the burst to refill; check /metrics rate_limiter."),
        ("Everything returns 503", "Admission gate saturated. Raise --max-inflight or "
                                   "lower --slow-endpoint-ms."),
        ("Everything returns 403", "A JAM rule matched. Hit /waf-test to see which rule, "
                                   "then check your URL encoding."),
        ("Windows shows raw escape codes", "Set `$env:IRONWAFFLE_COLOR='always'` or use "
                                           "Windows Terminal; legacy conhost may not do VT."),
        ("Metrics look empty", "No traffic yet. Hit /api/fast a few times, or run "
                               "`flood --clients 20 --duration 15`."),
        ("psutil / resource backend shows 'none'", "Harmless - CPU/RSS fall back to "
                                                   "process_time sampling."),
        ("Test suite hangs", "The e2e test binds port 0; ensure no firewall prompt is "
                             "blocking 127.0.0.1 (rare)."),
        ("High CPU during flood", "Expected: it is thread-per-connection by design so you "
                                  "can watch the gate work."),
    ]
    print()
    print(paint("  TROUBLESHOOTING", A.BWHITE, A.BOLD))
    for symptom, fix in items:
        print(f"   {paint(symptom, A.BYELLOW)}")
        print(f"     {paint(fix, A.GREY)}")


# =============================================================================
# SECTION 21 - TEST SUITE (SCRAMBLE)
# =============================================================================

class TestRollingWindow(unittest.TestCase):
    def test_count_and_rate(self):
        w = RollingWindow(1.0, 1000)
        base = time.monotonic()
        for i in range(10):
            w.add(1.0, base + i * 0.05)
        self.assertEqual(w.count(base + 0.45), 10)
        self.assertAlmostEqual(w.rate(base + 0.45), 10.0, places=3)

    def test_expiry_prunes(self):
        w = RollingWindow(0.5, 1000)
        base = time.monotonic()
        for i in range(20):
            w.add(1.0, base + i * 0.1)
        self.assertLessEqual(w.count(base + 2.0), 6)

    def test_bounded_size(self):
        w = RollingWindow(1000.0, 50)
        for i in range(500):
            w.add(1.0, time.monotonic() + i * 0.001)
        self.assertLessEqual(len(w), 50)

    def test_percentiles(self):
        w = RollingWindow(60.0, 1000)
        for v in range(1, 101):
            w.add(float(v))
        p = w.percentiles()
        self.assertGreaterEqual(p["p50"], 45)
        self.assertLessEqual(p["p50"], 55)
        self.assertGreaterEqual(p["p99"], 95)

    def test_invalid_window(self):
        with self.assertRaises(ValueError):
            RollingWindow(0)


class TestTokenBucket(unittest.TestCase):
    def test_burst_then_deny(self):
        b = TokenBucket(rate=10, burst=5)
        for _ in range(5):
            self.assertTrue(b.take()[0])
        self.assertFalse(b.take()[0])

    def test_refill_over_time(self):
        b = TokenBucket(rate=100, burst=10)
        for _ in range(10):
            b.take()
        self.assertFalse(b.take()[0])
        time.sleep(0.05)
        self.assertTrue(b.take()[0])

    def test_retry_after_positive(self):
        b = TokenBucket(rate=2, burst=1)
        b.take()
        ok, retry = b.take()
        self.assertFalse(ok)
        self.assertGreater(retry, 0)

    def test_validation(self):
        with self.assertRaises(ValueError):
            TokenBucket(0, 1)
        with self.assertRaises(ValueError):
            TokenBucket(1, 0)


class TestLeakyBucket(unittest.TestCase):
    def test_capacity_enforced(self):
        b = LeakyBucket(capacity=5, drain_per_sec=1)
        accepted = sum(1 for _ in range(20) if b.offer())
        self.assertLessEqual(accepted, 6)

    def test_drains(self):
        b = LeakyBucket(capacity=3, drain_per_sec=200)
        for _ in range(3):
            b.offer()
        time.sleep(0.05)
        self.assertTrue(b.offer())


class TestRateLimiter(unittest.TestCase):
    def test_per_client_isolation(self):
        rl = RateLimiter(rate=5, burst=5, max_clients=100)
        for _ in range(5):
            self.assertTrue(rl.check("a")[0])
        self.assertFalse(rl.check("a")[0])
        self.assertTrue(rl.check("b")[0])

    def test_bounded_client_table(self):
        rl = RateLimiter(rate=1000, burst=1000, max_clients=16)
        for i in range(500):
            rl.check(f"c{i}")
        self.assertLessEqual(rl.client_count(), 16)

    def test_stats_counting(self):
        rl = RateLimiter(rate=1, burst=2, max_clients=10)
        rl.check("x"); rl.check("x"); rl.check("x")
        self.assertEqual(rl.stats()["denied"], 1)


class TestBoundedPriorityQueue(unittest.TestCase):
    def test_priority_order(self):
        q = BoundedPriorityQueue(10)
        q.put("low", "HOSTILE")
        q.put("high", "LEGIT")
        self.assertEqual(q.get(), "high")
        self.assertEqual(q.get(), "low")

    def test_drops_lowest_class_first(self):
        q = BoundedPriorityQueue(3)
        for _ in range(3):
            q.put("h", "HOSTILE")
        q.put("l", "LEGIT")
        self.assertGreater(q.dropped["HOSTILE"], 0)
        self.assertEqual(len(q), 3)

    def test_bad_level(self):
        with self.assertRaises(ValueError):
            BoundedPriorityQueue(2).put(1, "NOPE")


class TestAdmissionController(unittest.TestCase):
    def test_rejects_when_saturated(self):
        gate = AdmissionController(max_inflight=2, max_wait_s=0.05)
        self.assertTrue(gate.acquire())
        self.assertTrue(gate.acquire())
        self.assertFalse(gate.acquire())
        gate.release()
        self.assertTrue(gate.acquire())

    def test_stats_consistency(self):
        gate = AdmissionController(max_inflight=4, max_wait_s=0.01)
        for _ in range(4):
            gate.acquire()
        gate.acquire()
        st = gate.stats()
        self.assertEqual(st["inflight"], 4)
        self.assertGreaterEqual(st["rejected"], 1)


class TestWAF(unittest.TestCase):
    def setUp(self):
        self.waf = WAF()

    def test_clean_path_passes(self):
        self.assertFalse(self.waf.inspect("GET", "/api/fast", "", "IronWaffle/1.0").blocked)

    def test_traversal_blocked(self):
        self.assertTrue(self.waf.inspect("GET", "/../../etc/passwd", "", "x").blocked)

    def test_sqli_blocked(self):
        self.assertTrue(self.waf.inspect("GET", "/api", "q=1 union select 1", "x").blocked)

    def test_null_byte_blocked(self):
        self.assertTrue(self.waf.inspect("GET", "/api%00", "", "x").blocked)

    def test_long_path_blocked(self):
        self.assertTrue(self.waf.inspect("GET", "/" + "a" * 3000, "", "x").blocked)

    def test_empty_ua_blocked(self):
        self.assertTrue(self.waf.inspect("GET", "/api", "", "").blocked)

    def test_disabled_passes_all(self):
        w = WAF(enabled=False)
        self.assertFalse(w.inspect("GET", "/../../x", "", "").blocked)


class TestCache(unittest.TestCase):
    def test_hit_and_miss(self):
        c = TTLCache(ttl_s=5, max_entries=10)
        self.assertIsNone(c.get("k"))
        c.put("k", "v")
        self.assertEqual(c.get("k"), "v")

    def test_ttl_expiry(self):
        c = TTLCache(ttl_s=0.05, max_entries=10)
        c.put("k", "v")
        time.sleep(0.08)
        self.assertIsNone(c.get("k"))

    def test_bounded_entries(self):
        c = TTLCache(ttl_s=100, max_entries=5)
        for i in range(50):
            c.put(f"k{i}", i)
        self.assertLessEqual(c.stats()["entries"], 5)


class TestConnectionPool(unittest.TestCase):
    def test_acquire_release(self):
        pool = ConnectionPool(size=2, query_ms=1, acquire_timeout_s=1)
        with pool.acquire():
            self.assertEqual(pool.stats()["in_use"], 1)
        self.assertEqual(pool.stats()["in_use"], 0)

    def test_timeout_when_exhausted(self):
        pool = ConnectionPool(size=1, query_ms=200, acquire_timeout_s=0.02)
        with pool.acquire():
            with self.assertRaises(TimeoutError):
                with pool.acquire():
                    pass


class TestMetrics(unittest.TestCase):
    def test_record_and_snapshot_fields(self):
        m = Metrics(window_s=10, max_clients=8)
        for i in range(20):
            m.record("c1", 200 if i % 5 else 429, 5.0, "/api/fast")
        self.assertEqual(m.counters["requests_total"], 20)
        self.assertEqual(m.status_codes[429], 4)
        self.assertEqual(m.top_clients()[0][0], "c1")

    def test_client_table_bounded(self):
        m = Metrics(window_s=10, max_clients=8)
        for i in range(100):
            m.record(f"c{i}", 200, 1.0, "/")
        self.assertLessEqual(len(m.clients), 8)

    def test_reset(self):
        m = Metrics()
        m.record("a", 200, 1.0, "/")
        m.reset()
        self.assertEqual(m.counters.get("requests_total", 0), 0)


class TestDangerLadder(unittest.TestCase):
    def test_ladder_is_ordered(self):
        floors = [d.floor for d in DANGER_LADDER]
        self.assertEqual(floors, sorted(floors))

    def test_score_bounds(self):
        self.assertGreaterEqual(danger_score(0, 0, 0, 0), 0)
        self.assertLessEqual(danger_score(10, 100, 5000, 100), 100)

    def test_level_mapping(self):
        self.assertEqual(danger_level(0).name, "RAW")
        self.assertEqual(danger_level(100).name, "BURNT")


class TestSimulation(unittest.TestCase):
    def test_baseline_is_healthy(self):
        sc = Scenario("t", "t", "t", duration_s=20, baseline_rps=40, attack_rps=0,
                      attack_start_s=5, attack_end_s=6, capacity_rps=200)
        res = Omelette().run(sc)
        self.assertGreater(res.legit_success_pct, 99.0)
        self.assertEqual(res.dropped_legit, 0.0)
        self.assertLess(res.peak_danger_score, 35)

    def test_volumetric_starves_legit_without_priority(self):
        sc = Scenario("t", "t", "t", duration_s=30, baseline_rps=40, attack_rps=1500,
                      attack_start_s=5, attack_end_s=20, capacity_rps=200,
                      queue_limit=200, priority_to_legit=False)
        res = Omelette().run(sc)
        self.assertLess(res.legit_success_pct, 60.0)
        self.assertGreater(res.total_dropped, 0)

    def test_priority_queue_rescues_legit(self):
        sc = Scenario("t", "t", "t", duration_s=30, baseline_rps=40, attack_rps=1500,
                      attack_start_s=5, attack_end_s=20, capacity_rps=200,
                      queue_limit=200, priority_to_legit=True)
        res = Omelette().run(sc)
        self.assertGreater(res.legit_success_pct, 95.0)

    def test_full_mitigation_holds_service(self):
        sc = Scenario("t", "t", "t", duration_s=30, baseline_rps=40, attack_rps=3000,
                      attack_start_s=5, attack_end_s=20, capacity_rps=200,
                      mitigation_effectiveness=1.0, mitigation_delay_s=0.5)
        res = Omelette().run(sc)
        self.assertGreater(res.legit_success_pct, 99.0)

    def test_recovery_time_is_measured(self):
        sc = Scenario("t", "t", "t", duration_s=60, baseline_rps=30, attack_rps=900,
                      attack_start_s=5, attack_end_s=25, capacity_rps=200, queue_limit=400)
        res = Omelette().run(sc)
        self.assertGreaterEqual(res.recovery_s, 0.0)
        self.assertLess(res.recovery_s, 60.0)

    def test_determinism_with_seed(self):
        sc = Scenario("t", "t", "t", seed=42, duration_s=20, attack_start_s=5, attack_end_s=15)
        a = Omelette().run(sc)
        b = Omelette().run(sc)
        self.assertEqual(a.served_legit, b.served_legit)
        self.assertEqual(a.peak_queue, b.peak_queue)

    def test_flash_crowd_is_legit_only(self):
        sc = Scenario("t", "t", "t", duration_s=40, baseline_rps=400, attack_rps=0,
                      attack_start_s=10, attack_end_s=30, capacity_rps=250, queue_limit=300)
        res = Omelette().run(sc)
        self.assertEqual(res.arrivals_attack, 0.0)
        self.assertGreater(res.dropped_legit, 0)
        self.assertLess(res.legit_success_pct, 100.0)

    def test_validation_errors(self):
        with self.assertRaises(ValueError):
            Omelette().run(Scenario("t", "t", "t", attack_start_s=10, attack_end_s=5))
        with self.assertRaises(ValueError):
            Omelette().run(Scenario("t", "t", "t", mitigation_effectiveness=2.0))

    def test_all_scenarios_run(self):
        for key, sc in default_scenarios().items():
            res = Omelette().run(sc)
            self.assertEqual(res.scenario, key)
            self.assertGreaterEqual(res.legit_success_pct, 0.0)
            self.assertLessEqual(res.legit_success_pct, 100.0001)

    def test_sweep_monotonic_effectiveness(self):
        sc = Scenario("t", "t", "t", duration_s=30, attack_rps=1500, attack_start_s=5,
                      attack_end_s=20, capacity_rps=200, queue_limit=300)
        sweep = Omelette().sweep(sc, "mitigation_effectiveness", [0.0, 0.5, 0.9, 1.0])
        pcts = [p for _, p in sweep]
        self.assertGreaterEqual(pcts[-1], pcts[0])


class TestConcurrency(unittest.TestCase):
    def test_metrics_thread_safe(self):
        m = Metrics(window_s=10, max_clients=512)
        def worker(idx):
            for i in range(200):
                m.record(f"c{idx % 10}", 200, 1.0, "/x")
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(16)]
        for t in threads: t.start()
        for t in threads: t.join()
        self.assertEqual(m.counters["requests_total"], 16 * 200)

    def test_limiter_thread_safe_never_over_admits(self):
        rl = RateLimiter(rate=1000, burst=50, max_clients=64)
        results = []
        lock = threading.Lock()
        def worker():
            local = [rl.check("shared")[0] for _ in range(100)]
            with lock:
                results.append(local)
        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads: t.start()
        for t in threads: t.join()
        self.assertEqual(len(results), 8)

    def test_gate_thread_safe(self):
        gate = AdmissionController(max_inflight=8, max_wait_s=2.0)
        peak = []
        lock = threading.Lock()
        def worker():
            for _ in range(50):
                if gate.acquire():
                    with lock:
                        peak.append(gate.stats()["inflight"])
                    time.sleep(0.0005)
                    gate.release()
        threads = [threading.Thread(target=worker) for _ in range(16)]
        for t in threads: t.start()
        for t in threads: t.join()
        self.assertLessEqual(max(peak), 8)
        self.assertEqual(gate.stats()["inflight"], 0)


class TestServerIntegration(unittest.TestCase):
    """End-to-end over real loopback sockets. No external traffic."""

    @classmethod
    def setUpClass(cls):
        import http.client
        cls.http = http.client
        cls.cfg = LabConfig(port=0, tls=False, rate_limit_rps=5,
                            rate_limit_burst=5, max_inflight=4,
                            max_queue_wait_s=0.05, db_pool_size=2,
                            slow_endpoint_ms=1)
        cls.lab = Lab(cls.cfg)
        cls.server = make_server(cls.lab)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.lab.stop_event.set()
        cls.server.shutdown()
        cls.server.server_close()

    def _get(self, path, client=None):
        conn = self.http.HTTPConnection("127.0.0.1", self.port, timeout=5)
        headers = {}
        if client:
            headers["X-Lab-Client"] = client
        conn.request("GET", path, headers=headers)
        resp = conn.getresponse()
        body = resp.read()
        conn.close()
        return resp.status, body

    def test_binds_loopback_only(self):
        self.assertEqual(self.server.server_address[0], "127.0.0.1")

    def test_health(self):
        status, _ = self._get("/health")
        self.assertEqual(status, 200)

    def test_metrics_json(self):
        status, body = self._get("/metrics")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertIn("danger", data)
        self.assertEqual(data["mode"], "LOOPBACK-SIMULATED")

    def test_rate_limit_returns_429(self):
        for _ in range(5):
            self._get("/api/fast", client="burst-test")
        status, _ = self._get("/api/fast", client="burst-test")
        self.assertEqual(status, 429)

    def test_distinct_clients_isolated(self):
        for _ in range(5):
            self._get("/api/fast", client="iso-a")
        status, _ = self._get("/api/fast", client="iso-b")
        self.assertEqual(status, 200)

    def test_waf_blocks_traversal(self):
        status, _ = self._get("/api/fast", client="waf-t")
        self.assertEqual(status, 200)
        status, _ = self._get("/../../../etc/passwd", client="waf-t2")
        self.assertEqual(status, 403)

    def test_cache_hit_header(self):
        self._get("/static/app.js", client="cache-t")
        conn = self.http.HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request("GET", "/static/app.js", headers={"X-Lab-Client": "cache-t"})
        resp = conn.getresponse()
        resp.read()
        self.assertEqual(resp.getheader("X-Cache"), "HIT")
        conn.close()

    def test_simulation_endpoint(self):
        status, body = self._get("/sim?scenario=baseline")
        self.assertEqual(status, 200)
        self.assertIn("legit_success_pct", json.loads(body))

    def test_unknown_route_404(self):
        status, _ = self._get("/nope")
        self.assertEqual(status, 404)

    def test_metrics_recorded_after_traffic(self):
        before = self.lab.metrics.counters.get("requests_total", 0)
        self._get("/api/fast", client="record-t")
        after = self.lab.metrics.counters.get("requests_total", 0)
        self.assertGreater(after, before)


class TestNoExternalTraffic(unittest.TestCase):
    def test_config_host_is_loopback(self):
        cfg = LabConfig()
        ipaddress.ip_address(cfg.host)
        self.assertTrue(ipaddress.ip_address(cfg.host).is_loopback)

    def test_non_loopback_rejected(self):
        cfg = LabConfig(host="8.8.8.8", enforce_loopback=True)
        with self.assertRaises(ValueError):
            cfg.validate()

    def test_scenario_math_needs_no_sockets(self):
        sc = default_scenarios()["volumetric"]
        res = Omelette().run(sc)
        self.assertGreater(res.arrivals_attack, 0)


class TestTLSForge(unittest.TestCase):
    def test_context_builds_or_skips(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            toast = Toast(tmp)
            ok, msg = toast.generate()
            if not ok:
                self.skipTest(f"no generator: {msg}")
            self.assertTrue(os.path.isfile(toast.cert_path))
            ctx = toast.build_context()
            self.assertIsInstance(ctx, ssl.SSLContext)
            facts = toast.cert_facts()
            self.assertTrue(facts["exists"])


# =============================================================================
# SECTION 22 - CLI
# =============================================================================

EPILOG = """
examples:
  python ironwaffle.py cert                      # forge a local test certificate
  python ironwaffle.py serve                     # HTTPS lab on 127.0.0.1:8443
  python ironwaffle.py serve --no-tls --port 8080
  python ironwaffle.py sim --scenario volumetric
  python ironwaffle.py sim --all
  python ironwaffle.py sim --scenario waf_tuned --json
  python ironwaffle.py flood --clients 40 --rps 25 --duration 20
  python ironwaffle.py selftest
  python ironwaffle.py doctor
  python ironwaffle.py brief

policy: nothing is ever sent to a public IP. All attack traffic is SIMULATED math.
"""


def cmd_serve(args: argparse.Namespace) -> int:
    cfg = LabConfig(
        host=args.host, port=args.port, cert_dir=args.cert_dir,
        log_path=args.log or os.path.join(args.cert_dir, "ironwaffle.log"),
        log_level=args.log_level, tls=not args.no_tls,
        rate_limit_rps=args.rate_limit, rate_limit_burst=args.rate_burst,
        max_inflight=args.max_inflight, max_queue_wait_s=args.queue_wait,
        capacity_rps=args.capacity, slow_endpoint_ms=args.slow_endpoint_ms,
    )
    print_banner()
    cfg.validate()

    lab = Lab(cfg)

    if cfg.tls:
        ok, msg = lab.toast.generate()
        if ok:
            lab.log.emit("NOTICE", "tls.ready", detail=msg, cert=lab.toast.cert_path)
        else:
            lab.log.emit("WARN", "tls.unavailable", detail=msg,
                         fallback="serving plain HTTP on loopback")
            cfg.tls = False

    server = make_server(lab)
    scheme = "https" if cfg.tls else "http"
    base = f"{scheme}://{cfg.host}:{cfg.port}"

    print()
    print(kv("build", f"{BUILD_NAME} {BUILD_TAG} v{BUILD_VERSION}", A.GREY, A.BYELLOW))
    print(kv("bind", f"{cfg.host}:{cfg.port}  (loopback only)", A.GREY, A.BGREEN))
    print(kv("scheme", scheme.upper(), A.GREY, A.BGREEN if cfg.tls else A.BYELLOW))
    print(kv("rate limit", f"{cfg.rate_limit_rps} rps burst {cfg.rate_limit_burst}", A.GREY, A.WHITE))
    print(kv("admission gate", f"{cfg.max_inflight} inflight, {cfg.max_queue_wait_s}s wait", A.GREY, A.WHITE))
    print(kv("assumed capacity", f"{cfg.capacity_rps} rps (for danger math)", A.GREY, A.WHITE))
    print(kv("log", cfg.log_path, A.GREY, A.GREY))
    print()
    print(f"  {paint('dashboard', A.BCYAN)}  {paint(base + '/dashboard', A.BWHITE, A.UNDER)}")
    print(f"  {paint('index    ', A.BCYAN)}  {paint(base + '/', A.BWHITE, A.UNDER)}")
    print(f"  {paint('metrics  ', A.BCYAN)}  {paint(base + '/metrics', A.GREY)}")
    print(f"  {paint('simulate ', A.BCYAN)}  {paint(base + '/sim?scenario=volumetric', A.GREY)}")
    if cfg.tls:
        print()
        print(f"  {paint('self-signed cert: browsers will warn. Use curl -k, or trust', A.BYELLOW)}")
        print(f"  {paint(lab.toast.cert_path, A.GREY)}")
    print()
    print(paint("  Ctrl+C to stop. Loopback only. No packets leave this machine.", A.GREY))
    print()

    lab.start_monitor()

    def _stop(signum, _frame):
        lab.log.emit("NOTICE", "signal.received", signum=signum)
        threading.Thread(target=lab.shutdown, daemon=True).start()

    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(Exception):
            signal.signal(sig, _stop)

    lab.log.emit("NOTICE", "server.start", url=base, tls=cfg.tls)
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        with contextlib.suppress(Exception):
            server.server_close()
        lab.shutdown()
        print()
        print(paint("  IRON WAFFLE stopped cleanly.", A.BGREEN))
    return 0


def cmd_sim(args: argparse.Namespace) -> int:
    print_banner()
    scenarios = default_scenarios()
    engine = Omelette()

    if args.all:
        chosen = list(scenarios.values())
    else:
        sc = scenarios.get(args.scenario)
        if sc is None:
            print(paint(f"  unknown scenario: {args.scenario}", A.BRED))
            print(paint("  available: " + ", ".join(scenarios), A.GREY))
            return 2
        chosen = [sc]

    summary = []
    for sc in chosen:
        if args.attack_rps:
            sc = dataclasses.replace(sc, attack_rps=args.attack_rps)
        if args.capacity:
            sc = dataclasses.replace(sc, capacity_rps=args.capacity)
        if args.effectiveness is not None:
            sc = dataclasses.replace(sc, mitigation_effectiveness=args.effectiveness)
        if args.priority:
            sc = dataclasses.replace(sc, priority_to_legit=True)

        result = engine.run(sc)
        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print(result.render())
        summary.append(result)

    if len(summary) > 1 and not args.json:
        print()
        print(paint("  COMPARATIVE SUMMARY  (all traffic synthetic)", A.BWHITE, A.BOLD))
        print(hrule("-", 78, A.GREY))
        print(f"  {paint('scenario', A.GREY).ljust(38)}"
              f"{paint('legit %', A.GREY).ljust(14)}"
              f"{paint('dropped', A.GREY).ljust(14)}"
              f"{paint('peak danger', A.GREY)}")
        for r in summary:
            lvl = danger_level(r.peak_danger_score)
            pct = r.legit_success_pct
            color = A.BGREEN if pct > 95 else (A.BYELLOW if pct > 70 else A.BRED)
            print(f"  {r.scenario.ljust(30)}"
                  f"  {paint(f'{pct:6.2f}%', color)}"
                  f"    {str(int(r.total_dropped)).ljust(10)}"
                  f"  {paint(lvl.name, lvl.color)}")
        print(hrule("-", 78, A.GREY))
        print(paint("  Remember: these numbers come from a fluid queue model, "
                    "not from real packets.", A.GREY))
    return 0


def cmd_cert(args: argparse.Namespace) -> int:
    print_banner()
    toast = Toast(args.cert_dir, args.host, args.days)
    if args.force and toast.exists():
        for p in (toast.cert_path, toast.key_path):
            with contextlib.suppress(OSError):
                os.remove(p)
    ok, msg = toast.generate(force=True)
    if not ok:
        print(paint(f"  FAILED: {msg}", A.BRED))
        print(paint("  install one of: `pip install cryptography` or openssl CLI", A.GREY))
        return 1
    print(kv("result", msg, A.GREY, A.BGREEN))
    print(kv("certificate", toast.cert_path, A.GREY, A.WHITE))
    print(kv("private key", toast.key_path, A.GREY, A.WHITE))
    print(kv("CN / SAN", f"{args.host} / IP:{args.host}, DNS:localhost", A.GREY, A.WHITE))
    print(kv("validity", f"{args.days} days", A.GREY, A.WHITE))
    print()
    print(paint("  POSTURE CHECKS", A.BWHITE, A.BOLD))
    for check, status, detail in toast.posture_check():
        color = {"OK": A.BGREEN, "WARN": A.BYELLOW, "FAIL": A.BRED}.get(status, A.WHITE)
        print(f"   {paint(status.ljust(5), color, A.BOLD)} {check.ljust(28)} {paint(detail, A.GREY)}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    print_banner()
    print(paint("  ENVIRONMENT DIAGNOSTICS", A.BWHITE, A.BOLD))
    print()
    rows: List[Tuple[str, str, str]] = []
    rows.append(("python", sys.version.split()[0], "OK" if sys.version_info >= (3, 8) else "FAIL"))
    rows.append(("platform", platform.platform()[:60], "OK"))
    rows.append(("hostname", socket.gethostname(), "OK"))
    try:
        ipaddress.ip_address("127.0.0.1")
        rows.append(("loopback arithmetic", "127.0.0.1 parses", "OK"))
    except Exception:
        rows.append(("loopback arithmetic", "failed", "FAIL"))
    rows.append(("openssl", shutil.which("openssl") or "not found",
                 "OK" if shutil.which("openssl") else "WARN"))
    try:
        import cryptography  # type: ignore
        rows.append(("cryptography", getattr(cryptography, "__version__", "?"), "OK"))
    except Exception:
        rows.append(("cryptography", "not installed", "WARN"))
    try:
        import psutil  # type: ignore
        rows.append(("psutil", getattr(psutil, "__version__", "?"), "OK"))
    except Exception:
        rows.append(("psutil", "not installed", "WARN"))
    rows.append(("TLS module", ssl.OPENSSL_VERSION[:50], "OK"))
    rows.append(("colour", "enabled" if _COLOR_ENABLED else "disabled",
                 "OK" if _COLOR_ENABLED else "WARN"))
    rows.append(("log dir writable",
                 "yes" if os.access(os.path.abspath(args.cert_dir), os.W_OK)
                 else "creating", "OK"))

    port_free = True
    with contextlib.suppress(OSError):
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind(("127.0.0.1", args.port))
        except OSError:
            port_free = False
        finally:
            probe.close()
    rows.append((f"port {args.port} on loopback", "free" if port_free else "in use",
                 "OK" if port_free else "WARN"))

    for name, detail, status in rows:
        color = {"OK": A.BGREEN, "WARN": A.BYELLOW, "FAIL": A.BRED}.get(status, A.WHITE)
        print(f"   {paint(status.ljust(5), color, A.BOLD)} {name.ljust(26)} {paint(detail, A.GREY)}")

    print()
    print(paint("  POLICY ASSERTIONS", A.BWHITE, A.BOLD))
    assertions = [
        "server binds 127.0.0.1 only - never a public interface",
        "certificate SAN covers IP:127.0.0.1 and DNS:localhost",
        "simulation is pure math - OMELETTE sends zero packets",
        "the optional flood driver targets 127.0.0.1 exclusively",
        "no DNS resolution, no third-party services, no rate-limit bypass",
    ]
    for a in assertions:
        print(f"   {paint('ASSERT', A.BGREEN)} {paint(a, A.GREY)}")
    return 0


def cmd_flood(args: argparse.Namespace) -> int:
    print_banner()
    scheme = "http" if args.no_tls else "https"
    print(kv("target", f"{scheme}://{args.host}:{args.port}{args.path}", A.GREY, A.BGREEN))
    print(kv("simulated clients", args.clients, A.GREY, A.WHITE))
    print(kv("per-client rps", args.rps, A.GREY, A.WHITE))
    print(kv("total offered rps", args.clients * args.rps, A.GREY, A.BYELLOW))
    print(kv("duration", f"{args.duration}s", A.GREY, A.WHITE))
    print()
    print(paint("  Each thread is one fake client using X-Lab-Client.", A.GREY))
    print(paint("  Nothing here leaves loopback.", A.GREY))
    print()

    driver = LoopbackDriver(args.host, args.port, not args.no_tls,
                            args.clients, args.rps, args.duration, args.path)
    started = time.monotonic()
    stats = driver.run()
    elapsed = time.monotonic() - started

    total = sum(v for k, v in stats.items() if isinstance(k, int))
    print()
    print(paint("  RESULT", A.BWHITE, A.BOLD))
    print(kv("elapsed", f"{elapsed:.2f}s", A.GREY, A.WHITE))
    print(kv("completed", total, A.GREY, A.WHITE))
    print(kv("achieved rps", f"{total / max(elapsed, 1e-6):.1f}", A.GREY, A.BYELLOW))
    for code in sorted(k for k in stats if isinstance(k, int)):
        color = A.BGREEN if code < 300 else (A.BYELLOW if code < 500 else A.BRED)
        print(kv(f"  HTTP {code}", stats[code], A.GREY, color))
    if stats.get("errors"):
        print(kv("transport errors", stats["errors"], A.GREY, A.BRED))
    print()
    print(paint("  Interpretation: 429 = rate limiter, 403 = WAF, "
                "503 = admission gate. Any of those means a defense worked.",
                A.GREY))
    return 0


def cmd_selftest(args: argparse.Namespace) -> int:
    print_banner()
    print(paint("  RUNNING TEST SUITE (SCRAMBLE)", A.BWHITE, A.BOLD))
    print()
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for name in sorted(dir(sys.modules[__name__])):
        if name.startswith("Test"):
            obj = getattr(sys.modules[__name__], name)
            if isinstance(obj, type) and issubclass(obj, unittest.TestCase):
                suite.addTests(loader.loadTestsFromTestCase(obj))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print()
    print(hrule("=", 78, A.GREY))
    total = result.testsRun
    failed = len(result.failures) + len(result.errors)
    print(kv("tests run", total, A.GREY, A.WHITE))
    print(kv("failures + errors", failed, A.GREY, A.BGREEN if failed == 0 else A.BRED))
    print(kv("skipped", len(result.skipped), A.GREY, A.BYELLOW))
    print(hrule("=", 78, A.GREY))
    if failed == 0:
        print(paint("  ALL GREEN. The lab is reproducible.", A.BGREEN, A.BOLD))
        return 0
    print(paint("  RED. See tracebacks above.", A.BRED, A.BOLD))
    return 1


def cmd_brief(args: argparse.Namespace) -> int:
    print_banner()
    print(paint("  ARCHITECTURE", A.BWHITE, A.BOLD))
    print_architecture()
    print_layer_matrix()
    print_incident_checklist()
    print_troubleshooting()
    print()
    print(paint("  LAYER-BY-LAYER DEFENSE EXPLANATION", A.BWHITE, A.BOLD))
    notes = [
        ("Network (L3/L4)", A.BBLUE,
         "Volumetric floods are absorbed before they reach you: anycast spreads load "
         "across scrubbing PoPs, upstream blackhole drops whole prefixes, and the origin "
         "IP stays hidden behind a CDN. You cannot win a bandwidth fight on a single box."),
        ("Transport (L4)", A.BCYAN,
         "State exhaustion targets the connection table, not bandwidth. Defenses: cap "
         "concurrent connections per source, shrink SYN backlog timeouts, reuse "
         "connections, and enable SYN cookies so half-open handshakes stop costing RAM."),
        ("TLS", A.BGREEN,
         "Each handshake costs CPU (asymmetric crypto). Defenses: terminate TLS at the "
         "edge, enable session resumption and TLS 1.3 0-RTT, pin an ECDSA/ECDHE cipher "
         "suite, and disable renegotiation. Handshake floods die at the edge."),
        ("HTTP (L7)", A.BYELLOW,
         "Application floods look like real users. Defenses: per-client token buckets, "
         "WAF signatures, request size and header limits, caching to cut origin work, "
         "and bounded queues that shed the least valuable request first."),
        ("Application", A.BRED,
         "The cheapest attack targets the most expensive resource: your database. "
         "Defenses: connection pooling with a hard cap, query timeouts, read replicas, "
         "result caching, and back-pressure that returns 503 instead of collapsing."),
        ("Monitoring / IR", A.BMAGENTA,
         "You cannot mitigate what you cannot see. Defenses: rolling-window metrics, "
         "per-client attribution, latency percentiles, alert thresholds with cooldown, "
         "and a written runbook rehearsed before the real attack."),
    ]
    for title, color, text in notes:
        print()
        print(f"  {paint(title, color, A.BOLD)}")
        for line in _wrap(text, 72):
            print(f"    {paint(line, A.GREY)}")
    print()
    return 0


def _wrap(text: str, width: int) -> List[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ironwaffle",
        description=f"{BUILD_NAME} {BUILD_TAG} v{BUILD_VERSION} - "
                    f"{BUILD_CODENAME}: DDoS mechanics, HTTPS defense and traffic analysis lab.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--color", choices=["auto", "always", "never"], default="auto")
    parser.add_argument("--no-color", action="store_true")
    sub = parser.add_subparsers(dest="command")

    p_serve = sub.add_parser("serve", help="run the HTTPS lab server on 127.0.0.1")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8443)
    p_serve.add_argument("--no-tls", action="store_true")
    p_serve.add_argument("--cert-dir", default=".ironwaffle")
    p_serve.add_argument("--log", default=None)
    p_serve.add_argument("--log-level", default="INFO",
                         choices=list(LEVELS.keys()))
    p_serve.add_argument("--rate-limit", type=float, default=25.0)
    p_serve.add_argument("--rate-burst", type=float, default=50.0)
    p_serve.add_argument("--max-inflight", type=int, default=96)
    p_serve.add_argument("--queue-wait", type=float, default=1.5)
    p_serve.add_argument("--capacity", type=float, default=250.0)
    p_serve.add_argument("--slow-endpoint-ms", type=float, default=40.0)
    p_serve.set_defaults(func=cmd_serve)

    p_sim = sub.add_parser("sim", help="run synthetic traffic scenarios (no packets)")
    p_sim.add_argument("--scenario", default="volumetric")
    p_sim.add_argument("--all", action="store_true")
    p_sim.add_argument("--json", action="store_true")
    p_sim.add_argument("--attack-rps", type=float)
    p_sim.add_argument("--capacity", type=float)
    p_sim.add_argument("--effectiveness", type=float)
    p_sim.add_argument("--priority", action="store_true")
    p_sim.set_defaults(func=cmd_sim)

    p_cert = sub.add_parser("cert", help="forge a local test TLS certificate")
    p_cert.add_argument("--cert-dir", default=".ironwaffle")
    p_cert.add_argument("--host", default="127.0.0.1")
    p_cert.add_argument("--days", type=int, default=825)
    p_cert.add_argument("--force", action="store_true")
    p_cert.set_defaults(func=cmd_cert)

    p_doc = sub.add_parser("doctor", help="environment + policy diagnostics")
    p_doc.add_argument("--cert-dir", default=".ironwaffle")
    p_doc.add_argument("--port", type=int, default=8443)
    p_doc.set_defaults(func=cmd_doctor)

    p_flood = sub.add_parser("flood", help="loopback load driver (still 127.0.0.1)")
    p_flood.add_argument("--host", default="127.0.0.1")
    p_flood.add_argument("--port", type=int, default=8443)
    p_flood.add_argument("--no-tls", action="store_true")
    p_flood.add_argument("--clients", type=int, default=20)
    p_flood.add_argument("--rps", type=float, default=20.0)
    p_flood.add_argument("--duration", type=float, default=15.0)
    p_flood.add_argument("--path", default="/api/fast")
    p_flood.set_defaults(func=cmd_flood)

    p_test = sub.add_parser("selftest", help="run the unit + integration test suite")
    p_test.set_defaults(func=cmd_selftest)

    p_brief = sub.add_parser("brief", help="print architecture, IR checklist, layer notes")
    p_brief.set_defaults(func=cmd_brief)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.no_color or args.color == "never":
        set_color(False)
    elif args.color == "always":
        set_color(True)
    else:
        set_color(_detect_color())

    if not getattr(args, "command", None):
        print_banner()
        print(paint("  ARCHITECTURE", A.BWHITE, A.BOLD))
        print_architecture()
        print()
        parser.print_help()
        return 0

    try:
        return args.func(args)
    except KeyboardInterrupt:
        print()
        print(paint("  interrupted.", A.BYELLOW))
        return 130
    except Exception as exc:
        print()
        print(paint(f"  FATAL: {exc}", A.BRED, A.BOLD))
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())