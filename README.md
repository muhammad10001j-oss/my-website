# IRON WAFFLE OMEGA

**A DDoS, HTTPS and traffic-analysis lab that runs entirely on `127.0.0.1`.**
One Python file. No internet needed at runtime. No real attack tool. Nothing ever leaves your machine.

You get a real HTTPS server, a live dashboard, a rate limiter, a WAF, a queue, a
traffic simulator, and a test suite — all in one file, all on loopback.

---

## 60-second start

Put these three files in one folder:

```
ironwaffle.py
recriminat.txt
README.md          <- this file
```

### Windows (PowerShell)

```powershell
cd C:\path\to\folder
powershell -ExecutionPolicy Bypass -File recriminat.txt
python ironwaffle.py serve
```

### Kali / Linux

```bash
cd ~/folder
bash recriminat.txt
python3 ironwaffle.py serve
```

Then open this in your browser:

```
https://127.0.0.1:8443/dashboard
```

Your browser will warn about the certificate. That is expected — it is a local
self-signed cert. Click **Advanced → Proceed**, or use `curl -k`.

**That's it. You are running the lab.**

---

## No installer? Do it by hand

If you would rather not run the installer script.

**Kali / Linux**

```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-venv
python3 -m venv .venv && . .venv/bin/activate
pip install cryptography psutil
python ironwaffle.py cert
python ironwaffle.py serve
```

**Windows**

```powershell
winget install Python.Python.3.12
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install cryptography psutil
python ironwaffle.py cert
python ironwaffle.py serve
```

`cryptography` and `psutil` are optional. Without them the lab still runs — it
just falls back to plain HTTP and basic CPU sampling.

---

## What you should see

```
[ OK ] python: Python 3.12.4
[ OK ] virtualenv: /home/you/folder/.venv
[ OK ] installed: cryptography
[ OK ] found ironwaffle.py
[ OK ] cert: .ironwaffle/cert.pem
[ OK ] doctor: all policy assertions passed
ALL GREEN. The lab is reproducible.

DONE. Next steps:
  python ironwaffle.py serve
  open https://127.0.0.1:8443/dashboard
```

And when the server is up:

```
==================================================================
  IRON WAFFLE OMEGA
  DDoS Mechanics | HTTPS Defense | Traffic Analysis  [loopback only]
==================================================================
  build             IRON WAFFLE OMEGA v1.0.0
  bind              127.0.0.1:8443  (loopback only)
  scheme            HTTPS
  rate limit        25 rps burst 50
  dashboard         https://127.0.0.1:8443/dashboard
  Ctrl+C to stop. Loopback only. No packets leave this machine.
```

---

## How it works

Simple version.

**1. A real HTTPS server on loopback.**
The server binds `127.0.0.1` only. It makes its own TLS certificate for
`127.0.0.1` so you get a genuine HTTPS endpoint without touching DNS or the
internet.

**2. Every request walks through a defence pipeline.**

```
you -> WAF -> rate limiter -> queue gate -> your endpoint -> metrics -> alerts
       403       429            503             200
```

- **WAF** blocks malformed requests (`../`, `%00`, `UNION SELECT`, huge URLs) with a `403`.
- **Rate limiter** gives each client a token bucket. Too fast? `429` plus a `Retry-After`.
- **Queue gate** caps how many requests run at once. Overloaded? `503` instead of a hang.
- **Metrics** record everything: counters, status codes, latency percentiles, top talkers.
- **Alerts** fire when thresholds break, and the danger level moves up the ladder.

**3. Nothing is actually attacked.**
The simulator is pure maths. It models a queue, adds fake traffic, and reports
what would happen. Zero packets are sent to a network. This is why you can run
"a 3000 rps flood" on a laptop.

**4. The state is colour-coded.**
Six levels from calm to on-fire, so you can see pressure at a glance.

| Level | Meaning |
|---|---|
| `RAW` | idle / clean |
| `WARM` | normal load |
| `SIMMER` | elevated, watch it |
| `SIZZLE` | suspicious, mitigations armed |
| `SMOKE` | under attack, shedding load |
| `BURNT` | overloaded, service degraded |

**5. Every defence has a breakfast name.**

| Tool | What it does |
|---|---|
| `MUFFIN` | the HTTPS server itself |
| `JAM` | WAF rule set |
| `SYRUP` | token bucket rate limiter |
| `PANCAKE` | bounded priority queue + admission gate |
| `FRIDGE` | TTL cache |
| `GRIDDLE` | database connection pool |
| `TOAST` | TLS cert forge + TLS audit |
| `SIZZLE` / `CEREAL` | metrics and rolling windows |
| `BACON` | alert engine |
| `OMELETTE` | traffic simulator (pure maths) |
| `MENU` | dashboard and landing page |
| `SCRAMBLE` | the test suite |

Names are silly. Behaviour is real.

---

## Things to try

Start the server in one terminal. Use a second terminal.

**Hit the endpoints**

```bash
curl -k https://127.0.0.1:8443/health
curl -k https://127.0.0.1:8443/api/fast
curl -k https://127.0.0.1:8443/api/slow?ms=300
curl -k https://127.0.0.1:8443/api/db
curl -k https://127.0.0.1:8443/waf-test
```

**Trigger the rate limiter** (25 requests fast, then a wall of `429`)

```bash
for i in $(seq 1 40); do curl -sk -o /dev/null -w "%{http_code} " https://127.0.0.1:8443/api/fast; done; echo
```

