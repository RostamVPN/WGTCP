#!/bin/sh
# Regenerate BIG-WireguardTCP-Patch: the WireGuard TCP delta against clean
# upstream checkouts of Linux (drivers/net/wireguard) and wireguard-tools (src).
#
# usage: scripts/generate-big-patch.sh <linux-checkout> <wireguard-tools-checkout> [output]
set -eu
usage="usage: $0 <linux-checkout> <wireguard-tools-checkout> [output]"
linux=${1:?$usage}
tools=${2:?$usage}
repo=$(cd "$(dirname "$0")/.." && pwd)
out=${3:-$repo/BIG-WireguardTCP-Patch}

kernel_sha=$(git -C "$linux" rev-parse HEAD)
kernel_tag=$(git -C "$linux" describe --tags --exact-match 2>/dev/null || echo "$kernel_sha")
tools_sha=$(git -C "$tools" rev-parse HEAD)
target=$(git -C "$repo" rev-parse HEAD)

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
cp -a "$linux/drivers/net/wireguard" "$work/kernel"
cp -a "$tools/src" "$work/tools"
git -C "$work" init -q
git -C "$work" -c user.name=baseline -c user.email=baseline@localhost add -A
git -C "$work" -c user.name=baseline -c user.email=baseline@localhost commit -q -m baseline
rm -rf "$work/kernel" "$work/tools"
cp -a "$repo/kernel" "$work/kernel"
cp -a "$repo/tools" "$work/tools"
rm -f "$work/tools/scale_test.py"
git -C "$work" add -A

{
cat <<HEADER
BIG WireGuard TCP implementation patch

Kernel baseline: Linux $kernel_tag ($kernel_sha)
Tools baseline: wireguard-tools $tools_sha
Target repository: https://github.com/RostamVPN/WGTCP.git
Target source commit: $target

This patch carries the kernel module and the wg tool changes that make
WireGuard TCP build and run on the baselines above. The module uses the
kernel's own <uapi/linux/wireguard.h>; the WGTCP extensions live in
kernel/wireguard_tcp_uapi.h. Upstream kernel crypto, SIMD and architecture
assembly are not modified. The patched module also builds on Linux 6.12
point releases through LINUX_VERSION_CODE guards.

Prepare the baseline from clean official checkouts:

    git clone --depth 1 --branch $kernel_tag https://github.com/torvalds/linux.git linux
    git clone https://github.com/WireGuard/wireguard-tools.git wireguard-tools
    git -C wireguard-tools checkout $tools_sha
    mkdir WireguardTCP-patch-base
    cp -a linux/drivers/net/wireguard WireguardTCP-patch-base/kernel
    cp -a wireguard-tools/src WireguardTCP-patch-base/tools

Apply and build with matching kernel headers installed:

    cd WireguardTCP-patch-base
    git apply --binary /path/to/BIG-WireguardTCP-Patch
    make -C tools -j\$(nproc)
    make -C /lib/modules/\$(uname -r)/build M=\$PWD/kernel CONFIG_WIREGUARD=m -j\$(nproc) modules

HEADER
git -C "$work" -c core.safecrlf=false diff --cached --binary --full-index --no-ext-diff
} > "$out"
echo "Wrote $out ($(wc -c < "$out" | tr -d ' ') bytes)"
