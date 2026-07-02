# Nexmon CSI Setup — Raspberry Pi 3B+

Getting Nexmon CSI running on a Raspberry Pi 3B+ so you can pull raw Channel State Information out of WiFi packets. This is for WiFi sensing work — presence detection, that kind of thing.

**Device:** Raspberry Pi 3B+ (Broadcom `bcm43455c0` chip)
**OS:** Raspberry Pi OS Lite (Legacy, 64-bit) — Debian Bookworm
**Firmware patched:** 7.45.189
**Original reference:** [nexmon_csi discussion #395](https://github.com/seemoo-lab/nexmon_csi/discussions/395)

I went through the official tutorial and hit three separate build errors and one kernel compatibility wall that aren't mentioned anywhere in the docs. This guide has all of that folded in, so if you're starting from a blank SD card you shouldn't need to debug any of it yourself — just follow it top to bottom.

---

## Before you start: use Bookworm, not the newest image

This is worth flagging up front, since it's easy to lose a lot of time to otherwise.

Nexmon CSI needs the WiFi driver (`brcmfmac_wcc`) to support something called a vendor command interface at the kernel level. This has been verified working on kernel 6.12, which is what Bookworm currently ships. On the newest Raspberry Pi OS (Trixie, kernel 6.18 at time of writing), that support isn't wired up — and the failure mode is difficult to diagnose: the CSI configuration command just hangs indefinitely, with no error and nothing useful in the logs.

So in Raspberry Pi Imager, don't use the default OS option. Look for **"Raspberry Pi OS (Legacy, 64-bit) Lite"** in the OS list instead — that's Bookworm.

---

## 1. Flash the SD card

Grab [Raspberry Pi Imager](https://www.raspberrypi.com/software/) if you don't have it.

- Device: Raspberry Pi 3
- OS: Raspberry Pi OS (Legacy, 64-bit) Lite
- Storage: your microSD card

Click the gear icon (Edit Settings) before writing and set up:

- A hostname you'll remember (`csi-pi` or whatever)
- Username and password
- Your WiFi SSID/password, and the correct country code
- SSH enabled, password auth is fine
- Keyboard layout under Localisation — set it to match your actual keyboard (probably `us`). This only matters if you need to connect a monitor and keyboard directly to the Pi at some point; a mismatched layout can silently remap what you type, which is confusing to debug without knowing that's the cause.

Write it, pop the card in the Pi, power on. First boot takes a minute or two — be patient, it's resizing the filesystem.

## 2. SSH in

```bash
ssh pi@<hostname>.local
```

If `.local` doesn't resolve (happens more than you'd think), check your router's connected devices list for the IP instead and use `ssh pi@<ip>`.

## 3. Update and grab dependencies

```bash
sudo apt update && sudo apt full-upgrade -y
sudo reboot
```

Reconnect after it reboots, then:

```bash
sudo apt install -y git libgmp3-dev gawk qpdf bison flex make autoconf \
  libtool texinfo xxd libnl-3-dev libnl-genl-3-dev bc libssl-dev tcpdump
```

## 4. Python 2, sort of

Here's the annoying part — Nexmon's build scripts are Python 2, and no current OS ships that anymore. The "proper" fix is pulling Python 2.7 from an archived Debian repo, but that's fragile (archived repos disappear or change without warning) and honestly overkill for what we need.

Easier route: just symlink `python2.7` to point at Python 3, then patch the couple of lines in the scripts that actually break under Python 3.

```bash
sudo ln -s /usr/bin/python3 /usr/bin/python2.7
```

## 5. Clone and build Nexmon

```bash
git clone --depth=1 https://github.com/seemoo-lab/nexmon.git
cd nexmon
source setup_env.sh
sed -i '1 s/$/2.7/' $NEXMON_ROOT/buildtools/b43-v3/debug/b43-beautifier
```

Now patch the Python 2→3 syntax issues. There are two of these: old-style `print "text"` statements (needs parens now) and `except IOError, e:` (needs `as` instead of a comma). Both show up in two different files, so fix both:

```bash
sed -i '/print /{s/print \(.*\)$/print(\1)/}' $NEXMON_ROOT/buildtools/b43-v3/debug/b43-beautifier
sed -i 's/except \(\w*\), \(\w*\):/except \1 as \2:/' $NEXMON_ROOT/buildtools/b43-v3/debug/b43-beautifier
sed -i '/print /{s/print \(.*\)$/print(\1)/}' $NEXMON_ROOT/buildtools/b43-v3/debug/libb43.py
sed -i 's/except \(\w*\), \(\w*\):/except \1 as \2:/' $NEXMON_ROOT/buildtools/b43-v3/debug/libb43.py
```

Then build:

```bash
make
```

This churns through firmware extraction for a bunch of chips — not just yours — so it takes a few minutes. Should end clean. Check with `echo $?`, want to see `0`.

## 6. nexutil

```bash
cd $NEXMON_ROOT/utilities/nexutil
sudo -E make install USE_VENDOR_CMD=1
sudo setcap cap_net_admin+ep /usr/bin/nexutil
```

Sanity check:

```bash
nexutil -m
```

You should get `monitor: 0` back. That just means nexutil can talk to the driver — nothing's configured yet, which is expected.

## 7. Clone nexmon_csi (this build WILL fail the first time)

```bash
cd $NEXMON_ROOT/patches/bcm43455c0/7_45_189
git clone --depth=1 https://github.com/seemoo-lab/nexmon_csi.git
cd nexmon_csi
make -f Makefile.rpi install-firmware
```

This is expected to fail. You'll see one of these errors:

- `Label "COND_RX_IFS2" does not exist`
- `Label "SPR_RXE_FRAMELEN" does not exist`
- `Label "enable_carrier_search" does not exist`

What's actually happening: this firmware patch has some hunks that no longer apply cleanly against the base ucode (most likely a toolchain version mismatch on the upstream side), so a section of assembly code that's meant to be inserted is skipped. This first failed attempt is what generates the `.asm` file we need in order to patch it by hand — so it's an expected part of the process, not something gone wrong.

## 8. Patch the ucode by hand

Run this from inside `nexmon_csi`. It edits `src/csi.ucode.bcm43455c0.7_45_189.asm` directly — adds two missing includes and manually drops in a whole microcode routine that the automatic patch step failed to insert.

```bash
python3 << 'EOF'
path = 'src/csi.ucode.bcm43455c0.7_45_189.asm'

with open(path, 'r') as f:
    lines = f.readlines()

content = ''.join(lines)

# these two includes define the SPR_* / COND_* constants the assembler is complaining about
if 'cond.inc' not in content:
    inc1 = '#include "/home/pi/nexmon/buildtools/b43-v3/debug/include/cond.inc"\n'
    inc2 = '#include "/home/pi/nexmon/buildtools/b43-v3/debug/include/spr.inc"\n'
    content = content.replace('%start entry', inc1 + inc2 + '%start entry', 1)

with open(path, 'w') as f:
    f.write(content)

with open(path, 'r') as f:
    lines = f.readlines()

# this whole block is the rejected patch hunk (check csi.ucode.bcm43455c0.7_45_189.asm.rej
# if you're curious) — pasting it in manually since the patch tool won't apply it
insertion = """#define\tClassifierCtrl\t\t0x140
#define\tcore0_crsControlu\t0x167D
#define\tcore0_crsControll\t0x167C
#define\tcore0_crsControluSub1\t0x167F
#define\tcore0_crsControllSub1\t0x167E
#define\tcore0_computeGainInfo\t0x6D4
#define\ted_crsEn\t\t0x339
#define\tBBConfig\t\t0x1
#define\tRfseqMode\t\t0x400
enable_carrier_search:
\tphy_reg_read(ClassifierCtrl, SPARE1)
\torxh\t4, SPARE1 & ~0x0007, SPARE1
\tphy_reg_write(ClassifierCtrl, SPARE1)
\tmov\t0, SPARE1
\tmov\tNCORES, SPARE4
luppa_core:
\tmov\tcore0_crsControlu, SPARE2
\tadd\tSPARE2, SPARE1, SPARE2
\tphy_reg_read(SPARE2, SPARE3)
\torxh\t0, SPARE3 & ~0x0010, SPARE3
\tphy_reg_write(SPARE2, SPARE3)
\tmov\tcore0_crsControll, SPARE2
\tadd\tSPARE2, SPARE1, SPARE2
\tphy_reg_read(SPARE2, SPARE3)
\torxh\t0, SPARE3 & ~0x0010, SPARE3
\tphy_reg_write(SPARE2, SPARE3)
\tmov\tcore0_crsControluSub1, SPARE2
\tadd\tSPARE2, SPARE1, SPARE2
\tphy_reg_read(SPARE2, SPARE3)
\torxh\t0, SPARE3 & ~0x0010, SPARE3
\tphy_reg_write(SPARE2, SPARE3)
\tmov\tcore0_crsControllSub1, SPARE2
\tadd\tSPARE2, SPARE1, SPARE2
\tphy_reg_read(SPARE2, SPARE3)
\torxh\t0, SPARE3 & ~0x0010, SPARE3
\tphy_reg_write(SPARE2, SPARE3)
\tadd\t0x200, SPARE1, SPARE1
\tsub\tSPARE4, 1, SPARE4
\tjne\tSPARE4, 0, luppa_core-
\tmov\t0, SPARE1
\tmov\tNCORES, SPARE4
luppa_core:
\tmov\tcore0_computeGainInfo, SPARE2
\tadd\tSPARE2, SPARE1, SPARE2
\tphy_reg_read(SPARE2, SPARE3)
\torxh\t0x4000, SPARE3 & ~0x4000, SPARE3
\tphy_reg_write(SPARE2, SPARE3)
\tadd\t0x200, SPARE1, SPARE1
\tsub\tSPARE4, 1, SPARE4
\tjne\tSPARE4, 0, luppa_core-
\tphy_reg_write(ed_crsEn, 0)
\trets
disable_carrier_search:
\tphy_reg_read(ClassifierCtrl, SPARE1)
\torxh\t7, SPARE1 & ~0x0007, SPARE1
\tphy_reg_write(ClassifierCtrl, SPARE1)
\tmov\t0, SPARE1
\tmov\tNCORES, SPARE4
luppa_core:
\tmov\tcore0_crsControlu, SPARE2
\tadd\tSPARE2, SPARE1, SPARE2
\tphy_reg_read(SPARE2, SPARE3)
\torxh\t0x10, SPARE3 & ~0x0010, SPARE3
\tphy_reg_write(SPARE2, SPARE3)
\tmov\tcore0_crsControll, SPARE2
\tadd\tSPARE2, SPARE1, SPARE2
\tphy_reg_read(SPARE2, SPARE3)
\torxh\t0x10, SPARE3 & ~0x0010, SPARE3
\tphy_reg_write(SPARE2, SPARE3)
\tmov\tcore0_crsControluSub1, SPARE2
\tadd\tSPARE2, SPARE1, SPARE2
\tphy_reg_read(SPARE2, SPARE3)
\torxh\t0x10, SPARE3 & ~0x0010, SPARE3
\tphy_reg_write(SPARE2, SPARE3)
\tmov\tcore0_crsControllSub1, SPARE2
\tadd\tSPARE2, SPARE1, SPARE2
\tphy_reg_read(SPARE2, SPARE3)
\torxh\t0x10, SPARE3 & ~0x0010, SPARE3
\tphy_reg_write(SPARE2, SPARE3)
\tadd\t0x200, SPARE1, SPARE1
\tsub\tSPARE4, 1, SPARE4
\tjne\tSPARE4, 0, luppa_core-
\tmov\t0, SPARE1
\tmov\tNCORES, SPARE4
luppa_core:
\tmov\tcore0_computeGainInfo, SPARE2
\tadd\tSPARE2, SPARE1, SPARE2
\tphy_reg_read(SPARE2, SPARE3)
\torxh\t0x0, SPARE3 & ~0x4000, SPARE3
\tphy_reg_write(SPARE2, SPARE3)
\tadd\t0x200, SPARE1, SPARE1
\tsub\tSPARE4, 1, SPARE4
\tjne\tSPARE4, 0, luppa_core-
\tphy_reg_write(ed_crsEn, 0xfff)
\trets
"""

last_line = lines[-1]
new_lines = lines[:-1] + [insertion] + [last_line]

with open(path, 'w') as f:
    f.writelines(new_lines)

print("done")
EOF
```

Quick check that it actually landed — each of these should print `1`:

```bash
grep -c "cond.inc" src/csi.ucode.bcm43455c0.7_45_189.asm
grep -c "spr.inc" src/csi.ucode.bcm43455c0.7_45_189.asm
grep -c "enable_carrier_search:" src/csi.ucode.bcm43455c0.7_45_189.asm
```

## 9. Build again — should work now

```bash
make -f Makefile.rpi install-firmware
```

This time it should complete without errors, ending with the firmware being installed via `update-alternatives`. If it doesn't, it's worth confirming the fixes from the previous step actually applied before troubleshooting further.

## 10. Hand wlan0 over to Nexmon

```bash
sudo nmcli dev disconnect wlan0
sudo nmcli dev set wlan0 managed no
sudo modprobe -r brcmfmac_wcc
sudo modprobe brcmfmac_wcc
sleep 2
sudo ifconfig wlan0 up
sudo iw dev wlan0 set power_save off
```

A note on why this is broken into individual commands rather than just running `make -f Makefile.rpi unmanage && make -f Makefile.rpi reload-full` (the approach in the official docs): if you're managing the Pi over a second WiFi interface — a USB adapter, for instance — for SSH, the official `unmanage` target can end up disabling WiFi system-wide and cutting off your only way in. Scoping these commands to `wlan0` specifically avoids that. If you only have the one onboard WiFi interface, the official one-liners are simpler, but expect to lose WiFi access afterward and need Ethernet or a monitor to get back in.

## 11. Generate a CSI config

Build the little helper tool first:

```bash
cd $NEXMON_ROOT/patches/bcm43455c0/7_45_189/nexmon_csi/utils/makecsiparams
make
```

Figure out what channel your target network is on:

```bash
iw dev wlan0 info
```

Then generate the config string — swap in the channel and the BSSID (MAC address) of whatever network you want `wlan0` listening to:

```bash
./makecsiparams -c <channel>/20 -C 1 -N 1 -m <target_network_BSSID>
```

You'll get a base64-looking string back. That's your config.

## 12. Apply it and flip on monitor mode

```bash
nexutil -Iwlan0 -s500 -b -l34 -v<config-string-from-above>
nexutil -Iwlan0 -m1
nexutil -Iwlan0 -m
```

Should say `monitor: 1` at the end. If this hangs instead of returning instantly — see the troubleshooting section below, it's almost certainly the kernel issue.

## 13. Capture CSI data

```bash
sudo tcpdump -i wlan0 -w capture.pcap
```

One thing worth knowing — CSI frames don't look like normal UDP traffic, so filtering with something like `dst port 5500` mostly won't catch anything, since tcpdump's filter can't parse the non-standard frame structure. It's more reliable to capture everything on `wlan0` and do the filtering/parsing downstream in your own analysis code.

Also make sure something is actually generating traffic on the network you're monitoring while this runs — an idle network produces no frames to extract CSI from, and you'll end up with an empty capture.

Each packet captured holds amplitude and phase data across the subcarriers of whatever WiFi frame it overheard.

## 14. Restore normal WiFi (optional)

```bash
make -f Makefile.rpi restore-wifi
```

---

## Troubleshooting

**`nexutil -s500 ...` just hangs, no error, nothing** — this is the kernel thing. Run `uname -r` and check. Anything past 6.12ish (Trixie ships 6.18 currently) doesn't have the vendor command hook wired up, so the command sits there forever waiting for a reply that's never coming. Only real fix is reflashing with Bookworm as described up top.

**No CSI packets showing up in your capture** — a few things to check in order: is `wlan0` actually up (`ifconfig wlan0 up`)? Does the channel you set in `makecsiparams` actually match the network you're listening to? Is there real traffic happening on that network right now? Also worth running `ip -s link show wlan0` — the RX counter should keep climbing even if the interface status looks weird (mine showed `NO-CARRIER` the whole time and it was still capturing fine, so don't read too much into that flag).

**Python syntax errors about `print` or exception handling** — means step 5's fixes either didn't apply, or a different file entirely has the same old-style syntax. Read the traceback, it'll tell you which file, then apply the same sed commands to that one.

---

## Credit

Built on [Nexmon CSI](https://github.com/seemoo-lab/nexmon_csi), SEEMOO Lab, TU Darmstadt. Used here for academic/research purposes.
