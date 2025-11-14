#!/usr/bin/env python3
"""
DFC Plot & Table Generator (Hardcoded Paths Version, improved x-tick handling)

- Hard-coded INPUT_DIR and OUT_DIR near the top.
- Keeps default Matplotlib colors (no orange override).
- For sqlite and tmux histograms: if the x-axis would have > ~40 distinct integer ticks,
  automatically increase bin width so the number of distinct x positions <= 40 (30-40).
"""

import os
import glob
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams.update({"figure.dpi": 150})

# ------------------------------------------------------------
# 🔧 HARD-CODED PATHS (EDIT THESE ONLY)
# ------------------------------------------------------------
INPUT_DIR = "output/dfc"       # folder where *_functions.csv & *_summary.csv exist
OUT_DIR   = "plots/dfc"      # output folder for all PDF plots & tables
# ------------------------------------------------------------

def ensure_outdir(path):
    os.makedirs(path, exist_ok=True)


def read_functions_csv(path):
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    needed = {"file", "function", "dfc", "nloc"}
    if not needed.issubset(df.columns):
        raise ValueError(f"{path} missing required columns {needed}")
    df["dfc"] = pd.to_numeric(df["dfc"], errors="coerce").fillna(0).astype(int)
    df["nloc"] = pd.to_numeric(df["nloc"], errors="coerce").fillna(0).astype(int)
    return df


def read_summary_csv(path):
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    if "dfc" not in df.columns:
        raise ValueError(f"{path} missing 'dfc'")
    return df


def choose_hist_cap(series, min_cap=5, pct=95, global_max=200):
    if series.empty:
        return min_cap, 0
    cap = int(math.ceil(np.percentile(series, pct)))
    cap = max(min_cap, cap)
    cap = min(cap, global_max)
    n_out = int((series > cap).sum())
    return cap, n_out


def _compute_bin_step_for_limit(cap, desired_max_ticks=40):
    """
    Given integer cap (0..cap), compute an integer bin_step >=1 such that
    number of tick positions (approx (cap+1)/bin_step) <= desired_max_ticks.
    Returns bin_step.
    """
    total_positions = cap + 1
    if total_positions <= desired_max_ticks:
        return 1
    # compute minimal integer step
    step = math.ceil(total_positions / desired_max_ticks)
    # normalize step to a friendly number (1,2,5,10,20,50...) optionally
    # We'll snap to 1,2,5,10,20,50 etc for nicer axis.
    for base in [1,2,5,10,20,50,100]:
        if step <= base:
            return base
    return step


def plot_histogram_project(df, project, outpath):
    s = df["dfc"]
    cap, n_out = choose_hist_cap(s)
    # For tmux/sqlite we apply tick-limiting; for others keep fine-grained integer bins
    project_key = project.lower().strip()
    desired_ticks = None
    if project_key in ("tmux", "sqlite"):
        desired_ticks = 40  # limit to ~40 ticks for these two projects

    if desired_ticks:
        bin_step = _compute_bin_step_for_limit(cap, desired_max_ticks=desired_ticks)
    else:
        # default integer bins (step =1)
        bin_step = 1

    # create bins centered on multiples of bin_step
    bins = np.arange(0, cap + bin_step, bin_step) - (bin_step / 2.0)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    # Use default color palette (no explicit color) — matplotlib will use default blue
    ax.hist(s[s <= cap], bins=bins, edgecolor="black", linewidth=0.4)

    ax.set_title(f"DFC Distribution — {project} (cap = {cap})")
    ax.set_xlabel("DFC")
    ax.set_ylabel("Number of Functions")
    ax.grid(axis="y", linestyle=":", alpha=0.6)

    if n_out > 0:
        outliers = df[df["dfc"] > cap]["dfc"].sort_values(ascending=False).unique()[:5]
        # small red bar to indicate outliers (keeps default histogram color intact)
        ax.bar(cap + bin_step*0.5, n_out, width=bin_step*0.6, color="red", alpha=0.7)
        ax.text(0.98, 0.95,
                f"Outliers > {cap}: {n_out}\nTop: {', '.join(map(str, outliers))}",
                transform=ax.transAxes, ha="right", va="top",
                bbox=dict(facecolor="white", alpha=0.8, edgecolor="black"),
                fontsize=9)

    # set xticks: use bin_step as tick step, but reduce density if still too many
    xticks = np.arange(0, cap + 1, bin_step)
    # if too many ticks (still >40), increase tick interval
    if len(xticks) > 40:
        tick_interval = math.ceil(len(xticks) / 35)  # aim for ~35 ticks
        xticks = xticks[::tick_interval]

    ax.set_xticks(xticks)
    ax.set_xlim(-bin_step, cap + bin_step*1.2)
    plt.tight_layout()
    fig.savefig(outpath)
    plt.close(fig)


def plot_boxplot_all(dict_funcs, outpath):
    projects = list(dict_funcs.keys())
    data = [dict_funcs[p]["dfc"] for p in projects]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.boxplot(data, tick_labels=projects, showfliers=True)
    ax.set_ylabel("DFC")
    ax.set_title("DFC Distribution Across Projects")
    ax.grid(axis="y", linestyle=":", alpha=0.6)
    plt.tight_layout()
    fig.savefig(outpath)
    plt.close(fig)


