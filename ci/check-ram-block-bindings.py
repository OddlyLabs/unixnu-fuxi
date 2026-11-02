#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-2-Clause-Patent
"""Check the RAM block bindings of the fuxi kernel after the link: NativeRamBlock against the original IOStorageFamily.

usage: check-ram-block-bindings.py <prelinked kernel.macho> [--contract-only]

scripts/build-fuxi-ram-block.py builds NativeRamBlock (kits/fuxi/NativeRamBlock.cpp, an unchanged copy of UniXNU RamBlock
4be2d7e) without UniXNU's storage audit: its IOBlockStorageDevice imports are bound to the kernelcache addresses in
scripts/fuxi_storage_abi.py. This script checks them in the kernel that ships:

- the original IOStorageFamily: the protected constructor and the destructors as pinned, the GOT slots through which they call
  IOService's constructor and destructor holding this kernel's, getMetaClass returning the bound metaclass, and the 190-slot
  vtable with its 14 pure slots, its 6 IOService overrides and its own implementations at the bound addresses;
- unless --contract-only: the bound symbols, and NativeRamBlock's vtable, every slot of which is either its own (all pure
  slots among them) or the entry of the original table.
It reads the Mach-O itself, so it runs without Xcode.
"""
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from fuxi_storage_abi import BINDINGS, CODE, GOT, OVERRIDES, PURE, SLOTS, STORAGE_SLOTS, VPTR

NEEDED = ['__ZTV14NativeRamBlock', '_native_ram_block_volume_device', '_native_ufs_store_mode']


def fail(message):
    raise SystemExit('check-ram-block-bindings: ' + message)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    contract_only = '--contract-only' in sys.argv[2:]
    data = open(sys.argv[1], 'rb').read()
    if struct.unpack_from('<I', data)[0] != 0xfeedfacf:
        fail('not a 64-bit Mach-O')
    segments, symtab, at = [], None, 32
    for _ in range(struct.unpack_from('<I', data, 16)[0]):
        cmd, size = struct.unpack_from('<II', data, at)
        if cmd == 0x19:
            segments.append((data[at + 8:at + 24].rstrip(b'\0').decode(), *struct.unpack_from('<QQQQ', data, at + 24)))
        elif cmd == 2:
            symtab = struct.unpack_from('<IIII', data, at + 8)
        at += size
    if symtab is None:
        fail('no symbol table')

    def segment(va):
        return next((name for name, vm, size, _, _ in segments if vm <= va < vm + size), None)

    def read(va, n):
        for _, vm, _, fileoff, filesize in segments:
            if vm <= va and va + n <= vm + filesize:
                return data[fileoff + va - vm:fileoff + va - vm + n]
        fail(f'{va:#x} is not backed by the file')

    def words(va, n):
        return struct.unpack(f'<{n}Q', read(va, 8 * n))

    symoff, nsyms, stroff, _ = symtab
    names = {}
    for i in range(nsyms):
        strx, kind, _, _, value = struct.unpack_from('<IBBHQ', data, symoff + 16 * i)
        if not kind & 0xe0 and kind & 0x0e:
            names[data[stroff + strx:data.index(b'\0', stroff + strx)].decode()] = value

    for va, want in CODE.items():
        if read(va, len(want) // 2).hex() != want:
            fail(f'IOStorageFamily instructions at {va:#x} differ from the pinned contract')
    for name, slot in GOT.items():
        if words(slot, 1)[0] != names[name]:
            fail(f'IOStorageFamily is not bound to this kernel\'s {name} (GOT {slot:#x})')
    adrp, add = struct.unpack('<2I', read(STORAGE_SLOTS[7], 8))
    if adrp & 0x9f00001f != 0x90000000 or add & 0xffc003ff != 0x91000000:
        fail('IOBlockStorageDevice::getMetaClass is not adrp/add x0')
    page = ((adrp >> 29 & 3) | (adrp >> 5 & 0x7ffff) << 2) << 12
    page -= 1 << 33 if page & 1 << 32 else 0
    meta = (STORAGE_SLOTS[7] & ~0xfff) + page + (add >> 10 & 0xfff)
    if meta != BINDINGS['__ZN20IOBlockStorageDevice10gMetaClassE']:
        fail(f'IOBlockStorageDevice::getMetaClass returns {meta:#x}, not the bound gMetaClass')
    original = words(VPTR, SLOTS)
    service = words(names['__ZTV9IOService'] + 16, 168)
    if not all(original) or words(VPTR + SLOTS * 8, 1)[0] != 0:
        fail('IOBlockStorageDevice vtable is not 190 slots')
    if [i for i in range(168) if original[i] != service[i]] != OVERRIDES:
        fail('IOBlockStorageDevice overrides other IOService slots than the pinned ones')
    if [i for i, a in enumerate(original) if a == names['___cxa_pure_virtual']] != PURE:
        fail('IOBlockStorageDevice pure slots changed')
    for slot, va in STORAGE_SLOTS.items():
        if original[slot] != va or segment(va) != '__PLK_TEXT_EXEC':
            fail(f'IOBlockStorageDevice slot {slot} holds {original[slot]:#x}, not {va:#x}')
    print('IOStorageFamily contract: instructions, IOService bindings, metaclass and 190-slot vtable as pinned')
    if contract_only:
        return
    missing = [name for name in NEEDED if name not in names]
    if missing:
        fail('missing from the kernel: ' + ', '.join(missing))
    for name, va in BINDINGS.items():
        if name in names and names[name] != va:
            fail(f'{name} is bound to {names[name]:#x}, not {va:#x}')
    own = words(names['__ZTV14NativeRamBlock'] + 16, SLOTS)
    owned = [slot for slot in range(SLOTS) if own[slot] != original[slot]]
    if not set(PURE) | {0, 1} <= set(owned):
        fail(f'NativeRamBlock leaves original slots {sorted(set(PURE) | {0, 1} - set(owned))} in place')
    outside = [slot for slot in owned if segment(own[slot]) != '__TEXT_EXEC']
    if outside:
        fail(f'NativeRamBlock slots {outside} differ from the original table but point outside the kernel text')
    print(f'NativeRamBlock: {len(owned)} own slots, {SLOTS - len(owned)} as in the original table; {len(NEEDED)} symbols defined')


if __name__ == '__main__':
    main()
