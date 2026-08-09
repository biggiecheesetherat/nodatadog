#!/usr/bin/env python3
"""
NoDatadog.py

This script patches `Vortex.exe` binary strings by neutering Datadog telemetry hostnames 
and endpoint URLs to force all background telemetry requests to fail safely to 127.0.0.1 (localhost).

Binary patch technique:
- Preserves exact byte length for PE alignment.
- Replaces target telemetry domain strings (`datadoghq.com`, `datadog`, `browser-intake`) 
  with dummy localhost domains (`127.0.0.1.invalid`, `00000000`, etc.).

This script is a part of the upcoming VortexRE project, a reverse engineered version of Vortex.
"""

from nodatadog import patched
import sys
import os

# List of target domains / string patterns to block
TARGET_DOMAINS = [
    "browser-intake-datadoghq.com",
    "browser-intake-us5-datadoghq.com",
    "http-intake.logs.datadoghq.com",
    "api.datadoghq.com",
    "datadoghq.com",
    "datadog.com",
    "datadog",
]

patched = False

def make_replacement(domain: str) -> bytes:
    """Generate a byte-for-byte length-matched replacement string pointing to 127.0.0.1 / invalid domain."""
    orig_len = len(domain)
    prefix = "127.0.0.1.disabled"
    if orig_len <= len("127.0.0.1"):
        repl = "0" * orig_len
    elif orig_len <= len(prefix):
        repl = ("127.0.0.1." + "0" * orig_len)[:orig_len]
    else:
        pad_len = orig_len - len(prefix)
        repl = prefix + ("." + "x" * pad_len)[:pad_len]
    
    repl_bytes = repl.encode("ascii")
    assert len(repl_bytes) == orig_len, f"Length mismatch for {domain}: {len(repl_bytes)} != {orig_len}"
    return repl_bytes

def patch_binary(input_path: str, output_path: str):
    if not os.path.exists(input_path):
        print(f"[!] Error: Input binary '{input_path}' not found.")
        sys.exit(1)

    print(f"[*] Reading binary: {input_path} ({os.path.getsize(input_path)} bytes)...")
    with open(input_path, "rb") as f:
        data = f.read()

    patched_data = bytearray(data)
    total_replacements = 0

    for domain in TARGET_DOMAINS:
        original = domain.encode("ascii")
        replacement = make_replacement(domain)
        count = data.count(original)
        if count > 0:
            print(f"[+] Found {count} occurrence(s) of '{domain}'. Patching to '{replacement.decode('ascii')}'...")
            patched_data = patched_data.replace(original, replacement)
            total_replacements += count
    global patched
    if total_replacements > 0:
        print(f"[*] Saving patched executable to: {output_path}")
        with open(output_path, "wb") as f:
            f.write(patched_data)
        patched = True
        print(f"[✓] Successfully patched {total_replacements} telemetry string(s)!")
    else:
        print("[!] No explicit Datadog telemetry domain strings were found in the target binary.")
        print("[!] Note: The official client may construct telemetry endpoints dynamically or rely on system DNS.")
        print("[!] To keep you safe, the program will not output the binary.")
def print_hosts_advice():
    print("\n" + "=" * 65)
    print("Incase the patch fails, this should be in place!")
    print("=" * 65)
    print("To block Datadog telemetry system-wide on Windows or Linux,")
    print("add the following lines to your hosts file:")
    print("  Linux:   /etc/hosts")
    print("  Windows: C:\\Windows\\System32\\drivers\\etc\\hosts")
    print("\n# Block Vortex Datadog Telemetry")
    print("127.0.0.1  browser-intake-datadoghq.com")
    print("127.0.0.1  http-intake.logs.datadoghq.com")
    print("127.0.0.1  api.datadoghq.com")
    print("127.0.0.1  datadoghq.com")
    print("=" * 65)

if __name__ == "__main__":
    print("NoDatadog.py - Coded by Themeatly2, based on VortexRE.")
    print("=" * 65)
    input_exe = sys.argv[1] if len(sys.argv) > 1 else "Vortex.exe"
    output_exe = sys.argv[2] if len(sys.argv) > 2 else "Vortex_patched.exe"
    
    patch_binary(input_exe, output_exe)
    if patched:
        print_hosts_advice()
    print("=" * 65)
    print("Thank you for using NoDatadog.py!")
