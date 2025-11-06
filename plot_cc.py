#!/usr/bin/env python3
"""Plot frequency of cyclomatic complexity from cc_matrix.csv.

Expected input CSV columns: project,file,function,start_line,end_line,nloc,cyclomatic,params

Creates: cc_cyclomatic_freq.png (bar chart)
"""
import csv
import argparse
from collections import Counter
import statistics
import os

try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None


def read_cyclomatic(csv_path):
    vals = []
    if not os.path.exists(csv_path):
        raise FileNotFoundError(csv_path)
    with open(csv_path, newline='') as fh:
        reader = csv.DictReader(fh)
        if 'cyclomatic' not in reader.fieldnames:
            # try lowercase/other names
            alt = None
            for name in reader.fieldnames:
                if 'cyclomatic' in name.lower():
                    alt = name
                    break
            if alt is None:
                raise ValueError('No cyclomatic column found in CSV')
            key = alt
        else:
            key = 'cyclomatic'

        for row in reader:
            v = row.get(key, '').strip()
            try:
                vals.append(int(float(v)))
            except Exception:
                # skip empty or non-numeric entries
                continue
    return vals


def plot_frequency(values, out_path, title=None):
    if plt is None:
        raise RuntimeError('matplotlib not installed')

    if not values:
        raise ValueError('No cyclomatic values to plot')

    counter = Counter(values)
    xs = sorted(counter.keys())
    ys = [counter[x] for x in xs]

    plt.figure(figsize=(10, 6))
    plt.bar(xs, ys, width=0.8, color='tab:blue', edgecolor='black')
    plt.xlabel('Cyclomatic Complexity')
    plt.ylabel('Frequency (number of functions)')
    if title:
        plt.title(title)
    else:
        plt.title('Cyclomatic Complexity Frequency')
    plt.xticks(xs)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def read_file_avg(csv_path):
    """Return a dict mapping file -> (avg_cyclomatic, function_count)."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(csv_path)
    sums = {}
    counts = {}
    with open(csv_path, newline='') as fh:
        reader = csv.DictReader(fh)
        # detect file and cyclomatic column names
        file_key = None
        cyclo_key = None
        for name in reader.fieldnames:
            lname = name.lower()
            if file_key is None and lname in ('file', 'filename', 'path'):
                file_key = name
            if cyclo_key is None and 'cyclomatic' in lname:
                cyclo_key = name
        if file_key is None:
            # try common alternatives
            for name in reader.fieldnames:
                if 'file' in name.lower():
                    file_key = name
                    break
        if cyclo_key is None:
            for name in reader.fieldnames:
                if 'cyclomatic' in name.lower():
                    cyclo_key = name
                    break
        if file_key is None or cyclo_key is None:
            raise ValueError('Could not detect file or cyclomatic columns')

        for row in reader:
            f = row.get(file_key, '').strip()
            v = row.get(cyclo_key, '').strip()
            try:
                vnum = int(float(v))
            except Exception:
                continue
            sums[f] = sums.get(f, 0) + vnum
            counts[f] = counts.get(f, 0) + 1

    result = {}
    for f, s in sums.items():
        result[f] = (s / counts[f], counts[f])
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', '-c', default='cc_matrix_tmux.csv', help='Input cc_matrix.csv file')
    parser.add_argument('--out', '-o', default='cc_matrix_tmux_freq.png', help='Output image file')
    parser.add_argument('--mode', '-m', default='freq', choices=['freq', 'file-avg'], help='Plot mode: freq (by function) or file-avg (average by file)')
    parser.add_argument('--top', '-t', type=int, default=30, help='Top N files to show when mode=file-avg')
    args = parser.parse_args()

    if args.mode == 'freq':
        vals = read_cyclomatic(args.csv)
        total = len(vals)
        mean = statistics.mean(vals) if vals else 0
        med = statistics.median(vals) if vals else 0
        mx = max(vals) if vals else 0

        title = f'Cyclomatic Complexity Frequency (functions={total}, mean={mean:.2f}, median={med}, max={mx})'
        plot_frequency(vals, args.out, title=title)
        print(f'Wrote {args.out} — functions: {total}, mean: {mean:.2f}, median: {med}, max: {mx}')
    else:
        # group by file and plot average cyclomatic per file
        file_map = read_file_avg(args.csv)
        if not file_map:
            print('No file-level data found in CSV')
            return
        # sort by avg desc and take top N
        items = sorted(file_map.items(), key=lambda x: x[1][0], reverse=True)
        top_n = args.top
        items = items[:top_n]

        files = [os.path.basename(f) for f, _ in items]
        avgs = [v[0] for _, v in items]

        # plot
        if plt is None:
            raise RuntimeError('matplotlib not installed')
        plt.figure(figsize=(max(8, len(files)*0.4), 6))
        plt.bar(range(len(files)), avgs, color='tab:green', edgecolor='black')
        plt.xticks(range(len(files)), files, rotation=45, ha='right')
        plt.ylabel('Average Cyclomatic Complexity')
        plt.xlabel('File')
        plt.title(f'Average Cyclomatic per File (top {len(files)})')
        plt.tight_layout()
        plt.savefig(args.out)
        plt.close()
        print(f'Wrote {args.out} — plotted top {len(files)} files by avg cyclomatic')


if __name__ == '__main__':
    main()
