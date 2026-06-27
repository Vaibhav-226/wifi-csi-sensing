# Nexmon CSI Setup — Raspberry Pi 3B+

Setup guide for installing Nexmon CSI on a Raspberry Pi 3B+ to extract 
raw Channel State Information (CSI) from WiFi packets for sensing research.

**Device:** Raspberry Pi 3B+ (bcm43455c0 chip)  
**OS:** Raspberry Pi OS Lite 32-bit (latest)  
**Reference:** [nexmon_csi discussion #395](https://github.com/seemoo-lab/nexmon_csi/discussions/395)

---

## Prerequisites

> Steps 1 and 3 from the original tutorial are skipped — they apply to 
> Raspberry Pi 5 and 64-bit systems only. Pi 3B+ users follow steps below directly.

---

## Setup Steps

### 1. Update system and install dependencies

```bash
sudo apt update
sudo apt full-upgrade
sudo apt install git libgmp3-dev gawk qpdf bison flex make autoconf \
  libtool texinfo xxd libnl-3-dev libnl-genl-3-dev bc libssl-dev tcpdump
```

### 2. Install Python 2.7 (required by Nexmon build tools)

```bash
sudo cp /etc/apt/sources.list /tmp/
echo 'deb http://archive.debian.org/debian/ stretch contrib main non-free' \
  | sudo tee -a /etc/apt/sources.list
sudo apt update
sudo apt install python2.7
sudo mv /tmp/sources.list /etc/apt/
sudo apt update
```

### 3. Clone and build Nexmon

```bash
git clone --depth=1 https://github.com/seemoo-lab/nexmon.git
cd nexmon
source setup_env.sh
sed -i '1 s/$/2.7/' $NEXMON_ROOT/buildtools/b43-v3/debug/b43-beautifier
make
```

### 4. Build and install nexutil

```bash
cd $NEXMON_ROOT/utilities/nexutil
sudo -E make install USE_VENDOR_CMD=1
sudo setcap cap_net_admin+ep /usr/bin/nexutil
```

### 5. Clone nexmon_csi

```bash
cd $NEXMON_ROOT/patches/bcm43455c0/7_45_189
git clone --depth=1 https://github.com/seemoo-lab/nexmon_csi.git
cd nexmon_csi
```

### 6. Build and install patched firmware

```bash
make -f Makefile.rpi install-firmware
make -f Makefile.rpi unmanage
make -f Makefile.rpi reload-full
```

### 7. Configure CSI extraction

Generate a config string using `makecsiparams`, then:

```bash
nexutil -s500 -b -l34 -v<your-base64-config>
nexutil -m1
```

---

## Capturing CSI

```bash
sudo tcpdump -i wlan0 dst port 5500
```

CSI packets arrive as UDP on port 5500. Each packet contains amplitude 
and phase data across 64 subcarriers for one received WiFi frame.

---

## Restore Normal WiFi

```bash
make -f Makefile.rpi restore-wifi
```

---

## Troubleshooting

If no CSI packets appear:
- Confirm WiFi interface is up: `ifconfig wlan0 up`
- Kill wpa_supplicant if running: `pkill wpa_supplicant`
- Ensure there is active WiFi traffic on the monitored channel
- Check you are listening on `wlan0`, not `mon0`

---

## Credits

[Nexmon CSI](https://github.com/seemoo-lab/nexmon_csi) by SEEMOO Lab,  
TU Darmstadt — used under academic license for research purposes.
