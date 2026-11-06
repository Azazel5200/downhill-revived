/* Native Windows host OS services smoke: no game data, SDL3, renderer or guest runtime.
   One executable runs on ARM64 and x64 to catch accidental architecture-specific APIs. */
#include "host_api.h"
#include "host_os.h"
#include "../include/guest.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>

uintptr_t guest_base; /* Normally provided by host64/guest_memory.c. */

static void require(int ok, const char *what)
{
    if (!ok) {
        fprintf(stderr, "FAIL: Windows host OS: %s\n", what);
        exit(1);
    }
}

static void fp_check(void)
{
    unsigned saved = host_fp_csr();
    for (unsigned rc = 0; rc != 4; ++rc)
        for (unsigned flush = 0; flush != 2; ++flush) {
            unsigned requested = 0x1F80u | (rc << 13) | (flush ? 0x8040u : 0);
            host_fp_set_csr(requested);
            unsigned actual = host_fp_csr();
            require(((actual ^ requested) & 0xE040u) == 0, "FPCR/MXCSR rounding and flush bits");
        }
    host_fp_set_csr(saved);
}

static void protection_check(void)
{
    SYSTEM_INFO info;
    GetSystemInfo(&info);
    size_t bytes = info.dwPageSize;
    uint8_t *ptr = (uint8_t *)VirtualAlloc(NULL, bytes, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    require(ptr != NULL, "VirtualAlloc test page");
    guest_base = (uintptr_t)ptr;
    require(host_mem_protect(0, (uint32_t)bytes, HOST_MEM_NOACCESS), "make test page inaccessible");
    MEMORY_BASIC_INFORMATION m;
    require(VirtualQuery(ptr, &m, sizeof m) == sizeof m && m.Protect == PAGE_NOACCESS,
            "check no-access protection");
    require(host_mem_protect(0, (uint32_t)bytes, HOST_MEM_READWRITE), "restore test page");
    ptr[0] = 0xA5;
    require(ptr[0] == 0xA5, "access restored page");
    guest_base = 0;
    VirtualFree(ptr, 0, MEM_RELEASE);
}

int main(void)
{
    char path[2048], system[256];
    require(host_exe_path(path, sizeof path) > 0 && strstr(path, "selftest_win_host.exe") != NULL,
            "UTF-8 executable path");
    host_os_system(system, sizeof system);
    require(strstr(system, "Windows ") == system && strchr(system, ',') != NULL,
            "Windows version and processor identity");

    fp_check();
    uint64_t before = host_cycles();
    for (volatile unsigned i = 0; i < 10000; ++i) { }
    uint64_t after = host_cycles();
    require(before != 0 && after > before, "monotonic diagnostic counter");

    uintptr_t lo, hi;
    host_code_range(&lo, &hi);
    require(lo != 0 && hi > lo && (uintptr_t)main >= lo && (uintptr_t)main < hi,
            "PE executable code section");
    protection_check();

    host_putenv_s("DHD_HOST_OS_SELFTEST", "on");
    require(getenv("DHD_HOST_OS_SELFTEST") && strcmp(getenv("DHD_HOST_OS_SELFTEST"), "on") == 0,
            "Windows environment update");
    host_putenv("DHD_HOST_OS_SELFTEST=");
    require(!getenv("DHD_HOST_OS_SELFTEST") || !*getenv("DHD_HOST_OS_SELFTEST"),
            "Windows environment removal");

    printf("PASS: Windows host OS: FP control (8 modes), timer, PE code, UTF-8 path, CPU, "
           "memory protection, environment\n");
    printf("System: %s\n", system);
    return 0;
}
