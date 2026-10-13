"""Figures 1 and 2 of the paper, from the recorded data.

  Figure 1 (fig1_divergence): state creation order against the measured work W(s), for three program groups. Reads ../data.
  Figure 2 (fig2_treesize_bands): macro rho of the live count against work, by tree size. Reads ../results/44_nesting_decomposition_groups.csv,
  which nesting_decomposition.py writes.

Output: fig1_divergence.pdf and fig2_treesize_bands.pdf (with a PNG preview of each) in this folder.

Usage:
    python make_figures.py
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "analysis"))
from models_m1_to_m5 import load_all

OUT_DIR = os.path.dirname(__file__)

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 8,
    "axes.titlesize": 8.5,
    "axes.labelsize": 8,
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5,
    "legend.fontsize": 7.5,
    "axes.linewidth": 0.6,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "pdf.fonttype": 42,   # embed as real (editable/selectable) text, not outlined paths
    "ps.fonttype": 42,
})

SINGLE_COL = 3.5   # inches
DOUBLE_COL = 7.16  # inches

OI_BLUE = "#0072B2"


def save(fig, name):
    fig.savefig(os.path.join(OUT_DIR, f"{name}.pdf"), bbox_inches="tight", metadata={"CreationDate": None})
    fig.savefig(os.path.join(OUT_DIR, f"{name}.png"), bbox_inches="tight", dpi=300)
    plt.close(fig)
    print(f"saved {name}.pdf / {name}.png")


def fig1_divergence():
    df = load_all()
    non_leaf = df[df["isEndStateAtEntry"] == False].copy()

    groups = ["InsertionSort", "HeapWork", "ArrayUtilsIndexOf"]
    fig, axes = plt.subplots(1, 3, figsize=(SINGLE_COL * 2.05, SINGLE_COL * 0.78), sharey=False)

    for ax, g in zip(axes, groups):
        sub = non_leaf[non_leaf["program_group"] == g]
        y = sub["actualSubtreeWork"].values.astype(float)
        y = np.where(y <= 0, 1, y)  # log-scale floor; actualSubtreeWork==0 only for leaves (excluded already)
        ax.scatter(sub["stateId"], y, s=4, alpha=0.4, color=OI_BLUE,
                   marker="o", linewidths=0)
        ax.set_yscale("log")
        ax.set_title(g, fontsize=8)
        ax.set_xlabel("state creation order")
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)

    axes[0].set_ylabel(r"subtree work $W(s)$ (log scale)")
    fig.suptitle(r"State creation order does not track measured subtree work",
                 fontsize=8.5, y=1.04)
    fig.tight_layout()
    save(fig, "fig1_divergence")


def fig2_treesize_bands():
    import pandas as pd
    csv_path = os.path.join(os.path.dirname(__file__), "..", "results", "44_nesting_decomposition_groups.csv")
    g = pd.read_csv(csv_path)
    bands = [(0, 15), (15, 60), (60, 300), (300, 10 ** 6)]
    labels = ["<15", "15-59", "60-299", "300+"]
    means, ns = [], []
    for lo, hi in bands:
        sub = g[(g["nonleaf"] >= lo) & (g["nonleaf"] < hi)]
        means.append(sub["rho_paper"].mean())
        ns.append(len(sub))

    fig, ax = plt.subplots(figsize=(SINGLE_COL * 0.92, SINGLE_COL * 1.05))
    x = np.arange(len(bands))
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color="0.85", linewidth=0.6, linestyle="-")
    ax.bar(x, means, width=0.6, color=OI_BLUE, edgecolor="black", linewidth=0.7, zorder=3)
    ax.axhline(0, color="black", linewidth=0.8)
    for xi, n in zip(x, ns):
        ax.text(xi, 0.028, f"n={n}", ha="center", va="bottom", fontsize=7)
    ax.set_ylim(min(means) - 0.08, 0.14)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_xlabel("non-leaf states in the tree")
    ax.set_ylabel(r"macro $\rho$ of live count vs. work")
    ax.set_title("Live-count signal weakens as trees grow", fontsize=8.5, pad=8)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", length=3)
    fig.tight_layout()
    save(fig, "fig2_treesize_bands")


if __name__ == "__main__":
    fig1_divergence()
    fig2_treesize_bands()
