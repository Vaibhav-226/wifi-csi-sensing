import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

# -------------------------------------------------------
# PARAMETERS
# -------------------------------------------------------

num_samples = 1000          # 10 seconds @100 Hz
num_subcarriers = 64
sampling_rate = 100

time = np.linspace(0, 10, num_samples)

# -------------------------------------------------------
# SIMULATE EMPTY ROOM
# -------------------------------------------------------

empty_room = np.random.normal(
    0,
    0.05,
    (num_samples, num_subcarriers)
)

# -------------------------------------------------------
# SIMULATE PERSON PRESENT
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

# Bell-shaped weighting across subcarriers
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
# COMBINE BOTH DATASETS
# -------------------------------------------------------

combined_data = np.vstack(
    (empty_room, person_present)
)

# -------------------------------------------------------
# PCA
# -------------------------------------------------------

pca = PCA(n_components=2)

# Learn principal components from the combined dataset
pca.fit(combined_data)

# Transform each dataset into the same PCA space
empty_pca = pca.transform(empty_room)
person_pca = pca.transform(person_present)

# -------------------------------------------------------
# PLOT
# -------------------------------------------------------

plt.figure(figsize=(8, 6))

plt.scatter(
    empty_pca[:, 0],
    empty_pca[:, 1],
    alpha=0.6,
    label="Empty Room"
)

plt.scatter(
    person_pca[:, 0],
    person_pca[:, 1],
    alpha=0.6,
    label="Person Present"
)
print("Explained variance ratio:", pca.explained_variance_ratio_)
print("Cumulative variance with 10 components:")
pca_full = PCA(n_components=10)
pca_full.fit(combined_data)
print(np.cumsum(pca_full.explained_variance_ratio_))
plt.xlabel("Principal Component 1")
plt.ylabel("Principal Component 2")
plt.title("PCA Analysis of Simulated CSI Data")

plt.legend()
plt.grid(True)

plt.show()