**Trigger the WAF** (expect `403`)

```bash
curl -k https://127.0.0.1:8443/../../etc/passwd
curl -k "https://127.0.0.1:8443/api/fast?q=1+union+select+1"
```

**Fake a crowd of clients**

```bash
python ironwaffle.py flood --clients 40 --rps 25 --duration 20
```

Each thread pretends to be a different client using a header, so one loopback IP
looks like 40 machines. Watch the dashboard change colour while it runs.

**Run an attack scenario with zero packets**

```bash
python ironwaffle.py sim --all
python ironwaffle.py sim --scenario volumetric
python ironwaffle.py sim --scenario waf_tuned
```

**Turn the mitigations off and on and compare**

```bash
python ironwaffle.py sim --scenario volumetric                    # no defence
python ironwaffle.py sim --scenario volumetric --effectiveness 1  # full scrubbing
```

Same attack, wildly different result. That is the whole lesson.

---

## Endpoints

| Path | What it is |
|---|---|
| `/` | index of everything |
| `/dashboard` | live colour dashboard, refreshes every 2s |
| `/metrics` | full JSON telemetry |
| `/health` | liveness probe |
| `/danger` | current danger level as text |
| `/reset` | clear counters |
| `/waf-test` | run the WAF against sample URLs |
| `/sim?scenario=NAME` | simulation result as JSON |
| `/api/fast` | cheap endpoint |
| `/api/slow?ms=250` | slow endpoint, burns workers |
| `/api/db` | forces a pooled DB call |
| `/api/cache?k=x` | cache HIT / MISS demo |
| `/api/big?kb=256` | bandwidth demo |
| `/api/boom` | always `500` |
| `/static/x.js` | cached asset |

Status codes are meaningful: `403` = WAF, `429` = rate limit, `503` = queue full.

---

## Commands

| Command | What it does |
|---|---|
| `python ironwaffle.py serve` | run the HTTPS lab |
| `python ironwaffle.py serve --no-tls --port 8080` | plain HTTP instead |
| `python ironwaffle.py serve --rate-limit 8 --max-inflight 4` | tight limits, easy to trigger |
| `python ironwaffle.py sim --all` | every scenario + comparison table |
| `python ironwaffle.py flood --clients 40` | loopback load test |
| `python ironwaffle.py cert` | make the TLS cert and audit it |
| `python ironwaffle.py doctor` | check environment and policy |
| `python ironwaffle.py selftest` | run the test suite |
| `python ironwaffle.py brief` | architecture + incident runbook |

---

## Tests

```bash
python ironwaffle.py selftest
```

Expect `0` failures. The suite covers rate limits, rolling windows, thread
safety, the WAF, the cache, the DB pool, the simulator maths, recovery time,
and a real end-to-end test over a loopback socket.

```
tests run            58
failures + errors    0
ALL GREEN. The lab is reproducible.
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Address already in use` | `--port 8444` |
| Browser certificate warning | Expected. Click through, or `curl -k` |
| `curl: (60)` | Add `-k` |
| Everything returns `429` | You are the attacker. Raise `--rate-limit` |
| Everything returns `503` | Raise `--max-inflight` |
| Everything returns `403` | A WAF rule matched. Check `/waf-test` |
| Raw escape codes in PowerShell | `$env:IRONWAFFLE_COLOR='always'`, use Windows Terminal |
| `bash: $'\r': command not found` | File has Windows line endings. `sed -i 's/\r$//' recriminat.txt` |
| Metrics all zero | No traffic yet. Hit `/api/fast` |
| No `openssl`, no `cryptography` | Server falls back to plain HTTP automatically |

---

## Safety rules

This lab is deliberately boring about the network.

- Binds `127.0.0.1` **only**. Never a public interface.
- No DNS lookups, no third-party services.
- No real botnet. No spoofed source addresses.
- No real attack traffic. The flood is just normal TCP to loopback.
- Attack traffic is **simulated maths**, clearly labelled everywhere.
- Bounded data structures everywhere, so memory cannot run away.
- `Ctrl+C` shuts down cleanly.

The internet is used **once**, by the installer, to download Python packages.
After that the lab is fully offline.

---

## Files

| File | Purpose |
|---|---|
| `ironwaffle.py` | the whole lab, single file |
| `recriminat.txt` | polyglot installer for Windows and Kali |
| `README.md` | this file |
| `.ironwaffle/` | auto-created: cert, key, logs |
| `.venv/` | auto-created: virtual environment |

Delete `.venv/` and `.ironwaffle/` to fully uninstall.

---

## Learning outcomes

After an hour with this you should be able to explain:

- The difference between DoS and DDoS, and why distribution beats IP blocking.
- Why bandwidth, packets per second, connections per second and requests per
  second are four completely different problems.
- What volumetric, state-exhaustion and application-layer attacks actually hit.
- Why a flash crowd and an attack look identical from the inside.
- Which defence belongs at which layer, and why no single one wins.
- Why the only metric that matters during an incident is **legitimate success rate**.

---

## Uninstall

```bash
rm -rf .venv .ironwaffle
```

Windows:

```powershell
Remove-Item -Recurse -Force .venv, .ironwaffle
```

Nothing was installed system-wide unless you used `--no-venv`.

---

**IRON WAFFLE OMEGA v1.0.0 "FULL BREAKFAST"**
Loopback only. Zero packets. Real defences.