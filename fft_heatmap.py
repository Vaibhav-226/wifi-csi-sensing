import numpy as np
import matplotlib.pyplot as plt

# -------------------------------------------------------
# PARAMETERS
# -------------------------------------------------------

num_samples = 1000          # 10 seconds @100 Hz
num_subcarriers = 64
sampling_rate = 100         # packets/sec

time = np.linspace(0, 10, num_samples)

# -------------------------------------------------------
# SIMULATE CSI
# -------------------------------------------------------

person_present = np.random.normal(
    0,
    0.05,
    (num_samples, num_subcarriers)
)

breathing_freq = 0.3

breathing_signal = np.sin(
    2 * np.pi * breathing_freq * time
)

subcarrier_idx = np.arange(num_subcarriers)

weights = np.exp(
    -((subcarrier_idx - 32) ** 2) /
    (2 * 8 ** 2)
)

weights = weights / np.max(weights)

breathing_amplitude = 0.2

person_present += (
    breathing_amplitude *
    np.outer(breathing_signal, weights)
)

# -------------------------------------------------------
# FFT OF EVERY SUBCARRIER
# -------------------------------------------------------

num_positive = num_samples // 2

fft_heatmap = np.zeros((num_subcarriers, num_positive))

for sc in range(num_subcarriers):

    # Extract one subcarrier
    signal = person_present[:, sc]

    # Remove DC component
    signal = signal - np.mean(signal)

    # FFT
    fft_result = np.fft.fft(signal)

    # Magnitude
    magnitude = np.abs(fft_result)

    # Positive frequencies only
    fft_heatmap[sc] = magnitude[:num_positive]

# -------------------------------------------------------
# FREQUENCY AXIS
# -------------------------------------------------------

frequencies = np.fft.fftfreq(
    num_samples,
    d=1 / sampling_rate
)

positive_freq = frequencies[:num_positive]

# -------------------------------------------------------
# PLOT HEATMAP
# -------------------------------------------------------

plt.figure(figsize=(12, 6))

plt.imshow(
    fft_heatmap,
    aspect='auto',
    origin='lower',
    extent=[
        positive_freq[0],
        positive_freq[-1],
        0,
        num_subcarriers - 1
    ]
)

plt.colorbar(label="FFT Magnitude")

plt.xlabel("Frequency (Hz)")
plt.ylabel("Subcarrier")
plt.title("FFT Magnitude Heatmap Across All Subcarriers")
plt.xlim(0, 5)
plt.show()