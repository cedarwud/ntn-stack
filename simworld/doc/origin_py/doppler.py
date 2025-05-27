"""
Full-band CFR demo – Python 3.11 · TF 2.19 · Sionna 1.0.2
Saves two delay-Doppler plots as PNG files: unscaled and power-scaled channels.
"""

# --------------------------------------------------------------------#
# 0) Imports & GPU housekeeping
# --------------------------------------------------------------------#
import os
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf

from sionna.rt import (
    load_scene,
    PlanarArray,
    Transmitter,
    Receiver,
    PathSolver,
    subcarrier_frequencies,
)

# --------------------------------------------------------------------#
# 1) Parameters
# --------------------------------------------------------------------#
# Scene and antenna configuration
SCENE_NAME = "NYCU.xml"  # Consider using sionna.rt.scene.etoile for testing
TX_ARRAY_CONFIG = dict(
    num_rows=1,
    num_cols=1,
    vertical_spacing=0.5,
    horizontal_spacing=0.5,
    pattern="iso",
    polarization="V",
)
RX_ARRAY_CONFIG = TX_ARRAY_CONFIG

# Transmitters: (name, position, orientation, role, power_dbm)
TX_LIST = [
    ("tx0", [-100, -100, 20], [np.pi * 5 / 6, 0, 0], "desired", 30),
    ("tx1", [-100, 50, 20], [np.pi / 6, 0, 0], "desired", 30),
    ("tx2", [100, -100, 20], [-np.pi / 2, 0, 0], "desired", 30),
    ("jam1", [100, 50, 20], [np.pi / 2, 0, 0], "jammer", 40),
    ("jam2", [50, 50, 20], [np.pi / 2, 0, 0], "jammer", 40),
    ("jam3", [-50, -50, 20], [np.pi / 2, 0, 0], "jammer", 40),
]

RX_CONFIG = ("rx", [0, 0, 20])  # (name, position)

# PathSolver parameters
PATHSOLVER_ARGS = dict(
    max_depth=5,
    max_num_paths_per_src=1000,
    los=True,
    specular_reflection=True,
    diffuse_reflection=False,
    refraction=False,
    synthetic_array=False,
    seed=41,
)

# OFDM parameters
N_SUBCARRIERS = 512
SUBCARRIER_SPACING = 30e3  # Hz
NUM_OFDM_SYMBOLS = 512

# Output file paths for plots
PLOT_UNSCALED = "unscaled_delay_doppler.png"
PLOT_POWER_SCALED = "power_scaled_delay_doppler.png"

# --------------------------------------------------------------------#
# 2) Scene Setup and CFR Computation
# --------------------------------------------------------------------#
# Create scene and configure antennas
scene = load_scene(SCENE_NAME)
scene.tx_array = PlanarArray(**TX_ARRAY_CONFIG)
scene.rx_array = PlanarArray(**RX_ARRAY_CONFIG)

# Clear existing transmitters and receivers
for tx_name in list(scene.transmitters):
    scene.remove(tx_name)
for rx_name in list(scene.receivers):
    scene.remove(rx_name)


# Add transmitters
def add_tx(scene, name, pos, ori, role, power_dbm):
    tx = Transmitter(name=name, position=pos, orientation=ori, power_dbm=power_dbm)
    tx.role = role
    scene.add(tx)


for name, pos, ori, role, p_dbm in TX_LIST:
    add_tx(scene, name, pos, ori, role, p_dbm)

# Add receiver
rx_name, rx_pos = RX_CONFIG
scene.add(Receiver(name=rx_name, position=rx_pos))

# Assign velocities to transmitters
for name, tx in scene.transmitters.items():
    tx.velocity = [30, 0, 0]

# Group transmitters by role
all_txs = [scene.get(n) for n in scene.transmitters]
idx_des = [i for i, tx in enumerate(all_txs) if tx.role == "desired"]
idx_jam = [i for i, tx in enumerate(all_txs) if tx.role == "jammer"]

# Compute CFR with error handling
solver = PathSolver()
try:
    paths = solver(scene, **PATHSOLVER_ARGS)
except RuntimeError as e:
    print(f"Error in PathSolver: {e}")
    print("Try reducing max_depth, max_num_paths_per_src, or using a simpler scene.")
    raise

freqs = subcarrier_frequencies(N_SUBCARRIERS, SUBCARRIER_SPACING)
ofdm_symbol_duration = 1 / SUBCARRIER_SPACING

