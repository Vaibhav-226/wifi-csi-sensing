# Nexmon CSI Setup (Raspberry Pi 3B+)

## Device Information

- **Device:** Raspberry Pi 3B+
- **Wi-Fi Chip:** bcm43455c0
- **OS:** Raspberry Pi OS Lite (32-bit, latest)

### Notes

- **Skip Step 1** — Raspberry Pi 5 only (16 KB page-size kernel issue)
- **Skip Step 3** — 64-bit (AArch64) systems only
- **Actual setup steps:** 2 → 4 → 5 → 6 → 7 → 8 → 9

---

# Step 1 — Switch to the 4 KB page-size kernel

**Status:** ❌ SKIP — Raspberry Pi 5 only

**Reason:**

- Raspberry Pi 3B+ does not use the 16 KB page-size kernel.
- This workaround is only needed on Raspberry Pi 5.

Commands (for reference only):

```bash
sudo echo 'kernel=kernel8.img' >> /boot/firmware/config.txt
```

**What I think this does:**

- Adds a line to the Raspberry Pi boot configuration.
- Tells the Pi to boot using `kernel8.img`.
- Required only because Nexmon cannot build with the newer 16 KB page-size kernel.

```bash
sudo reboot
```

**What I think this does:**

- Restarts the Raspberry Pi so the new kernel setting takes effect.

---

# Step 2 — Update system and install dependencies

```bash
sudo apt update
```

**What I think this does:**

- Refreshes the package list from the Debian repositories.

```bash
sudo apt full-upgrade
```

**What I think this does:**

- Updates all installed packages to their latest compatible versions.

```bash
sudo apt install git libgmp3-dev gawk qpdf bison flex make autoconf libtool texinfo xxd libnl-3-dev libnl-genl-3-dev bc libssl-dev tcpdump
```

**What I think this does:**

- Installs all tools and libraries needed to build Nexmon and capture CSI packets.
- Includes compiler tools, networking libraries, OpenSSL development headers, and `tcpdump`.

---

# Step 3 — Install 32-bit compatibility libraries

**Status:** ❌ SKIP — 64-bit (AArch64) systems only

**Reason:**

- Raspberry Pi 3B+ running the 32-bit Raspberry Pi OS does not require these compatibility libraries.

Commands (for reference only):

```bash
sudo dpkg --add-architecture armhf
```

**What I think this does:**

- Enables installing 32-bit ARM packages on a 64-bit Raspberry Pi OS.

```bash
sudo apt update
```

**What I think this does:**

- Refreshes package lists after enabling the new architecture.

```bash
sudo apt-get install libc6:armhf libisl23:armhf libmpfr6:armhf libmpc3:armhf libstdc++6:armhf
```

**What I think this does:**

- Installs required 32-bit runtime libraries used by Nexmon's build tools.

```bash
sudo ln -s /usr/lib/arm-linux-gnueabihf/libisl.so.23 /usr/lib/arm-linux-gnueabihf/libisl.so.10
```

**What I think this does:**

- Creates a symbolic link so software expecting an older library version can use the newer one.

```bash
sudo ln -s /usr/lib/arm-linux-gnueabihf/libmpfr.so.6 /usr/lib/arm-linux-gnueabihf/libmpfr.so.4
```

**What I think this does:**

- Creates another compatibility symbolic link for MPFR.

---

# Step 4 — Install Python 2.7

```bash
sudo cp /etc/apt/sources.list /tmp/
```

**What I think this does:**

- Creates a backup of the current package repository configuration.

```bash
echo 'deb http://archive.debian.org/debian/ stretch contrib main non-free' | sudo tee -a /etc/apt/sources.list
```

**What I think this does:**

- Temporarily adds the Debian Stretch repository because Python 2.7 is no longer available in modern repositories.

```bash
sudo apt update
```

**What I think this does:**

- Refreshes the package lists to include the newly added repository.

```bash
sudo apt install python2.7
```

**What I think this does:**

- Installs Python 2.7, which is required by the older `bcm43` tool used by Nexmon.

```bash
sudo mv /tmp/sources.list /etc/apt/
```

**What I think this does:**

- Restores the original package repository configuration.

```bash
sudo apt update
```

**What I think this does:**

- Refreshes package lists after removing the temporary repository.

---

# Step 5 — Download and build Nexmon

