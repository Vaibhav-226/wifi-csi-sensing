import struct
import numpy as np

# ==========================================================
# CREATE A FAKE NEXMON CSI PACKET
# ==========================================================

# Fake 20-byte header (contents don't matter for this exercise)
header = bytes(20)

# Generate 128 fake int16 CSI values
# (64 real + 64 imaginary values interleaved)
fake_values = np.random.randint(
    -1000,
    1000,
    size=128,
    dtype=np.int16
)

# Pack the int16 values into 256 bytes
csi_bytes = struct.pack(
    '128h',
    *fake_values
)

# Combine header and CSI data
raw_packet = header + csi_bytes

print("Total packet size:", len(raw_packet), "bytes")

# ==========================================================
# PARSE THE PACKET
# ==========================================================

# Skip the 20-byte header
csi_data = raw_packet[20:]

print("CSI data size:", len(csi_data), "bytes")

# ==========================================================
# UNPACK CSI DATA
# ==========================================================

values = struct.unpack(
    '128h',
    csi_data
)

# ==========================================================
# SEPARATE REAL AND IMAGINARY PARTS
# ==========================================================

real = values[0::2]
imag = values[1::2]

# ==========================================================
# COMPUTE AMPLITUDE
# ==========================================================

amplitude = np.sqrt(
    np.array(real) ** 2 +
    np.array(imag) ** 2
)

# ==========================================================
# PRINT RESULTS
# ==========================================================

print("\nReal Values:")
print(real)

print("\nImaginary Values:")
print(imag)

print("\nAmplitude (64 Subcarriers):")
print(amplitude)