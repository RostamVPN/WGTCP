ccflags-y := -D'pr_fmt(fmt)=KBUILD_MODNAME ": " fmt'
# Force-include the WGTCP uapi shim, which pulls in the kernel's own
# <uapi/linux/wireguard.h> and layers only the WGTCP extensions on top.
# (No -I../include: we deliberately use the kernel's uapi header, not a
# forked copy, so one source builds across kernel versions.)
ccflags-y += -include $(src)/wireguard_tcp_uapi.h
ccflags-$(CONFIG_WIREGUARD_DEBUG) += -DDEBUG

# Feature-probe: WQ_PERCPU is an enum added to alloc_workqueue on newer kernels
# (backported into some 6.12 point releases). Detect it in the kernel headers so
# device.c requests per-CPU explicitly where required, and omits it (0) where
# per-CPU is still the default. Robust to distro backports; version guards aren't.
# Debian splits headers: the running-kernel build dir is linux-headers-<v>-<arch>
# but workqueue.h lives in the version-matched -common sibling — check both
# (version-exact via sed so another installed kernel can't false-positive).
# $(srctree) is the /lib/modules/<ver>/build symlink; resolve it to the real
# linux-headers-<ver>-<arch> path first, then derive the version-matched -common.
_wq_src    := $(realpath $(srctree))
_wq_common := $(shell echo '$(_wq_src)' | sed 's/-[a-z0-9_]*$$/-common/')
_wq_hdrs   := $(_wq_src)/include/linux/workqueue.h $(_wq_common)/include/linux/workqueue.h
ccflags-y  += $(if $(shell grep -l 'WQ_PERCPU' $(_wq_hdrs) 2>/dev/null),-DHAVE_WQ_PERCPU)

# WireGuard TCP debug levels (add to EXTRA_CFLAGS or uncomment here):
#   -DWG_TCP_VERBOSE    Function enter/exit traces, param dumps (very noisy)
#   -DWG_TCP_DIAG       TCP performance diagnostics (cwnd, rtt, retrans)
#   Neither              No debug output (production)
# Example: make ... EXTRA_CFLAGS="-DWG_TCP_DIAG"
# ccflags-y += -DWG_TCP_VERBOSE -DWG_TCP_DIAG
wireguard-y := main.o
wireguard-y += noise.o
wireguard-y += device.o
wireguard-y += peer.o
wireguard-y += timers.o
wireguard-y += queueing.o
wireguard-y += send.o
wireguard-y += receive.o
wireguard-y += socket.o
wireguard-y += wg_tcp.o
wireguard-y += wg_tcp_debug.o
wireguard-y += peerlookup.o
wireguard-y += allowedips.o
wireguard-y += ratelimiter.o
wireguard-y += cookie.o
wireguard-y += netlink.o
wireguard-y += generated/netlink.o
obj-$(CONFIG_WIREGUARD) := wireguard.o
