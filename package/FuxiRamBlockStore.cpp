// SPDX-License-Identifier: BSD-2-Clause-Patent
// The persistent-store hooks NativeRamBlock.cpp (an unchanged copy of UniXNU RamBlock 4be2d7e) imports weakly. On sheng
// ShengUfs provides them; fuxi has no storage driver, and the kernel is linked statically, so a weak import still needs a
// definition. Mode 0 means no store: NativeRamBlock keeps a volatile RAM disk and never calls the others.
#include <stdint.h>

extern "C" {
unsigned native_ufs_store_mode(void) {return 0;}
int native_ufs_store_open(uint64_t, uint64_t *, const char **why) {if (why) *why = "no store on fuxi"; return 0;}
int native_ufs_store_read(uint64_t, uint32_t, void *) {return 0;}
int native_ufs_store_write(uint64_t, uint32_t, const void *) {return 0;}
int native_ufs_store_sync(void) {return 0;}
unsigned native_ufs_store_gpt_check(void) {return 0xff;}
}
