#!/usr/bin/env python3

import os
import shlex
import subprocess
import sys
from datetime import datetime
import pyfiglet
from termcolor import colored

# Clear screen
os.system("clear" if os.name != "nt" else "cls")

# ASCII banner
banner = pyfiglet.figlet_format("RECONHAWK")
print(colored(banner, "cyan"))

# ===== Colors =====
RED = "\033[91m"
GRN = "\033[92m"
CYN = "\033[96m"
YLW = "\033[93m"
RST = "\033[0m"

# ====== Title ======
print(f"{RED}CREATED BY CYBERGHOST{RST}\n")

# ===== Inputs =====
if len(sys.argv) > 1:
    target = sys.argv[1].strip()
else:
    target = input(f"{CYN}[?] Target domain: {RST}").strip()

if not target:
    print(f"{RED}[!] No target given.{RST}")
    sys.exit(1)

# Normalize the target safely
target = target.strip().lower()

# Remove URL scheme and www.
for prefix in ["http://", "https://", "www."]:
    if target.startswith(prefix):
        target = target[len(prefix):]

# Remove trailing slashes
target = target.rstrip("/")

if not target:
    print(f"{RED}[!] Invalid target after normalization.{RST}")
    sys.exit(1)

# ===== Paths & files =====
base_dir = os.path.expanduser("~/recon_results")
os.makedirs(base_dir, exist_ok=True)

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
subs_file = os.path.join(base_dir, f"{target}_{stamp}_subs.txt")
alive_file = os.path.join(base_dir, f"{target}_{stamp}_alive.txt")

# ===== Helper to run shell =====
def run(cmd):
    return subprocess.run(
        cmd, shell=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True
    )

print(f"{YLW}[*] Recon chain started for {target} (results: {base_dir}){RST}")

# ===== 0) preflight: check required tools =====
def check_tool(name):
    res = run(f"which {shlex.quote(name)}")
    return res.returncode == 0

missing = []
for t in ("subfinder", "httpx", "sort"):
    if not check_tool(t):
        missing.append(t)

if missing:
    print(f"{RED}[!] Missing tools: {', '.join(missing)}{RST}")
    print(f"{YLW}Install them first (use subfinder, httpx). Exiting.{RST}")
    sys.exit(1)

# ===== 1) subfinder =====
print(f"{CYN}[*] subfinder → collecting subdomains (silent)…{RST}")
cmd_subs = f"subfinder -silent -d {shlex.quote(target)} -o {shlex.quote(subs_file)}"
res1 = run(cmd_subs)

if res1.returncode != 0:
    print(f"{RED}[!] subfinder error:\n{res1.stderr.strip()}{RST}")
    sys.exit(1)

# De-dup + sort in-place
run(f"sort -u -o {shlex.quote(subs_file)} {shlex.quote(subs_file)}")

# Count subs safely
with open(subs_file, "r", encoding="utf-8", errors="ignore") as fh:
    subs_lines = [ln.strip() for ln in fh if ln.strip()]
subs_count = len(subs_lines)

if subs_count == 0:
    print(f"{RED}[!] No subdomains found. Check scope or DNS. Saved empty list at {subs_file}.{RST}")
    sys.exit(0)

# ===== 2) httpx =====
print(f"{CYN}[*] httpx → probing for alive (silent)…{RST}")

# Build stable httpx command
cmd_httpx = (
    f"cat {shlex.quote(subs_file)} | "
    f"httpx -silent -threads 50 -timeout 6 -follow-redirects -no-color "
    f"-o {shlex.quote(alive_file)}"
)

res2 = run(cmd_httpx)
# httpx sometimes returns non-zero even on success; check file existence
if res2.returncode != 0 and not os.path.exists(alive_file):
    print(f"{RED}[!] httpx error:\n{res2.stderr.strip()}{RST}")
    sys.exit(1)

# De-dup + sort alive too (if file exists)
if os.path.exists(alive_file):
    run(f"sort -u -o {shlex.quote(alive_file)} {shlex.quote(alive_file)}")
    with open(alive_file, "r", encoding="utf-8", errors="ignore") as fh:
        alive = [ln.strip() for ln in fh if ln.strip()]
else:
    alive = []

alive_count = len(alive)

# ===== Output policy: show alive only =====
print(f"{GRN}[+] Alive hosts ({alive_count}){RST}")
for url in alive:
    print(f"{GRN}{url}{RST}")

# ===== Summary (files saved silently) =====
print(f"{YLW}\n[*] Files saved:{RST}")
print(f"{GRN} • Subs [✓]>>>   {subs_file}{RST}")
print(f"{GRN} • Alive[✓]>>>  {alive_file}{RST}")
