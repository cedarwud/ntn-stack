import tensorflow as tf
import numpy as np
from sionna.rt import (
    load_scene,
    PlanarArray,
    Transmitter,
    Receiver,
    PathSolver,
    subcarrier_frequencies,
)
import matplotlib.pyplot as plt

# Configuration constants
SCENE_NAME = "NYCU.xml"
TX_ARRAY_CONFIG = dict(
    num_rows=1,
    num_cols=1,
    vertical_spacing=0.5,
    horizontal_spacing=0.5,
    pattern="iso",
    polarization="V",
)
RX_ARRAY_CONFIG = TX_ARRAY_CONFIG
TX_LIST = [
    ("tx0", [-100, -100, 20], [np.pi * 5 / 6, 0, 0], "desired", 30),
    ("tx1", [-100, 50, 20], [np.pi / 6, 0, 0], "desired", 30),
    ("tx2", [100, -100, 20], [-np.pi / 2, 0, 0], "desired", 30),
    ("jam1", [100, 50, 20], [np.pi / 2, 0, 0], "jammer", 40),
    ("jam2", [50, 50, 20], [np.pi / 2, 0, 0], "jammer", 40),
    ("jam3", [-50, -50, 20], [np.pi / 2, 0, 0], "jammer", 40),
]
RX_CONFIG = ("rx", [0, 0, 20])
PATHSOLVER_ARGS = dict(
    max_depth=10,
    los=True,
    specular_reflection=True,
    diffuse_reflection=False,
    refraction=False,
    synthetic_array=False,
    seed=41,
)
N_SUBCARRIERS = 1024
SUBCARRIER_SPACING = 30e3
num_ofdm_symbols = 1024
num_subcarriers = 1024
subcarrier_spacing = 30e3

# 1) Setup scene and antenna arrays
scene = load_scene(SCENE_NAME)
scene.tx_array = PlanarArray(**TX_ARRAY_CONFIG)
scene.rx_array = PlanarArray(**RX_ARRAY_CONFIG)

# Ensure scene is empty
assert len(scene.transmitters) == 0 and len(scene.receivers) == 0


# 2) Add transmitters
def add_tx(scene, name, pos, ori, role, power_dbm):
    tx = Transmitter(name=name, position=pos, power_dbm=power_dbm)
    tx.role = role
    scene.add(tx)
    return tx


for name, pos, ori, role, p_dbm in TX_LIST:
    add_tx(scene, name, pos, ori, role, p_dbm)

# 3) Add receiver
rx_name, rx_pos = RX_CONFIG
rx = Receiver(name=rx_name, position=rx_pos)
scene.add(rx)

# 4) Group transmitter indices by role
tx_names = scene.transmitters
all_txs = [scene.get(n) for n in tx_names]
idx_des = [i for i, tx in enumerate(all_txs) if getattr(tx, "role", None) == "desired"]
idx_jam = [i for i, tx in enumerate(all_txs) if getattr(tx, "role", None) == "jammer"]

# 5) Solve paths
solver = PathSolver()


def solve():
    return solver(scene, **PATHSOLVER_ARGS)


freqs = subcarrier_frequencies(N_SUBCARRIERS, SUBCARRIER_SPACING)
for name in scene.transmitters:
    scene.get(name).velocity = [30, 0, 0]
paths = solve()

ofdm_symbol_duration = 1 / subcarrier_spacing

# 6) Compute CFR
H_unit = paths.cfr(
    frequencies=freqs,
    sampling_frequency=1 / ofdm_symbol_duration,
    num_time_steps=num_ofdm_symbols,
    normalize_delays=True,
    normalize=False,
    out_type="numpy",
).squeeze()  # shape: (num_tx, T, F)

# 7) Compute H for desired, jammer, and all
H_all = H_unit.sum(axis=0)
H_des = H_unit[idx_des].sum(axis=0)
H_jam = H_unit[idx_jam].sum(axis=0)

# 8) Prepare mesh for plotting
T, F = H_des.shape
t_axis = np.arange(T)
f_axis = np.arange(F)
T_mesh, F_mesh = np.meshgrid(t_axis, f_axis, indexing="ij")

# 9) Create and save the 1x3 subplot figure
fig = plt.figure(figsize=(18, 5))

# Subplot 1: H_des
ax1 = fig.add_subplot(131, projection="3d")
ax1.plot_surface(F_mesh, T_mesh, np.abs(H_des), cmap="viridis", edgecolor="none")
ax1.set_xlabel("Subcarrier")
ax1.set_ylabel("OFDM symbol")
ax1.set_title("‖H_des‖")

# Subplot 2: H_jam
ax2 = fig.add_subplot(132, projection="3d")
ax2.plot_surface(F_mesh, T_mesh, np.abs(H_jam), cmap="viridis", edgecolor="none")
ax2.set_title("‖H_jam‖")

# Subplot 3: H_all
ax3 = fig.add_subplot(133, projection="3d")
ax3.plot_surface(F_mesh, T_mesh, np.abs(H_all), cmap="viridis", edgecolor="none")
ax3.set_title("‖H_all‖")

plt.tight_layout()
plt.savefig("channel_response_plots.png")
plt.close()
