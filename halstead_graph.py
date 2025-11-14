#!/usr/bin/env python3
"""
Halstead Graph Generator

Produces:
 - effort_vs_difficulty.pdf
 - difficulty_vs_volume_quadrant.pdf
 - effort_per_function.pdf

Behavior:
 - Tries to read INPUT_DIR/halstead_all.csv with columns:
     project,vocabulary,volume,difficulty,effort,time,bugs,functions (functions optional)
 - If not found, falls back to embedded values provided by the user.
"""

import os
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ------------------ EDIT PATHS HERE ------------------
INPUT_DIR = "output/halstead"   # place halstead_all.csv here if you want to use your own CSV
OUT_DIR   = "plots/halstead"    # output folder for all PDF plots
# ----------------------------------------------------

plt.rcParams.update({"figure.dpi": 150, "font.size": 10})

# fallback data (values you provided)
FALLBACK = [
    {
        "project": "JsonCpp",
        "n1": 39, "n2": 696, "N1": 12562, "N2": 9791,
        "vocabulary": 735, "length": 22353,
        "volume": 212836.33462914446,
        "difficulty": 274.31681034482756,
        "effort": 58384584.44095127,
        "time": 3243588.024497293,
        "bugs": 70.94544487638149,
        # functions optional
    },
    {
        "project": "OGRE",
        "n1": 41, "n2": 15027, "N1": 298143, "N2": 235420,
        "vocabulary": 15068, "length": 533563,
        "volume": 7405427.759244964,
        "difficulty": 321.16257403340654,
        "effort": 2378346240.977555,
        "time": 132130346.72097526,
        "bugs": 2468.4759197483213,
    },
    {
        "project": "SQLite",
        "n1": 40, "n2": 12959, "N1": 396987, "N2": 327528,
        "vocabulary": 12999, "length": 724515,
        "volume": 9901303.876129277,
        "difficulty": 505.4834477968979,
        "effort": 5004945220.990616,
        "time": 278052512.2772564,
        "bugs": 3300.4346253764256,
    },
    {
        "project": "tmux",
        "n1": 38, "n2": 7809, "N1": 249560, "N2": 203254,
        "vocabulary": 7847, "length": 452814,
        "volume": 5858473.790502769,
        "difficulty": 494.5352798053528,
        "effort": 2897221975.2186127,
        "time": 160956776.40103403,
        "bugs": 1952.8245968342562,
    },
]

def ensure_out(path):
    os.makedirs(path, exist_ok=True)

def load_data(input_dir):
    csv_path = os.path.join(input_dir, "halstead_all.csv")
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        # normalize columns
        df.columns = [c.strip().lower() for c in df.columns]
        required = {"project","vocabulary","volume","difficulty","effort","bugs"}
        if not required.issubset(set(df.columns)):
            raise ValueError(f"{csv_path} must contain columns: {required}")
        return df
    else:
        # fallback -> build dataframe
        df = pd.DataFrame(FALLBACK)
        return df

def fmt_sci(x):
    # format large numbers in scientific notation with 2 significant digits
    if x == 0:
        return "0"
    exp = int(math.floor(math.log10(abs(x))))
    mant = x / (10**exp)
    return f"{mant:.2f}\\times10^{ {exp} }".replace("^{ ", "^{").replace(" }", "}")

def plot_effort_vs_difficulty(df, outpath):
    fig, ax = plt.subplots(figsize=(8,6))
    x = df["difficulty"].astype(float)
    y = df["effort"].astype(float)
    projects = df["project"].astype(str)

    ax.scatter(x, y, s=80, alpha=0.85, edgecolor="k", linewidth=0.6)
    for xi, yi, p in zip(x, y, projects):
        ax.annotate(p, (xi, yi), xytext=(6,3), textcoords="offset points", fontsize=9)

    ax.set_xlabel("Halstead Difficulty (D)")
    ax.set_ylabel("Halstead Effort (E)")
    ax.set_title("Halstead Effort vs Difficulty")
    ax.grid(axis="both", linestyle=":", alpha=0.6)

    # log scale for effort (y) because efforts vary hugely
    ax.set_yscale("log")
    # minor ticks
    ax.ticklabel_format(axis="x", style="plain")
    plt.tight_layout()
    fig.savefig(outpath)
    plt.close(fig)

