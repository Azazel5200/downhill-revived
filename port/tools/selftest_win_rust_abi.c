/* Asset-free Windows ARM64 C -> Rust staticlib linker/runtime smoke; NOT the game. */
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "dhd_render.h"

/* The real game supplies this log bridge. The fixture deliberately doesn't need it. */
void dhd_host_log(const char *line, size_t bytes)
{
    (void)line;
    (void)bytes;
}

int main(void)
{
    const char *version = dhdr_version();
    if (!version || strncmp(version, "dhd_render ", 11) != 0) {
        fputs("FAIL: invalid Rust renderer version over C ABI\n", stderr);
        return 2;
    }
    if (dhdr_device_features() != 0) {
        fputs("FAIL: GPU features must be zero before device initialization\n", stderr);
        return 3;
    }
    printf("PASS: native ARM64 C -> Rust renderer ABI: %s (GPU not initialized)\n", version);
    return 0;
}