```bash
git clone --depth=1 https://github.com/seemoo-lab/nexmon.git
```

**What I think this does:**

- Downloads the Nexmon source code from GitHub.
- `--depth=1` downloads only the latest commit, making the clone faster.

```bash
cd nexmon
```

**What I think this does:**

- Moves into the Nexmon project directory.

```bash
source setup_env.sh
```

**What I think this does:**

- Sets environment variables required for building Nexmon.

```bash
sed -i '1 s/$/2.7/' $NEXMON_ROOT/buildtools/b43-v3/debug/b43-beautifier
```

**What I think this does:**

- Modifies the script so it explicitly runs using Python 2.7.

```bash
make
```

**What I think this does:**

- Compiles the Nexmon build tools.

---

# Step 6 — Build and install nexutil

```bash
cd $NEXMON_ROOT/utilities/nexutil
```

**What I think this does:**

- Moves into the `nexutil` utility directory.

```bash
sudo -E make install USE_VENDOR_CMD=1
```

**What I think this does:**

- Compiles and installs `nexutil`.
- `-E` preserves environment variables.
- `USE_VENDOR_CMD=1` enables vendor commands needed by the Raspberry Pi Wi-Fi driver.

```bash
sudo setcap cap_net_admin+ep /usr/bin/nexutil
```

**What I think this does:**

- Gives `nexutil` permission to perform network administration tasks without needing to run it as root every time.

---

# Step 7 — Download Nexmon CSI

```bash
cd $NEXMON_ROOT/patches/bcm43455c0/7_45_189
```

**What I think this does:**

- Moves into the firmware patch directory for the BCM43455C0 Wi-Fi chip.

```bash
git clone --depth=1 https://github.com/seemoo-lab/nexmon_csi.git
```

**What I think this does:**

- Downloads the Nexmon CSI project.

```bash
cd nexmon_csi
```

**What I think this does:**

- Moves into the Nexmon CSI project directory.

---

# Step 8 — Build and install the patched firmware

```bash
make -f Makefile.rpi install-firmware
```

**What I think this does:**

- Builds and installs the modified firmware that supports CSI extraction.

```bash
make -f Makefile.rpi unmanage
```

**What I think this does:**

- Stops NetworkManager from controlling the Wi-Fi interface.

```bash
make -f Makefile.rpi reload-full
```

**What I think this does:**

- Reloads the Wi-Fi driver so the newly installed firmware becomes active.

---

# Step 9 — Configure CSI extraction

```bash
nexutil -s500 -b -l34 -v<your-config-generated-with-makecsiparams>
```

**What I think this does:**

- Sends CSI configuration parameters to the firmware.
- Enables CSI extraction using the specified configuration.

```bash
nexutil -m1
```

**What I think this does:**

- Switches the Wi-Fi interface into monitor mode so CSI packets can be captured.

---

# Capture CSI Packets

```bash
sudo tcpdump -i wlan0 dst port 5500
```

**What I think this does:**

- Listens on the `wlan0` interface.
- Displays UDP packets sent to destination port 5500, where Nexmon CSI transmits CSI data.

---

# Restore Normal Wi-Fi

```bash
make -f Makefile.rpi restore-wifi
```

**What I think this does:**

- Restores the original firmware.
- Returns the Wi-Fi interface to normal managed mode.
- Disables CSI extraction.

---

# Summary

## My actual setup on Raspberry Pi 3B+

| Step   | Status                |
| ------ | --------------------- |
| Step 1 | ❌ Skip (Pi 5 only)   |
| Step 2 | ✅ Do                 |
| Step 3 | ❌ Skip (64-bit only) |
| Step 4 | ✅ Do                 |
| Step 5 | ✅ Do                 |
| Step 6 | ✅ Do                 |
| Step 7 | ✅ Do                 |
| Step 8 | ✅ Do                 |
| Step 9 | ✅ Do                 |

**Execution order:**

1. Step 2 — Update system and install dependencies
2. Step 4 — Install Python 2.7
3. Step 5 — Build Nexmon
4. Step 6 — Install `nexutil`
5. Step 7 — Clone `nexmon_csi`
6. Step 8 — Install patched firmware
7. Step 9 — Configure CSI extraction and enable monitor mode

This is the complete setup procedure for my Raspberry Pi 3B+ running Raspberry Pi OS Lite (32-bit).