H_unit = paths.cfr(
    frequencies=freqs,
    sampling_frequency=1 / ofdm_symbol_duration,
    num_time_steps=NUM_OFDM_SYMBOLS,
    normalize_delays=True,
    normalize=False,
    out_type="numpy",
)

# Debug shape
print(f"H_unit shape before squeeze: {H_unit.shape}")
H_unit = H_unit.squeeze()  # Should be (num_tx, T, F)
print(f"H_unit shape after squeeze: {H_unit.shape}")
assert H_unit.shape == (
    len(all_txs),
    NUM_OFDM_SYMBOLS,
    N_SUBCARRIERS,
), f"Expected H_unit shape ({len(all_txs)}, {NUM_OFDM_SYMBOLS}, {N_SUBCARRIERS}), got {H_unit.shape}"

# Compute linear powers
tx_p_lin = (
    10 ** (np.array([tx.power_dbm for tx in all_txs]) / 10) / 1e3
)  # (num_tx,) = (6,)
sqrtP = np.sqrt(tx_p_lin).reshape(-1, 1, 1)  # (num_tx, 1, 1) = (6, 1, 1)
H_pw = H_unit * sqrtP  # Broadcasting: (6, 512, 512) * (6, 1, 1) -> (6, 512, 512)
print(f"H_pw shape: {H_pw.shape}")
assert H_pw.shape == (
    len(all_txs),
    NUM_OFDM_SYMBOLS,
    N_SUBCARRIERS,
), f"Expected H_pw shape ({len(all_txs)}, {NUM_OFDM_SYMBOLS}, {N_SUBCARRIERS}), got {H_pw.shape}"

# Sum by role for power-scaled channels
H_des = H_pw[idx_des].sum(axis=0)  # (3, 512, 512) -> (512, 512)
H_jam = H_pw[idx_jam].sum(axis=0)  # (3, 512, 512) -> (512, 512)
H_all = H_des + H_jam
print(f"H_des shape (power-scaled): {H_des.shape}")
assert H_des.shape == (
    NUM_OFDM_SYMBOLS,
    N_SUBCARRIERS,
), f"Expected H_des shape ({NUM_OFDM_SYMBOLS}, {N_SUBCARRIERS}), got {H_des.shape}"

# Sum by role for unscaled channels (for first plot)
H_des_unscaled = H_unit[idx_des].sum(axis=0)  # (3, 512, 512) -> (512, 512)
H_jam_unscaled = H_unit[idx_jam].sum(axis=0)  # (3, 512, 512) -> (512, 512)
H_all_unscaled = H_des_unscaled + H_jam_unscaled
print(f"H_des_unscaled shape: {H_des_unscaled.shape}")
assert H_des_unscaled.shape == (
    NUM_OFDM_SYMBOLS,
    N_SUBCARRIERS,
), f"Expected H_des_unscaled shape ({NUM_OFDM_SYMBOLS}, {N_SUBCARRIERS}), got {H_des_unscaled.shape}"


# --------------------------------------------------------------------#
# 3) Delay-Doppler Transformation and Plotting
# --------------------------------------------------------------------#
def to_delay_doppler(H_tf):
    print(f"Input H_tf shape: {H_tf.shape}")
    assert H_tf.shape == (
        NUM_OFDM_SYMBOLS,
        N_SUBCARRIERS,
    ), f"Expected H_tf shape ({NUM_OFDM_SYMBOLS}, {N_SUBCARRIERS}), got {H_tf.shape}"
    Hf = np.fft.fftshift(H_tf, axes=-1)  # Frequency shift on last axis
    h_delay = np.fft.ifft(Hf, axis=-1, norm="ortho")  # Frequency to delay
    h_dd = np.fft.fft(h_delay, axis=-2, norm="ortho")  # Time to Doppler
    h_dd = np.fft.fftshift(h_dd, axes=-2)  # Doppler shift
    print(f"Output h_dd shape: {h_dd.shape}")
    return h_dd


# Compute delay-Doppler for unscaled channels (first plot)
Hdd_des_unscaled = to_delay_doppler(H_des_unscaled)
Hdd_jam_unscaled = to_delay_doppler(H_jam_unscaled)
Hdd_all_unscaled = to_delay_doppler(H_all_unscaled)
print(f"Hdd_des_unscaled shape: {Hdd_des_unscaled.shape}")

