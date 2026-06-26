import numpy as np
import matplotlib.pyplot as plt

# -------------------------------------------------------
# PARAMETERS
# -------------------------------------------------------

num_samples = 1000         # 2 seconds of data
num_subcarriers = 64
sampling_rate = 100        # 100 packets/sec

time = np.linspace(0, 10, num_samples)

# -------------------------------------------------------
# SIMULATE CSI DATA
# -------------------------------------------------------

# Base CSI noise
person_present = np.random.normal(
    0,
    0.05,
    (num_samples, num_subcarriers)
)

# Breathing signal
breathing_freq = 0.3       # Hz
breathing_signal = np.sin(
    2 * np.pi * breathing_freq * time
)

# Bell-shaped weighting across subcarriers
subcarrier_idx = np.arange(num_subcarriers)

weights = np.exp(
    -((subcarrier_idx - 32) ** 2) / (2 * 8 ** 2)
)

weights = weights / np.max(weights)

# Add breathing effect
breathing_amplitude = 0.2

person_present += (
    breathing_amplitude *
    np.outer(breathing_signal, weights)
)

# -------------------------------------------------------
# FFT ANALYSIS
# -------------------------------------------------------

# Extract CSI signal from subcarrier 32
signal = person_present[:, 32]

# Remove DC component (mean value)
signal = signal - np.mean(signal)

# Compute FFT
fft_result = np.fft.fft(signal)

# Magnitude spectrum
fft_magnitude = np.abs(fft_result)

# Frequency axis
frequencies = np.fft.fftfreq(
    len(signal),
    d=1/sampling_rate
)

# Keep only positive frequencies
positive = frequencies >= 0

# -------------------------------------------------------
# FIND DOMINANT FREQUENCY
# -------------------------------------------------------

peak_index = np.argmax(fft_magnitude[positive])

peak_frequency = frequencies[positive][peak_index]

print(f"Detected peak frequency: {peak_frequency:.2f} Hz")

# -------------------------------------------------------
# PLOT
# -------------------------------------------------------

plt.figure(figsize=(10,5))

plt.plot(
    frequencies[positive],
    fft_magnitude[positive]
)

plt.xlabel("Frequency (Hz)")
plt.ylabel("Magnitude")
plt.title("FFT of CSI Signal (Subcarrier 32)")
plt.grid(True)
plt.xlim(0, 5)
plt.show()