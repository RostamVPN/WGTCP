#!/usr/bin/env python3
# Copyright 2026 Internet Mastering & Company, Inc. <sina@redteam.net>
# SPDX-License-Identifier: Apache-2.0
"""Load N synthetic peers onto a WireGuard interface and measure the cost.

Measures two things that matter for a 10M-peer interface:

  1. peer-add throughput -- the ceiling on how fast a provisioning API can
     populate or repopulate an interface (e.g. after a restart).
  2. handshake-path latency proxy -- `wg show <if> transfer` walks every peer
     via the netlink dump path; timing it at increasing peer counts exposes
     whether per-peer lookup is flat or degrading.

Peers are added in batches via a single `wg setconf`-style stdin feed, since
one netlink transaction per peer is far slower and would measure the wrong
thing.
"""

import argparse
import base64
import os
import subprocess
import sys
import time


def peer_pubkeys(n):
    """Generate n distinct 32-byte peer public keys.

    These are random values, not keys derived from private keys. The peer
    table stores whatever 32-byte public key it is given and only performs
    curve operations during a handshake, so random keys exercise the hashtable
    and per-peer allocation paths identically while avoiding 2n scalar
    multiplications. This test never completes a handshake against these
    peers, so on-curve validity is irrelevant here.

    Deriving real keys via `wg pubkey` costs one process spawn per key, which
    dominated the measurement and is why it is not done.
    """
    seen = set()
    out = []
    while len(out) < n:
        k = os.urandom(32)
        if k in seen:
            continue
        seen.add(k)
        out.append(base64.b64encode(k).decode())
    return out


def add_peers(iface, pubs, base_ip_int, batch):
    """Add peers in batches; return (total_seconds, per_batch_rates)."""
    rates = []
    t_total = 0.0
    for i in range(0, len(pubs), batch):
        chunk = pubs[i:i + batch]
        args = ["wg", "set", iface]
        for j, pk in enumerate(chunk):
            ip_int = base_ip_int + i + j
            ip = ".".join(str((ip_int >> s) & 0xFF) for s in (24, 16, 8, 0))
            args += ["peer", pk, "allowed-ips", f"{ip}/32"]
        t0 = time.perf_counter()
        subprocess.run(args, check=True, capture_output=True)
        dt = time.perf_counter() - t0
        t_total += dt
        rates.append(len(chunk) / dt)
    return t_total, rates


def time_dump(iface, reps=3):
    """Time the netlink dump path, which touches every peer."""
    best = float("inf")
    for _ in range(reps):
        t0 = time.perf_counter()
        subprocess.run(["wg", "show", iface, "transfer"],
                       check=True, capture_output=True)
        best = min(best, time.perf_counter() - t0)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iface", default="wgscale")
    ap.add_argument("--total", type=int, default=200000)
    ap.add_argument("--step", type=int, default=50000)
    ap.add_argument("--batch", type=int, default=5000)
    args = ap.parse_args()

    # 10.0.0.0 as an integer, so allowed-ips spans the 10/8 space.
    base_ip = (10 << 24)

    print(f"# generating {args.total} peer public keys", flush=True)
    t0 = time.perf_counter()
    pubs = peer_pubkeys(args.total)
    print(f"# keygen took {time.perf_counter()-t0:.1f}s "
          f"({len(pubs)} pubkeys)", flush=True)

    print(f"{'peers':>10} {'add_rate/s':>12} {'dump_ms':>10} {'rss_MB':>9}",
          flush=True)

    added = 0
    while added < args.total:
        n = min(args.step, args.total - added)
        _, rates = add_peers(args.iface, pubs[added:added + n],
                             base_ip + added, args.batch)
        added += n
        avg_rate = sum(rates) / len(rates)
        dump_ms = time_dump(args.iface) * 1000
        with open("/proc/meminfo") as f:
            mi = {l.split(":")[0]: l.split()[1] for l in f}
        used_mb = (int(mi["MemTotal"]) - int(mi["MemAvailable"])) // 1024
        print(f"{added:>10} {avg_rate:>12.0f} {dump_ms:>10.1f} {used_mb:>9}",
              flush=True)


if __name__ == "__main__":
    sys.exit(main())
