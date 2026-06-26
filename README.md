# WiFi CSI Sensing Research Portfolio

This project uses Channel State Information (CSI) extracted from standard 
WiFi signals to detect human presence in a room. By analyzing how a person's 
body absorbs and reflects WiFi signals, the system can detect presence, 
movement, and eventually location — all using a normal WiFi router with no 
additional hardware. This shows how everyday WiFi infrastructure can be 
passively exploited for indoor surveillance, which is directly relevant to 
physical layer security research.

It runs on a Raspberry Pi 3B+ using Nexmon firmware to capture raw CSI data 
from the onboard WiFi chip.

## Project 1 — Presence Detection (current)
Detecting human presence using variance analysis across CSI subcarriers.
A person's body causes breathing-induced signal fluctuation at around 0.3 Hz,
which creates measurable variance on body-sensitive subcarriers (20 to 44 
out of 64 total). Currently implemented as a Python simulation — hardware 
testing on Raspberry Pi planned for July 2026.

## How to Run
python csi_detector.py
Dependencies: numpy, matplotlib

## Roadmap
- Project 1: CSI-based presence and motion detection (current)
- Project 2: Indoor localization and spatial mapping
- Project 3: Countermeasures and defense against passive WiFi sensing