def plot_difficulty_vs_volume_quadrant(df, outpath):
    fig, ax = plt.subplots(figsize=(8,6))
    x = df["difficulty"].astype(float)
    y = df["volume"].astype(float)
    projects = df["project"].astype(str)

    ax.scatter(x, y, s=80, alpha=0.85, edgecolor="k", linewidth=0.6)
    for xi, yi, p in zip(x, y, projects):
        ax.annotate(p, (xi, yi), xytext=(6,3), textcoords="offset points", fontsize=9)

    ax.set_xlabel("Halstead Difficulty (D)")
    ax.set_ylabel("Halstead Volume (V)")
    ax.set_title("Difficulty vs Volume (Architectural Signature)")

    # log scale for volume to keep plot readable
    ax.set_yscale("log")
    # draw median lines to create quadrants
    med_x = np.median(x)
    med_y = np.median(y)
    ax.axvline(med_x, color="gray", linestyle="--", linewidth=0.8)
    ax.axhline(med_y, color="gray", linestyle="--", linewidth=0.8)
    ax.text(0.02, 0.95, f"median D={med_x:.1f}\nmedian V={int(med_y):,}", transform=ax.transAxes,
            ha="left", va="top", fontsize=9, bbox=dict(facecolor="white", alpha=0.7, edgecolor="none"))

    ax.grid(axis="x", linestyle=":", alpha=0.6)
    plt.tight_layout()
    fig.savefig(outpath)
    plt.close(fig)

def plot_effort_per_function(df, outpath):
    fig, ax = plt.subplots(figsize=(8,5))
    # need functions column; if missing, try to read from user-provided mapping or set to NaN
    if "functions" in df.columns:
        funcs = df["functions"].astype(float)
    else:
        # attempt to get functions from an external summary CSV in same folder
        funcs = None

    labels = df["project"].astype(str)
    efforts = df["effort"].astype(float)

    if funcs is None or funcs.isnull().any():
        # we can't compute per-function exactly; instead compute Effort / (Volume) as proxy
        eff_per_unit = efforts / df["vocabulary"].astype(float)  # fallback metric: effort per vocabulary token
        ax.bar(labels, eff_per_unit)
        ax.set_ylabel("Effort per Vocabulary Token (E / vocabulary) [proxy]")
        ax.set_title("Effort per Function (fallback: Effort/Vocabulary shown)")
        # annotate original Effort values on top
        for i, val in enumerate(eff_per_unit):
            ax.text(i, val + 0.02*max(eff_per_unit), f"{int(efforts.iloc[i]):,}", ha="center", va="bottom", fontsize=8, rotation=0)
    else:
        eff_per_func = efforts / funcs
        ax.bar(labels, eff_per_func)
        ax.set_ylabel("Effort per Function (person-discriminations)")
        ax.set_title("Halstead Effort per Function")
        for i, val in enumerate(eff_per_func):
            ax.text(i, val + 0.02*max(eff_per_func), f"{val:,.0f}", ha="center", va="bottom", fontsize=9)

    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=25, ha="right")
    ax.grid(axis="y", linestyle=":", alpha=0.6)
    plt.tight_layout()
    fig.savefig(outpath)
    plt.close(fig)

def main():
    ensure_out(OUT_DIR)
    df = load_data(INPUT_DIR)

    # Ensure numeric types
    for col in ["vocabulary","volume","difficulty","effort","bugs"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Save a small CSV copy used for plotting (optional)
    df.to_csv(os.path.join(OUT_DIR, "halstead_used_for_plots.csv"), index=False)

    # Plot 1: Effort vs Difficulty
    plot_effort_vs_difficulty(df, os.path.join(OUT_DIR, "effort_vs_difficulty.pdf"))

    # Plot 2: Difficulty vs Volume (quadrant)
    plot_difficulty_vs_volume_quadrant(df, os.path.join(OUT_DIR, "difficulty_vs_volume_quadrant.pdf"))

    # Plot 3: Effort per Function (or fallback)
    plot_effort_per_function(df, os.path.join(OUT_DIR, "effort_per_function.pdf"))

    print("Halstead plots saved to:", OUT_DIR)

if __name__ == "__main__":
    main()
