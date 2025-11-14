#!/usr/bin/env python3
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

INPUT_CSV = "output/sloc/loc.csv"            # adjust path if needed
OUT_DIR = "plots/sloc"  # adjust path if needed
OUT_DIR = os.path.expanduser(OUT_DIR)
os.makedirs(OUT_DIR, exist_ok=True)

# Read CSV
df = pd.read_csv(INPUT_CSV)
# Ensure columns names (strip whitespace)
df.columns = [c.strip() for c in df.columns]

# Basic sanity: require project, LOC, SLOC
if not {"project","LOC","SLOC"}.issubset(set(df.columns)):
    raise SystemExit("CSV must contain columns: project, LOC, SLOC")

# Convert numeric columns
df["LOC"] = pd.to_numeric(df["LOC"], errors="coerce").fillna(0).astype(int)
df["SLOC"] = pd.to_numeric(df["SLOC"], errors="coerce").fillna(0).astype(int)

projects = df["project"].tolist()
locs = df["LOC"].values
slocs = df["SLOC"].values

# 1) Combined LOC vs SLOC bar chart (side-by-side)
x = np.arange(len(projects))
width = 0.35

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.bar(x - width/2, locs, width, label="LOC")
ax.bar(x + width/2, slocs, width, label="SLOC")
ax.set_xticks(x)
ax.set_xticklabels(projects, rotation=25, ha="right")
ax.set_ylabel("Lines")
ax.set_title("LOC vs SLOC per Project")
ax.legend()
ax.grid(axis="y", linestyle=":", linewidth=0.5, alpha=0.7)

plt.tight_layout()
combined_path = os.path.join(OUT_DIR, "loc_vs_sloc_combined.pdf")
fig.savefig(combined_path)
plt.close(fig)
print("Saved:", combined_path)

# 2) SLOC / LOC ratio bar chart (density)
# Avoid division by zero
ratio = (df["SLOC"] / df["LOC"]).replace([float('inf'), -float('inf')], 0).fillna(0)

fig, ax = plt.subplots(figsize=(7, 4))
ax.bar(projects, ratio)
ax.set_ylim(0, 1.05)  # ratio logically in [0,1], small headroom
ax.set_ylabel("SLOC / LOC")
ax.set_title("Source Code Density (SLOC / LOC)")
ax.set_xticks(np.arange(len(projects)))
ax.set_xticklabels(projects, rotation=25, ha="right")
ax.grid(axis="y", linestyle=":", linewidth=0.5, alpha=0.7)

# annotate bars with ratio values
for i, v in enumerate(ratio):
    ax.text(i, v + 0.02, f"{v:.2f}", ha="center", va="bottom", fontsize=9)

plt.tight_layout()
ratio_path = os.path.join(OUT_DIR, "sloc_loc_ratio.pdf")
fig.savefig(ratio_path)
plt.close(fig)
print("Saved:", ratio_path)
