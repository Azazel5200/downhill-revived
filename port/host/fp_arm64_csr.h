/* The module speaks x86 MXCSR, even when its host is AArch64. Translate the rounding and
   flush-to-zero controls into FPCR in one place for the POSIX and Windows ARM64 hosts.
   Both AArch64 build paths use clang, which supports these architectural register accesses. */
#ifndef PORT_HOST_FP_ARM64_CSR_H
#define PORT_HOST_FP_ARM64_CSR_H

#include <stdint.h>

#if defined(__aarch64__) || defined(_M_ARM64)
static inline unsigned host_arm64_fp_csr(void)
{
    static const unsigned rmode_to_rc[4] = {0, 2, 1, 3};
    uint64_t v;
    __asm__ volatile("mrs %0, fpcr" : "=r"(v));
    return 0x1F80u | (rmode_to_rc[(v >> 22) & 3] << 13) | ((v >> 24) & 1 ? 0x8040u : 0);
}

static inline void host_arm64_fp_set_csr(unsigned csr)
{
    static const unsigned rc_to_rmode[4] = {0, 2, 1, 3};
    uint64_t now, v = (uint64_t)rc_to_rmode[(csr >> 13) & 3] << 22 |
                      (csr & 0x8040u ? 1ull << 24 : 0);
    __asm__ volatile("mrs %0, fpcr" : "=r"(now));
    if (now != v) __asm__ volatile("msr fpcr, %0\n\tisb" :: "r"(v) : "memory");
}
#endif

#endif
