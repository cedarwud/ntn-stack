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
    RadioMapSolver,
)

# 載入場景並列印物件材質
scene = load_scene("NYCU.xml")
for name, obj in scene.objects.items():
    print(f"{name:<15}{obj.radio_material.name}")

# 參數設定
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
    ("tx0", [-100, -100, 40], [np.pi * 5 / 6, 0, 0], "desired", 30),
    ("tx1", [-100, 50, 40], [np.pi / 6, 0, 0], "desired", 30),
    ("tx2", [100, -100, 40], [-np.pi / 2, 0, 0], "desired", 30),
    ("jam1", [100, 50, 40], [np.pi / 2, 0, 0], "jammer", 40),
    ("jam2", [50, 50, 40], [np.pi / 2, 0, 0], "jammer", 40),
    ("jam3", [-50, -50, 40], [np.pi / 2, 0, 0], "jammer", 40),
    ("jam4", [-100, 0, 40], [np.pi / 2, 0, 0], "jammer", 40),
    ("jam5", [0, -100, 40], [np.pi / 2, 0, 0], "jammer", 40),
    ("jam6", [-100, -50, 40], [np.pi / 2, 0, 0], "jammer", 40),
]

RX_CONFIG = ("rx", [0, 0, 40])

PATHSOLVER_ARGS = dict(
    max_depth=3,
    los=True,
    specular_reflection=True,
    diffuse_reflection=False,
    refraction=False,
    synthetic_array=False,
    seed=41,
)

RMSOLVER_ARGS = dict(max_depth=10, cell_size=(1.0, 1.0), samples_per_tx=10**7)

N_SYMBOLS = 1
N_SUBCARRIERS = 1024
SUBCARRIER_SPACING = 30e3
num_ofdm_symbols = 1024
num_subcarriers = 1024
subcarrier_spacing = 30e3

# 建立場景與天線配置
scene = load_scene("GIS.xml")
scene.tx_array = PlanarArray(**TX_ARRAY_CONFIG)
scene.rx_array = PlanarArray(**RX_ARRAY_CONFIG)

# 移除現有發射機和接收機
for tx_name in list(scene.transmitters.keys()):
    scene.remove(tx_name)
for rx_name in list(scene.receivers.keys()):
    scene.remove(rx_name)

# 確認清空
assert len(scene.transmitters) == 0 and len(scene.receivers) == 0


# 新增發射機
def add_tx(scene, name, pos, ori, role, power_dbm):
    tx = Transmitter(name=name, position=pos, power_dbm=power_dbm)
    tx.role = role
    scene.add(tx)
    return tx


for name, pos, ori, role, p_dbm in TX_LIST:
    add_tx(scene, name, pos, ori, role, p_dbm)

# 新增接收機
rx_name, rx_pos = RX_CONFIG
rx = Receiver(name=rx_name, position=rx_pos)
scene.add(rx)

# 分組索引
tx_names = list(scene.transmitters.keys())
all_txs = [scene.get(n) for n in tx_names]
idx_des = [i for i, tx in enumerate(all_txs) if getattr(tx, "role", None) == "desired"]
idx_jam = [i for i, tx in enumerate(all_txs) if getattr(tx, "role", None) == "jammer"]

# RadioMap 計算
rm_solver = RadioMapSolver()
rm = rm_solver(scene, **RMSOLVER_ARGS)

# PathSolver 函式
solver = PathSolver()


def solve():
    return solver(scene, **PATHSOLVER_ARGS)


# 計算 CFR
freqs = subcarrier_frequencies(N_SUBCARRIERS, SUBCARRIER_SPACING)
for name in scene.transmitters:
    scene.get(name).velocity = [30, 0, 0]
paths = solve()

ofdm_symbol_duration = 1 / subcarrier_spacing
delay_resolution = ofdm_symbol_duration / num_subcarriers
doppler_resolution = subcarrier_spacing / num_ofdm_symbols

