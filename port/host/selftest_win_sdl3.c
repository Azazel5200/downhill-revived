/* A standalone, asset-free SDL3 startup test. Does not open a window or an audio device. */
#include <SDL3/SDL.h>
#include <stdio.h>
#include <string.h>

int main(void)
{
#if !defined(_M_ARM64)
#error The SDL3 ARM64 smoke must compile as native ARM64
#endif
    if (strcmp(SDL_GetPlatform(), "Windows") != 0) {
        fprintf(stderr, "FAIL: SDL3 unexpected platform: %s\n", SDL_GetPlatform());
        return 1;
    }
    if (!SDL_Init(0)) {
        fprintf(stderr, "FAIL: SDL3 initialization: %s\n", SDL_GetError());
        return 2;
    }
    printf("PASS: native Windows ARM64 SDL3 %d.%d.%d initialized (without opening devices)\n",
           SDL_MAJOR_VERSION, SDL_MINOR_VERSION, SDL_MICRO_VERSION);
    SDL_Quit();
    return 0;
}