def plot_total_dfc(summary_map, agg_map, outpath):
    projects = sorted(set(list(summary_map.keys()) + list(agg_map.keys())))
    totals = [summary_map.get(p, agg_map[p]) for p in projects]

    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(projects))
    bars = ax.bar(x, totals)  # default color (blue)

    ax.set_title("Total Data-Flow Complexity per Project")
    ax.set_xticks(x)
    ax.set_xticklabels(projects, rotation=25, ha="right")
    ax.set_ylabel("Total DFC")
    ax.grid(axis="y", linestyle=":", alpha=0.6)

    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 0.02 * h + 1,
                f"{int(h)}", ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    fig.savefig(outpath)
    plt.close(fig)


def plot_scatter_project(df, project, outpath):
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(df["nloc"], df["dfc"], s=10, alpha=0.7)  # default blue markers

    ax.set_title(f"DFC vs NLOC — {project}")
    ax.set_xlabel("NLOC")
    ax.set_ylabel("DFC")
    ax.grid(axis="both", linestyle=":", alpha=0.6)

    if len(df) > 1:
        corr = np.corrcoef(df["nloc"], df["dfc"])[0, 1]
        ax.text(0.02, 0.95, f"Pearson r = {corr:.2f}",
                transform=ax.transAxes, ha="left", va="top",
                bbox=dict(facecolor="white", alpha=0.6))

    plt.tight_layout()
    fig.savefig(outpath)
    plt.close(fig)


def plot_scatter_combined(dict_funcs, outpath):
    fig, ax = plt.subplots(figsize=(8, 6))

    colors = plt.cm.tab10.colors
    for i, (project, df) in enumerate(dict_funcs.items()):
        # Keep default-ish color palette but do not change global defaults
        ax.scatter(df["nloc"], df["dfc"], s=8, alpha=0.6,
                   color=colors[i % len(colors)], label=project)

    ax.set_title("Combined DFC vs NLOC")
    ax.set_xlabel("NLOC")
    ax.set_ylabel("DFC")
    ax.legend(markerscale=2, fontsize=8)
    ax.grid(axis="both", linestyle=":", alpha=0.6)

    plt.tight_layout()
    fig.savefig(outpath)
    plt.close(fig)


def make_top10_table(all_funcs_df, out_csv, out_tex, out_pdf):
    top10 = all_funcs_df.sort_values("dfc", ascending=False).head(10)
    top10 = top10[["project", "file", "function", "dfc", "nloc"]]

    top10.to_csv(out_csv, index=False)

    # LaTeX table
    latex = top10.to_latex(index=False,
                           caption="Top 10 functions by Data-Flow Complexity",
                           label="tab:top10_dfc")
    with open(out_tex, "w") as f:
        f.write(latex)

    # PDF version of table
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.axis("off")
    table = ax.table(cellText=top10.values,
                     colLabels=top10.columns,
                     loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.2)
    plt.tight_layout()
    fig.savefig(out_pdf)
    plt.close(fig)


def main():
    ensure_outdir(OUT_DIR)

    # load all *_functions.csv
    func_files = sorted(glob.glob(os.path.join(INPUT_DIR, "*_functions.csv")))
    if not func_files:
        raise SystemExit("No *_functions.csv found in INPUT_DIR")

    dict_funcs = {}
    summary_map = {}
    agg_map = {}
    all_funcs = []

    for path in func_files:
        base = os.path.basename(path)
        project = base.replace("_functions.csv", "").replace("_", " ").strip()

        df = read_functions_csv(path)
        dict_funcs[project] = df
        agg_map[project] = int(df["dfc"].sum())

        # try to read summary
        summary_path = path.replace("_functions.csv", "_summary.csv")
        if os.path.exists(summary_path):
            try:
                s = read_summary_csv(summary_path)
                summary_map[project] = int(s.iloc[0]["dfc"])
            except:
                pass

        df2 = df[["file", "function", "dfc", "nloc"]].copy()
        df2["project"] = project
        all_funcs.append(df2)

    all_funcs_df = pd.concat(all_funcs, ignore_index=True)

    # 1. Histogram per project
    for project, df in dict_funcs.items():
        out = os.path.join(OUT_DIR, f"histogram_{project.replace(' ','_')}.pdf")
        plot_histogram_project(df, project, out)

    # 2. Combined boxplot
    plot_boxplot_all(dict_funcs, os.path.join(OUT_DIR, "boxplot_dfc_projects.pdf"))

    # 3. Total DFC per project
    plot_total_dfc(summary_map, agg_map, os.path.join(OUT_DIR, "total_dfc_per_project.pdf"))

    # 4. Scatter per project
    for project, df in dict_funcs.items():
        plot_scatter_project(df, project,
                             os.path.join(OUT_DIR, f"scatter_{project.replace(' ','_')}.pdf"))

    # Combined scatter
    plot_scatter_combined(dict_funcs, os.path.join(OUT_DIR, "scatter_combined.pdf"))

    # 5. Top 10 functions table
    make_top10_table(
        all_funcs_df,
        os.path.join(OUT_DIR, "top10_outliers.csv"),
        os.path.join(OUT_DIR, "top10_outliers.tex"),
        os.path.join(OUT_DIR, "top10_outliers.pdf")
    )

    print(f"All plots & tables saved in: {OUT_DIR}")


if __name__ == "__main__":
    main()
