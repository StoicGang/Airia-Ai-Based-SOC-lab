# Recovering Arch Linux from Cascading Library Corruption

> **Context:** This issue occurred on a VirtualBox VM running Arch Linux as part of the [Airia SOC Lab](https://github.com/StoicGang/Airia-Ai-Based-SOC-lab) environment. The recovery process is applicable to any Arch Linux system that suffers widespread shared library corruption after an interrupted upgrade.

---

## The Problem

A `pacman -Syu` system upgrade was interrupted mid-write. The VM host also ran out of disk space during subsequent repair attempts. This combination caused:

- Core shared libraries written as empty or truncated files (0 bytes / "file too short")
- `pacman` unable to run — it depends on the same corrupted libraries
- `bash` and `chroot` broken — missing runtime dependencies
- A circular failure: the tools needed to fix the system were themselves broken

### Error Signatures

If you see any of these, you're likely dealing with the same issue:

```
/sbin/init: error while loading shared libraries: /usr/lib/libcrypto.so.3: file too short
```

```
pacman: error while loading shared libraries: /usr/lib/liblzma.so.5: file too short
```

```
bash: error while loading shared libraries: libreadline.so.8: cannot open shared object file
```

```
error while loading shared libraries: libgcc_s.so.1: cannot open shared object file
```

```
VERR_DISK_FULL (VirtualBox)
```

---

## Prerequisites

- Arch Linux ISO (download from [archlinux.org](https://archlinux.org/download/))
- Access to your VM boot settings (VirtualBox: F12 at boot → CD-ROM)
- Enough free disk space on the **host machine** (at least 10 GB free)

---

## Recovery Steps

### Step 1 — Boot from the Arch ISO

The installed system cannot repair itself because its own tools depend on the corrupted libraries. Boot from external media instead.

**VirtualBox:** Press `F12` during boot → select `CD-ROM` (attach the Arch ISO to the virtual optical drive first).

### Step 2 — Check host disk space

Before doing anything in the VM, verify your **host machine** has free disk space. VirtualBox will silently fail writes if the host is full.

```
VERR_DISK_FULL → Free space on host, not inside the VM
```

Free at least 10 GB on the host before continuing.

### Step 3 — Mount the installed system

Identify your partitions:

```bash
lsblk
```

Typical layout:
- `/dev/sda1` → boot partition
- `/dev/sda2` → root partition

Mount them:

```bash
mount /dev/sda2 /mnt
mount /dev/sda1 /mnt/boot
```

### Step 4 — Mount pseudo-filesystems

Required for package hooks (systemd, post-install scripts) to work:

```bash
mount --bind /proc /mnt/proc
mount --bind /sys /mnt/sys
mount --bind /dev /mnt/dev
mount --bind /dev/pts /mnt/dev/pts
```

### Step 5 — Reinstall ALL packages from outside the broken system

This is the key step. Do **not** try to fix packages one by one inside `chroot` — that leads to an endless loop of missing `.so` files.

Instead, use the ISO's working `pacman` binary to operate on `/mnt` from outside:

```bash
pacman -r /mnt --cachedir /mnt/var/cache/pacman/pkg -S $(pacman -r /mnt -Qq) --overwrite '*' --noconfirm
```

**What this does:**
- `-r /mnt` — tells pacman to use `/mnt` as the root filesystem (not the ISO's root)
- `$(pacman -r /mnt -Qq)` — lists every package installed in `/mnt`'s package database
- `--overwrite '*'` — replaces any corrupted or partially written files
- Uses the ISO's own libraries, so pacman itself works fine

**If that fails** (e.g., too many packages for one command), split it:

```bash
pacman -r /mnt -Qq > /tmp/pkglist.txt
pacman -r /mnt --cachedir /mnt/var/cache/pacman/pkg -S --overwrite '*' --noconfirm - < /tmp/pkglist.txt
```

### Step 6 — Verify pacman works inside chroot

```bash
arch-chroot /mnt pacman --version
```

Expected output: `Pacman v7.x.x` (or current version)

If it still fails with a missing `.so`, install that specific library from outside:

```bash
pacstrap -K /mnt <package-name> --overwrite '*'
```

Common missing packages at this stage:
- `gcc-libs` (provides `libgcc_s.so.1`)
- `libarchive` (provides `libarchive.so.13`)
- `libseccomp` (provides `libseccomp.so.2`)
- `curl` (provides `libcurl.so.4`)

### Step 7 — Full system sync

Once pacman works inside chroot:

```bash
arch-chroot /mnt
pacman -Syu
```

Then verify no files are still corrupted:

```bash
pacman -Qk 2>&1 | grep -v "0 missing"
```

**No output = clean system.** Every package has all its files intact.

### Step 8 — Regenerate boot files

```bash
# Still inside arch-chroot /mnt:
mkinitcpio -P
grub-install /dev/sda          # adjust if using systemd-boot
grub-mkconfig -o /boot/grub/grub.cfg
```

### Step 9 — Fix user accounts (if needed)

`pacstrap` with `--overwrite '*'` can overwrite `/etc/shadow` and `/etc/passwd`, wiping user credentials.

If login fails after reboot:

```bash
# Boot ISO again, mount /mnt, arch-chroot /mnt
passwd                          # reset root password
useradd -d /home/USERNAME -G wheel -s /bin/bash USERNAME
passwd USERNAME
EDITOR=nano visudo              # uncomment: %wheel ALL=(ALL:ALL) ALL
```

Use `-d` instead of `-m` if the home directory already exists.

### Step 10 — Reboot

```bash
exit                            # leave chroot
umount -l /mnt                  # lazy unmount (handles busy targets)
reboot
```

Remove the ISO from VirtualBox boot order. Boot from hard disk.

---

## Why One-by-One Fixes Don't Work

When corruption is widespread (dozens of libraries in `/usr/lib`), fixing one package reveals the next missing dependency:

```
pacman needs libarchive → install libarchive
pacman needs libcurl → install curl
pacman needs libseccomp → install libseccomp
pacman needs libacl → install acl
... (continues indefinitely)
```

The `pacman -r /mnt -S $(pacman -r /mnt -Qq)` approach bypasses this entirely because it reinstalls **everything at once** using the ISO's working binaries.

---

## What Standard Recovery Guides Cover (and Why They Don't Apply Here)

| Standard advice | Why it doesn't work here |
|---|---|
| `sudo pacman -Syyu` | Pacman can't run — its libraries are corrupted |
| Delete `/var/lib/pacman/db.lck` | Not a lockfile issue — libraries are broken |
| `pacman -Scc` (clear cache) | Pacman can't execute at all |
| `pacman -Qk` (check packages) | Same — pacman binary can't load |
| Reinstall one package | Fixes one dependency, reveals three more |

---

## Prevention

1. **Never interrupt `pacman -Syu`.** Wait for it to finish completely.
2. **Monitor host disk space.** A VM can fail because the host ran out of room, even if the guest has free space.
3. **Take VM snapshots before major upgrades.** VirtualBox snapshots take seconds and save hours.
4. **Keep the Arch ISO attached** to the VM's virtual optical drive. When things break, you can boot it immediately without downloading.

---

## Environment

- **VM platform:** VirtualBox
- **Guest OS:** Arch Linux (rolling release)
- **Cause:** Interrupted `pacman -Syu` + host disk full during recovery
- **Recovery tool:** Arch Linux ISO (latest)
- **Time to resolve:** ~2 hours (including diagnosis)

---

## Related

- [Arch Wiki — System Recovery](https://wiki.archlinux.org/title/System_recovery)
- [Arch Wiki — Pacman/Restore local database](https://wiki.archlinux.org/title/Pacman/Restore_local_database)
- [Airia SOC Lab — Main Repository](https://github.com/StoicGang/Airia-Ai-Based-SOC-lab)
