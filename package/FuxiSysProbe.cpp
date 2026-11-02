// SPDX-License-Identifier: BSD-2-Clause-Patent
// One report row on how far the system got, for the touch probe's panic message: the root filesystem's type and the device it
// was mounted from, then the first processes by pid with their names and the number of processes. Empty before the root is
// mounted, so the reports of earlier boots stay as they were. Kept apart from FuxiTouchProbe.cpp so that the BSD headers
// stay out of the probe.
#include <sys/types.h>
#include <sys/vnode.h>
#include <sys/mount.h>
#include <sys/proc.h>
#include <libkern/libkern.h>

extern "C" const char *fuxi_sys_row(char *out, size_t size) {
    if (!out || size < 64) return "";
    vnode_t root = vfs_rootvnode();
    if (!root) {out[0] = 0; return out;}
    struct vfsstatfs *sf = vfs_statfs(vnode_mount(root));
    int n = snprintf(out, size, "\nSYS root %.15s %.40s", sf ? sf->f_fstypename : "?", sf ? sf->f_mntfromname : "?");
    vnode_put(root);
    unsigned found = 0;
    for (int pid = 1; pid < 1000; ++pid) {
        proc_t p = proc_find(pid);
        if (!p) continue;
        if (++found <= 6 && n > 0 && n < static_cast<int>(size) - 24) {
            char name[17] = {};
            proc_name(pid, name, sizeof name);
            n += snprintf(out + n, size - static_cast<size_t>(n), " %d:%s", pid, name);
        }
        proc_rele(p);
    }
    if (n > 0 && n < static_cast<int>(size) - 12) snprintf(out + n, size - static_cast<size_t>(n), " n%u", found);
    return out;
}