# Compute delay-Doppler for power-scaled channels (second plot)
Hdd_des = to_delay_doppler(H_des)
Hdd_jam = to_delay_doppler(H_jam)
Hdd_all = to_delay_doppler(H_all)
print(f"Hdd_des shape (power-scaled): {Hdd_des.shape}")

# Define plotting range
T, F = Hdd_des.shape  # Should be (512, 512)
offset = 20
d_start, d_end = 0, offset * 2  # Delay: first 40 bins
t_mid = T // 2  # Doppler: center at 0 Hz
t_start, t_end = t_mid - offset, t_mid + offset  # Doppler: ±20 bins

# Coordinate axes
delay_bins = np.arange(F) * ((1 / SUBCARRIER_SPACING) / F) * 1e9  # ns
doppler_bins = np.fft.fftshift(np.fft.fftfreq(T, d=1 / SUBCARRIER_SPACING))  # Hz
X, Y = np.meshgrid(delay_bins[d_start:d_end], doppler_bins[t_start:t_end])

# --- First Plot: Unscaled Channels ---
fig1 = plt.figure(figsize=(18, 5))
fig1.suptitle("Delay-Doppler Plots (Unscaled Channels)")

ax1 = fig1.add_subplot(131, projection="3d")
Z_des_unscaled = np.abs(Hdd_des_unscaled[t_start:t_end, d_start:d_end])
ax1.plot_surface(X, Y, Z_des_unscaled, cmap="viridis", edgecolor="none")
ax1.set(title="Delay–Doppler |Desired|", xlabel="Delay (ns)", ylabel="Doppler (Hz)")

ax2 = fig1.add_subplot(132, projection="3d")
Z_jam_unscaled = np.abs(Hdd_jam_unscaled[t_start:t_end, d_start:d_end])
ax2.plot_surface(X, Y, Z_jam_unscaled, cmap="viridis", edgecolor="none")
ax2.set(title="Delay–Doppler |Jammer|", xlabel="Delay (ns)", ylabel="Doppler (Hz)")

ax3 = fig1.add_subplot(133, projection="3d")
Z_all_unscaled = np.abs(Hdd_all_unscaled[t_start:t_end, d_start:d_end])
ax3.plot_surface(X, Y, Z_all_unscaled, cmap="viridis", edgecolor="none")
ax3.set(title="Delay–Doppler |All|", xlabel="Delay (ns)", ylabel="Doppler (Hz)")

plt.tight_layout()
plt.savefig(PLOT_UNSCALED, dpi=300, bbox_inches="tight")
print(f"Saved unscaled plot to {PLOT_UNSCALED}")
plt.close(fig1)  # Close figure to free memory

# --- Second Plot: Power-Scaled Channels ---
fig2 = plt.figure(figsize=(18, 5))
fig2.suptitle("Delay-Doppler Plots (Power-Scaled Channels)")

ax1 = fig2.add_subplot(131, projection="3d")
Z_des = np.abs(Hdd_des[t_start:t_end, d_start:d_end])
ax1.plot_surface(X, Y, Z_des, cmap="viridis", edgecolor="none")
ax1.set(title="Delay–Doppler |Desired|", xlabel="Delay (ns)", ylabel="Doppler (Hz)")

ax2 = fig2.add_subplot(132, projection="3d")
Z_jam = np.abs(Hdd_jam[t_start:t_end, d_start:d_end])
ax2.plot_surface(X, Y, Z_jam, cmap="viridis", edgecolor="none")
ax2.set(title="Delay–Doppler |Jammer|", xlabel="Delay (ns)", ylabel="Doppler (Hz)")

ax3 = fig2.add_subplot(133, projection="3d")
Z_all = np.abs(Hdd_all[t_start:t_end, d_start:d_end])
ax3.plot_surface(X, Y, Z_all, cmap="viridis", edgecolor="none")
ax3.set(title="Delay–Doppler |All|", xlabel="Delay (ns)", ylabel="Doppler (Hz)")

plt.tight_layout()
plt.savefig(PLOT_POWER_SCALED, dpi=300, bbox_inches="tight")
print(f"Saved power-scaled plot to {PLOT_POWER_SCALED}")
plt.close(fig2)  # Close figure to free memory

# Optional: Display plots (comment out if running non-interactively)
plt.show()
