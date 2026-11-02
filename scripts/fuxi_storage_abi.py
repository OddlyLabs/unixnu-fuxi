# SPDX-License-Identifier: BSD-2-Clause-Patent
"""The original IOBlockStorageDevice that UniXNU RamBlock's NativeRamBlock derives from, in the iPadOS 17.7.11 kernelcache.

Shared by scripts/build-fuxi-ram-block.py (binds NativeRamBlock's imports) and ci/check-ram-block-bindings.py (checks them in
the kernel that ships). UniXNU's own binder reads these from an audit of an earlier research build; the values were read from
the fuxi kernel of run 41439604891 and agree with those UniXNU's marble-milacy port records (docs/devices/marble-milacy.md).
They are the kernelcache's, so a kernel build does not move them.
"""

VPTR = 0xfffffff005cb44d0                     # IOBlockStorageDevice's vtable address point (__ZTV20IOBlockStorageDevice + 16)
SLOTS = 190
BINDINGS = {'__ZN20IOBlockStorageDeviceC2EPK11OSMetaClass': 0xfffffff00496ed98,
            '__ZN20IOBlockStorageDeviceD2Ev': 0xfffffff00496edb8,
            '__ZN20IOBlockStorageDevice10gMetaClassE': 0xfffffff006add1d0,
            '__ZTV20IOBlockStorageDevice': VPTR - 16}
# IOBlockStorageDevice's own implementations by slot: the six IOService slots it overrides (0 and 1 are the abstract
# destructors, which trap) and its non-pure slots from 168 on.
STORAGE_SLOTS = {
    0: 0xfffffff00496edbc, 1: 0xfffffff00496edc0, 7: 0xfffffff00496edc4, 21: 0xfffffff00496ee30, 33: 0xfffffff00496ee88,
    44: 0xfffffff00496ef38, 171: 0xfffffff00496f074, 182: 0xfffffff00496f038, 183: 0xfffffff00496f044,
    185: 0xfffffff00496f050, 186: 0xfffffff00496f05c, 187: 0xfffffff00496f068, 188: 0xfffffff00496f080,
    189: 0xfffffff00496f08c}
OVERRIDES = [0, 1, 7, 21, 33, 44]
PURE = [168, 169, 170, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 184]   # a concrete subclass implements all 14
# The protected constructor (it stores VPTR), and D2 followed by the two abstract destructors, D1 and D0, which are brk traps.
CODE = {0xfffffff00496ed98: 'fd7bbfa9fd0300919f440094289a00d008411391080000f9fd7bc1a8c0035fd6',
        0xfffffff00496edb8: '9c440014200020d4200020d4'}
# The family reaches IOService's constructor and destructor through these GOT slots, which the prelinker fills.
GOT = {'__ZN9IOServiceC2EPK11OSMetaClass': 0xfffffff005cb3430, '__ZN9IOServiceD2Ev': 0xfffffff005cb3438}