H_unit = paths.cfr(
    frequencies=freqs,
    sampling_frequency=1 / ofdm_symbol_duration,
    num_time_steps=num_ofdm_symbols,
    normalize_delays=False,
    normalize=False,
    out_type="numpy",
).squeeze()

H_all = H_unit.sum(axis=0)
H_des = H_unit[idx_des].sum(axis=0)
H_jam = H_unit[idx_jam].sum(axis=0)
tx_p_lin = 10 ** (np.array([tx.power_dbm for tx in all_txs]) / 10) / 1e3
tx_p_lin = np.squeeze(tx_p_lin)
sqrtP = np.sqrt(tx_p_lin)[:, None, None]
H_unit = H_unit * sqrtP


# 計算 Delay-Doppler 圖
def to_delay_doppler(H_tf):
    Hf = np.fft.fftshift(H_tf, axes=1)
    h_delay = np.fft.ifft(Hf, axis=1, norm="ortho")
    h_dd = np.fft.fft(h_delay, axis=0, norm="ortho")
    h_dd = np.fft.fftshift(h_dd, axes=0)
    return h_dd


Hdd_list = [np.abs(to_delay_doppler(H_unit[i])) for i in range(H_unit.shape[0])]

# 動態組合網格
grids = []
labels = []
doppler_bins = np.arange(
    -num_ofdm_symbols / 2 * doppler_resolution,
    num_ofdm_symbols / 2 * doppler_resolution,
    doppler_resolution,
)
delay_bins = np.arange(0, num_subcarriers * delay_resolution, delay_resolution) / 1e-9
x, y = np.meshgrid(delay_bins, doppler_bins)

offset = 20
x_start = int(num_subcarriers / 2) - offset
x_end = int(num_subcarriers / 2) + offset
y_start = 0
y_end = offset
x_grid = x[x_start:x_end, y_start:y_end]
y_grid = y[x_start:x_end, y_start:y_end]

# Desired 個別
for k, i in enumerate(idx_des):
    Zi = Hdd_list[i][x_start:x_end, y_start:y_end]
    grids.append(Zi)
    labels.append(f"Des Tx{i}")

# Jammer 個別
for k, i in enumerate(idx_jam):
    Zi = Hdd_list[i][x_start:x_end, y_start:y_end]
    grids.append(Zi)
    labels.append(f"Jam Tx{i}")

# Desired All
if idx_des:
    Z_des_all = np.sum([Hdd_list[i] for i in idx_des], axis=0)
    grids.append(Z_des_all[x_start:x_end, y_start:y_end])
    labels.append("Des ALL")

# Jammer All
if idx_jam:
    Z_jam_all = np.sum([Hdd_list[i] for i in idx_jam], axis=0)
    grids.append(Z_jam_all[x_start:x_end, y_start:y_end])
    labels.append("Jam ALL")

# All Tx
Z_all = np.sum(Hdd_list, axis=0)
grids.append(Z_all[x_start:x_end, y_start:y_end])
labels.append("ALL Tx")

# 統一 Z 軸
z_min = 0
z_max = max(g.max() for g in grids) * 1.05

# 自動排版
n_plots = len(grids)
cols = 3
rows = int(np.ceil(n_plots / cols))
figsize = (cols * 4.5, rows * 4.5)

fig = plt.figure(figsize=figsize)

for idx, (Z, label) in enumerate(zip(grids, labels), start=1):
    ax = fig.add_subplot(rows, cols, idx, projection="3d")
    ax.plot_surface(x_grid, y_grid, Z, cmap="viridis", edgecolor="none")
    ax.set_title(f"Delay–Doppler |{label}|", pad=8)
    ax.set_xlabel("Delay (ns)")
    ax.set_ylabel("Doppler (Hz)")
    ax.set_zlabel("|H|")
    ax.set_zlim(z_min, z_max)

plt.tight_layout()
plt.savefig("delay_doppler_plot.png")
plt.close()
