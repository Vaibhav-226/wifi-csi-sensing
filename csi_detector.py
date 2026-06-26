import numpy as np
import matplotlib.pyplot as plt

# ── PARAMETERS ──────────────────────────────────────────
# 200 frames = 2 seconds of CSI capture at 100 packets/sec
# 64 subcarriers = what Broadcom BCM43455 (Pi 3B+) exposes

num_samples = 200
num_subcarriers = 64
time = np.linspace(0, 2, num_samples)

# ── SIMULATION ──────────────────────────────────────────
# Empty room: only thermal noise, no human body present
# Mean ~0, small std because signal is stable
empty_room = np.random.normal(0, 0.05, (num_samples, num_subcarriers))

# Person present: same base noise plus breathing effect
# Breathing at ~0.3 Hz causes periodic amplitude fluctuation
person_present = np.random.normal(0, 0.05, (num_samples, num_subcarriers))

breathing_freq = 0.3
breathing_signal = np.sin(2 * np.pi * breathing_freq * time)

# Subcarrier weights: bell curve peaking at subcarrier 32
# because human body affects mid-band frequencies most
subcarrier_idx = np.arange(num_subcarriers)
weights = np.exp(-((subcarrier_idx - 32) ** 2) / (2 * 8 ** 2))
weights = weights / np.max(weights)

# Add breathing effect to person_present using outer product
# np.outer(a, b) multiplies each element of a with entire array b
breathing_amplitude = 0.2
person_present += breathing_amplitude * np.outer(breathing_signal, weights)

# ── DETECTOR FUNCTION ───────────────────────────────────
# Variance is shift-invariant — only spread matters, not mean
# Body-sensitive subcarriers are 20-44 (middle of the band)
def detect_presence(csi_data, threshold):
    variance = np.var(csi_data, axis=0)
    mean_variance = np.mean(variance[20:45])
    if mean_variance > threshold:
        return "Person detected"
    else:
        return "Empty room"

# ── MAIN ────────────────────────────────────────────────
empty_var = np.var(empty_room, axis=0)
person_var = np.var(person_present, axis=0)

empty_mean = np.mean(empty_var[20:45])
person_mean = np.mean(person_var[20:45])

# Midpoint threshold: sits between empty and person mean variances
threshold = (empty_mean + person_mean) / 2

print("Empty room mean variance:", empty_mean)
print("Person present mean variance:", person_mean)
print("Chosen threshold:", threshold)
print("Empty room result:", detect_presence(empty_room, threshold))
print("Person present result:", detect_presence(person_present, threshold))

# ── PLOT ────────────────────────────────────────────────
plt.plot(empty_var, label="Empty Room")
plt.plot(person_var, label="Person Present")
plt.xlabel("Subcarrier Index")
plt.ylabel("Variance")
plt.title("CSI Variance Across Subcarriers")
plt.legend()
plt.grid(True)
plt.show()