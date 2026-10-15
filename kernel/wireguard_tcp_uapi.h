/* SPDX-License-Identifier: GPL-2.0 */
/*
 * WGTCP UAPI extensions.
 *
 * This shim layers WGTCP's WireGuard-UAPI additions on top of the kernel's
 * own <uapi/linux/wireguard.h> instead of shipping a forked copy of it. A
 * forked copy cannot serve a single portable source: the kernel renamed its
 * uapi include guard between 6.12 (_WG_UAPI_WIREGUARD_H) and 7.0
 * (_UAPI_LINUX_WIREGUARD_H), so a forked header stops suppressing the kernel's
 * on 7.0 and the enums get declared twice. Including the kernel's header and
 * adding only the genuinely WGTCP-specific bits here builds cleanly on both.
 *
 * Force-included for every translation unit via kernel/Makefile.
 */

#ifndef _WG_TCP_UAPI_H
#define _WG_TCP_UAPI_H

#include <linux/version.h>
#include <uapi/linux/wireguard.h>

/* --- TCP transport selector: WGTCP-only, present on no stock kernel --- */
#ifndef WG_TRANSPORT_UDP
#define WG_TRANSPORT_UDP 0
#endif
#ifndef WG_TRANSPORT_TCP
#define WG_TRANSPORT_TCP 1
#endif

/*
 * WGDEVICE_A_TRANSPORT: an extra generic-netlink device attribute. The stock
 * enum ends "... WGDEVICE_A_PEERS, __WGDEVICE_A_LAST"; reuse that sentinel
 * slot for our attribute and widen the policy-array bound by one so
 * device_policy[WGDEVICE_A_MAX + 1] includes it.
 */
#ifndef WGDEVICE_A_TRANSPORT
#define WGDEVICE_A_TRANSPORT (__WGDEVICE_A_LAST)
#undef  WGDEVICE_A_MAX
#define WGDEVICE_A_MAX (__WGDEVICE_A_LAST)
#endif

/*
 * Dynamic-allowedips attributes. WGTCP introduced these; mainline adopted the
 * identical values in 7.0 (WGALLOWEDIP_F_REMOVE_ME == 1, WGALLOWEDIP_A_FLAGS
 * appended after CIDR_MASK). Define them only on pre-7.0 kernels, where the
 * stock header lacks them. The 7.0 boundary is coarse; refine if an
 * intermediate kernel needs finer granularity.
 */
#if LINUX_VERSION_CODE < KERNEL_VERSION(7, 0, 0)
#define WGALLOWEDIP_F_REMOVE_ME (1U << 0)
#define WGALLOWEDIP_A_FLAGS     (__WGALLOWEDIP_A_LAST)
#undef  WGALLOWEDIP_A_MAX
#define WGALLOWEDIP_A_MAX (__WGALLOWEDIP_A_LAST)
#endif

#endif /* _WG_TCP_UAPI_H */
