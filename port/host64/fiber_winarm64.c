/* Experimental fiber switch for classic Windows ARM64 (not ARM64EC).
   Same EE fiber interface as fiber_win64.c and fiber_arm64.c. The Windows ABI saves x19-x30,
   the low 64 bits of v8-v15 and the floating-point control register. Windows also keeps the
   running stack's bounds in its TEB (x18), which must follow the new SP for __chkstk and
   RtlCaptureStackBackTrace. This file is NOT a validated game target until --fiber-test passes
   on an ARM64 Windows device, including both guard-page faults. */
#include <stdint.h>
#include <string.h>
#include "fiber_switch.h"

/* Clang's ARM64 COFF assembler accepts these Windows function/unwind directives. A synthetic
   frame resumes at fiber_start with x19 holding fiber_entry's argument and x29=0 ending the
   frame chain. This is an explicit native switch, not an OS fiber or an ARM64EC transition.

   The 208-byte frame:
     0..79   x19-x28       80..95   x29-x30        96..159  d8-d15
     160     FPCR          168      TEB StackBase  176      TEB StackLimit
     184     TEB DeallocationStack                  192..207 padding

   The TEB offsets match Windows ARM64's platform register x18 and the Windows x64 adapter:
   StackBase +0x08, StackLimit +0x10, DeallocationStack +0x1478. The native device selftest
   must verify these offsets before this implementation is considered usable. */
__asm__(
".text\n"
".globl fiber_switch_asm\n"
".def fiber_switch_asm; .scl 2; .type 32; .endef\n"
"fiber_switch_asm:\n"
".seh_proc fiber_switch_asm\n"
"  sub sp, sp, #208\n"
".seh_stackalloc 208\n"
".seh_endprologue\n"
"  stp x19, x20, [sp,#0]\n"
"  stp x21, x22, [sp,#16]\n"
"  stp x23, x24, [sp,#32]\n"
"  stp x25, x26, [sp,#48]\n"
"  stp x27, x28, [sp,#64]\n"
"  stp x29, x30, [sp,#80]\n"
"  stp d8, d9, [sp,#96]\n"
"  stp d10, d11, [sp,#112]\n"
"  stp d12, d13, [sp,#128]\n"
"  stp d14, d15, [sp,#144]\n"
"  mrs x9, fpcr\n"
"  str x9, [sp,#160]\n"
"  ldr x9, [x18,#8]\n"
"  str x9, [sp,#168]\n"
"  ldr x9, [x18,#16]\n"
"  str x9, [sp,#176]\n"
"  ldr x9, [x18,#0x1478]\n"
"  str x9, [sp,#184]\n"
"  mov x2, sp\n"
"  str x2, [x0]\n"
"  mov sp, x1\n"
"  ldr x9, [sp,#168]\n"
"  str x9, [x18,#8]\n"
"  ldr x9, [sp,#176]\n"
"  str x9, [x18,#16]\n"
"  ldr x9, [sp,#184]\n"
"  str x9, [x18,#0x1478]\n"
"  ldp x19, x20, [sp,#0]\n"
"  ldp x21, x22, [sp,#16]\n"
"  ldp x23, x24, [sp,#32]\n"
"  ldp x25, x26, [sp,#48]\n"
"  ldp x27, x28, [sp,#64]\n"
"  ldp x29, x30, [sp,#80]\n"
"  ldp d8, d9, [sp,#96]\n"
"  ldp d10, d11, [sp,#112]\n"
"  ldp d12, d13, [sp,#128]\n"
"  ldp d14, d15, [sp,#144]\n"
"  ldr x9, [sp,#160]\n"
"  msr fpcr, x9\n"
"  isb\n"
"  add sp, sp, #208\n"
"  ret\n"
".seh_endproc\n"
".globl fiber_start\n"
".def fiber_start; .scl 2; .type 32; .endef\n"
"fiber_start:\n"
".seh_proc fiber_start\n"
".seh_endprologue\n"
"  mov x0, x19\n"
"  bl fiber_entry\n"
"  brk #0\n"
".seh_endproc\n"
);
void fiber_start(void);

void *fiber_frame(uintptr_t lo, uintptr_t hi, void *arg) {
    /* New-fiber stack: a page below lo is guarded; the initial SP is 16-aligned. */
    uint64_t *frame=(uint64_t *)(((hi-16)&~(uintptr_t)15)-208), fpcr;
    __asm__ volatile("mrs %0, fpcr" : "=r"(fpcr));
    memset(frame,0,208);
    frame[0]=(uintptr_t)arg;              /* x19 */
    frame[11]=(uintptr_t)fiber_start;      /* x30 */
    frame[20]=fpcr;
    frame[21]=hi; frame[22]=lo; frame[23]=lo;  /* Windows TEB stack bounds */
    return frame;
}
