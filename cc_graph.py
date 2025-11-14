#!/usr/bin/env python3
"""
Cyclomatic Complexity Plot Generator — final version

Features:
- Dynamic per-project x-axis capping based on percentiles.
- Per-project histogram capped and annotated for outliers (top values shown).
- Average CC plot with close numeric labels.
- Max CC plot with numeric labels.
- High-CC counts plot with numeric labels above each bar.
- Boxplot removed.

Edit INPUT_DIR and OUT_DIR below.
"""
import os
import glob
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ------------------- CONFIG -------------------
INPUT_DIR = "output/cc"    # folder with csvs
OUT_DIR = "plots/cc"     # where PDFs will be saved
MIN_CAP = 10              # minimum x-axis cap
GLOBAL_MAX_CAP = 50       # max allowed x-axis cap (visual)
TOP_OUTLIER_SHOW = 5      # how many top outlier values to show in annotation
# ------------------------------------------------


def ensure_out(path):
    os.makedirs(path, exist_ok=True)


def read_cc_csv(path):
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    if "cyclomatic" not in df.columns:
        raise ValueError(f"'cyclomatic' column not in {path}")
    return pd.to_numeric(df["cyclomatic"], errors="coerce").dropna().astype(int)


def choose_cap(series, min_cap=MIN_CAP, global_max=GLOBAL_MAX_CAP):
    """Choose dynamic cap based on percentiles."""
    if series.empty:
        return min_cap, {}
    p75 = np.percentile(series, 75)
    p90 = np.percentile(series, 90)
    p95 = np.percentile(series, 95)
    p99 = np.percentile(series, 99)

    if p99 <= global_max:
        cap = math.ceil(p99)
    elif p95 <= global_max:
        cap = math.ceil(p95)
    elif p90 <= global_max:
        cap = math.ceil(p90)
    else:
        cap = global_max

    cap = max(min_cap, cap)
    return cap, {"p75": p75, "p90": p90, "p95": p95, "p99": p99}


def plot_histogram_with_outliers(series, project_label, outpath, cap):
    """Histogram capped at chosen limit, with outlier annotation."""
    fig, ax = plt.subplots(figsize=(8, 4.5))

    outliers = series[series > cap].sort_values(ascending=False)
    clipped = series[series <= cap]

    bins = np.arange(0, cap + 2) - 0.5
    counts, edges, patches = ax.hist(clipped, bins=bins, edgecolor='black', linewidth=0.4)

    n_outliers = int(outliers.size)
    if n_outliers > 0:
        # small red bar to indicate number of outliers (drawn to the right of cap)
        ax.bar(cap + 0.6, n_outliers, width=0.3, color='tab:red', alpha=0.7)
        top_vals = outliers.unique()[:TOP_OUTLIER_SHOW]
        info_text = f"Outliers (>{cap}): {n_outliers}\nTop: {', '.join(map(str, top_vals))}"
        ax.text(0.98, 0.95, info_text, transform=ax.transAxes,
                ha="right", va="top",
                bbox=dict(facecolor='white', alpha=0.85, edgecolor='black'), fontsize=9)

    ax.set_xlabel("Cyclomatic Complexity")
    ax.set_ylabel("Number of functions")
    ax.set_title(f"CC Distribution — {project_label} (cap = {cap})")

    xticks = np.arange(0, cap + 1)
    step = 2 if len(xticks) > 20 else 1
    ax.set_xticks(xticks[::step])
    ax.set_xlim(-0.6, cap + 1)

    ax.grid(axis="y", linestyle=":", alpha=0.6)
    plt.tight_layout()
    fig.savefig(outpath)
    plt.close(fig)


