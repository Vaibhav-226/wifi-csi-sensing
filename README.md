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

## Project 1 — Presence Detection (in progress)

Simulation and signal processing pipeline complete. Implemented:
- Variance-based presence detection across 64 CSI subcarriers
- FFT-based breathing frequency detection (0.3 Hz peak identified)
- Multi-subcarrier FFT heatmap showing spatial selectivity of breathing signature
- PCA dimensionality reduction (PC1 captures 47% of variance, separates empty room vs person present)

Hardware implementation on Raspberry Pi 3B+ with Nexmon firmware arriving July 4.

## How to Run

python csi_detector.py

Dependencies: numpy, matplotlib, scikit-learn

## Roadmap
- Project 1: CSI-based presence and motion detection (current)
- Project 2: Indoor localization and spatial mapping
- Project 3: Countermeasures and defense against passive WiFi sensing