def plot_bar(values, labels, ylabel, title, outpath, annotate=False):
    """General bar plot function, with optional numeric annotations."""
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(labels))
    bars = ax.bar(x, values, color="C0")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=25, ha="right")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(axis="y", linestyle=":", alpha=0.6)

    if annotate:
        for bar in bars:
            height = bar.get_height()
            # tighter placement for averages, dynamic offset
            if "Average" in title:
                # offset proportional to height but small; ensure minimum spacing
                offset = 0.001 * height
                offset = max(offset, 0.12)
                label_text = f"{height:.2f}"
            else:
                offset = 0.02 * height
                offset = max(offset, 0.12)
                label_text = f"{int(round(height))}"
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height + offset,
                label_text,
                ha="center", va="bottom", fontsize=9
            )

    plt.tight_layout()
    fig.savefig(outpath)
    plt.close(fig)


def plot_high_cc_counts(dict_cc, thresholds, outpath):
    projects = list(dict_cc.keys())
    counts = {t: [(dict_cc[p] > t).sum() for p in projects] for t in thresholds}

    x = np.arange(len(projects))
    width = 0.2
    offsets = np.linspace(-width, width, len(thresholds))

    fig, ax = plt.subplots(figsize=(10, 5))

    for i, t in enumerate(thresholds):
        bar_positions = x + offsets[i]
        bar_values = counts[t]
        bars = ax.bar(bar_positions, bar_values, width=width, label=f"CC > {t}")

        # numeric labels above each bar (tight)
        for bar, val in zip(bars, bar_values):
            height = val
            offset = 0.02 * max(1, height)
            offset = max(offset, 0.12)
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height + offset,
                f"{int(height)}",
                ha='center', va='bottom', fontsize=9
            )

    ax.set_xticks(x)
    ax.set_xticklabels(projects, rotation=25, ha="right")
    ax.set_ylabel("Number of Functions")
    ax.set_title("Counts of High-Complexity Functions")
    ax.legend()
    ax.grid(axis="y", linestyle=":", alpha=0.6)

    plt.tight_layout()
    fig.savefig(outpath)
    plt.close(fig)


# ------------------- MAIN -------------------
ensure_out(OUT_DIR)

csv_paths = sorted(glob.glob(os.path.join(INPUT_DIR, "*.csv")))
if not csv_paths:
    raise SystemExit(f"No CSV files found in {INPUT_DIR}")

dict_cc = {}
labels = []
caps_report = {}

for path in csv_paths:
    name = os.path.splitext(os.path.basename(path))[0]
    label = name.replace("_cc", "").replace("_", " ").strip()
    dict_cc[label] = read_cc_csv(path)
    labels.append(label)

# 1 — Average CC (annotated)
avg_vals = [dict_cc[p].mean() for p in labels]
plot_bar(
    avg_vals, labels,
    "Average CC",
    "Average Cyclomatic Complexity per Project",
    os.path.join(OUT_DIR, "avg_cc_per_project.pdf"),
    annotate=True
)

# 2 — Max CC (annotated)
max_vals = [dict_cc[p].max() for p in labels]
plot_bar(
    max_vals, labels,
    "Max CC",
    "Maximum Cyclomatic Complexity per Project",
    os.path.join(OUT_DIR, "max_cc_per_project.pdf"),
    annotate=True
)

# 3 — Per-project histograms with dynamic caps and outlier annotation
for project, series in dict_cc.items():
    cap, pct = choose_cap(series)
    caps_report[project] = {"cap": cap, "percentiles": pct}
    outpath = os.path.join(OUT_DIR, f"cc_histogram_{project.replace(' ', '_')}.pdf")
    plot_histogram_with_outliers(series, project, outpath, cap=cap)

# 4 — High CC counts plot
thresholds = [5, 10, 20]
plot_high_cc_counts(dict_cc, thresholds, os.path.join(OUT_DIR, "high_cc_counts.pdf"))

# Diagnostics print
print("Chosen caps and percentiles per project:")
for p, info in caps_report.items():
    print(f"- {p}: cap={info['cap']}, percentiles={info['percentiles']}")

print("\nAll plots saved in:", OUT_DIR)
