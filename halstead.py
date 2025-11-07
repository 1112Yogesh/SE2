import re
import sys
import os
import csv
import math
from typing import List, Tuple, Dict, Optional

# Common C / C++ operators and symbols (regex patterns)
OPERATORS = [
    r"\+\+", r"--", r"->", r"\.", r"::",
    r"\+\=", r"-=", r"\*=", r"/=", r"%=",
    r"\+", r"-", r"\*", r"/", r"%", r"=", r"==", r"!=", r"<=", r">=", r"<", r">",
    r"&&", r"\|\|", r"!", r"&", r"\|", r"\^", r"~", r"<<", r">>",
    r"\?", r":", r";", r",",
    r"\(", r"\)", r"\{", r"\}", r"\[", r"\]"
]

# Regex for operands (identifiers, constants)
IDENTIFIER = re.compile(r"\b[_a-zA-Z][_a-zA-Z0-9]*\b")
NUMBER = re.compile(r"\b\d+(?:\.\d+)?\b")


def strip_comments_and_strings(code: str) -> str:
    """Remove comments and string/char literals from source code."""
    # Remove single-line comments
    code = re.sub(r"//.*", "", code)
    # Remove multi-line comments
    code = re.sub(r"/\*[\s\S]*?\*/", "", code)
    # Remove string and char literals (naive but sufficient for token counting)
    code = re.sub(r'"(?:\\.|[^"\\])*"', "", code)
    code = re.sub(r"'(?:\\.|[^'\\])*'", "", code)
    return code


def tokenize_source(code: str) -> Tuple[List[str], List[str]]:
    """Return lists of operators and operands found in the source code."""
    operators_found: List[str] = []
    operands_found: List[str] = []

    code = strip_comments_and_strings(code)

    # Match operators. Sort by length (regex order) to prefer multi-char operators first.
    for op in sorted(OPERATORS, key=len, reverse=True):
        matches = re.findall(op, code)
        if matches:
            operators_found.extend(matches)
            code = re.sub(op, " ", code)

    # Match operands: identifiers and numbers
    operands_found.extend(IDENTIFIER.findall(code))
    # NUMBER.findall returns tuples if groups exist; use finditer to get group(0)
    for m in NUMBER.finditer(code):
        operands_found.append(m.group(0))

    return operators_found, operands_found


def compute_halstead(operators: List[str], operands: List[str]) -> Dict[str, float]:
    """Compute Halstead metrics from lists of operators and operands.

    Returns a dictionary with n1, n2, N1, N2, vocabulary, length, volume, difficulty, effort, time, bugs.
    """
    n1 = len(set(operators))
    n2 = len(set(operands))
    N1 = len(operators)
    N2 = len(operands)

    vocabulary = n1 + n2
    length = N1 + N2

    volume = 0.0
    if vocabulary > 0 and length > 0:
        volume = length * math.log2(vocabulary)

    difficulty = 0.0
    if n2 > 0:
        difficulty = (n1 / 2.0) * (N2 / n2)

    effort = difficulty * volume
    time = effort / 18.0 if effort > 0 else 0.0
    bugs = volume / 3000.0 if volume > 0 else 0.0

    return {
        "n1": n1,
        "n2": n2,
        "N1": N1,
        "N2": N2,
        "vocabulary": vocabulary,
        "length": length,
        "volume": volume,
        "difficulty": difficulty,
        "effort": effort,
        "time": time,
        "bugs": bugs,
    }


def analyze_file(path: str) -> Dict[str, float]:
    """Analyze a single C/C++ source file and return its Halstead metrics."""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        code = f.read()
    ops, oprs = tokenize_source(code)
    return compute_halstead(ops, oprs)


def analyze_directory(directory: str, extensions: List[str], ignore: Optional[List[str]] = None) -> Dict[str, float]:
    """Walk a directory and aggregate Halstead metrics across files with given extensions.

    ignore: optional list of regex patterns to skip file names.
    """
    all_ops: List[str] = []
    all_oprs: List[str] = []

    if not os.path.exists(directory):
        raise FileNotFoundError(directory)

    for root, _, files in os.walk(directory):
        for name in files:
            if not any(name.endswith(ext) for ext in extensions):
                continue
            if ignore and any(re.match(pat, name) for pat in ignore):
                continue
            path = os.path.join(root, name)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    code = f.read()
                ops, oprs = tokenize_source(code)
                all_ops.extend(ops)
                all_oprs.extend(oprs)
            except Exception:
                # Skip files we can't read for any reason
                continue

    return compute_halstead(all_ops, all_oprs)


class Project:
    """Represents a code project to analyze."""

    def __init__(self, name: str, description: str, src: str, src_file_extensions: List[str], ignore: Optional[List[str]] = None):
        self.name = name
        self.description = description
        self.src = src
        self.src_file_extensions = src_file_extensions
        self.ignore = ignore

    def get_halstead_metrics(self) -> Dict[str, float]:
        """Return aggregated Halstead metrics for the project source path."""
        if os.path.isfile(self.src):
            # Single file
            return analyze_file(self.src)
        else:
            return analyze_directory(self.src, self.src_file_extensions, self.ignore)


def write_metrics_csv(output_path: str, metrics: Dict[str, float]):
    fieldnames = ["n1", "n2", "N1", "N2", "vocabulary", "length", "volume", "difficulty", "effort", "time", "bugs"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        # Ensure all keys exist (fill 0 if missing)
        row = {k: metrics.get(k, 0) for k in fieldnames}
        writer.writerow(row)


def halstead_matrix_for_projects(projects: List[Project]) -> Dict[str, Dict[str, float]]:
    """Compute Halstead metrics for a list of projects and return a mapping name -> metrics."""
    results: Dict[str, Dict[str, float]] = {}
    for proj in projects:
        try:
            results[proj.name] = proj.get_halstead_metrics()
        except FileNotFoundError:
            results[proj.name] = {"error": f"path not found: {proj.src}"}
    return results


if __name__ == "__main__":
    # Define projects to analyze
    projects = [
        Project(
            name="Json CPP",
            description="jsoncpp",
            src="jsoncpp/src/lib_json",
            src_file_extensions=[".cpp"],
        ),
        Project(
            name="OGRE",
            description="Object-Oriented Graphics Rendering Engine",
            src="ogre/OgreMain/src",
            src_file_extensions=[".c", ".cpp"],
        ),
        Project(
            name="Sqlite",
            description="SQLite",
            src="sqlite/src",
            src_file_extensions=[".c"],
            ignore=[r"test.*"],
        ),
        Project(
            name="tmux",
            description="Terminal multiplexer",
            src="tmux",
            src_file_extensions=[".c"],
            ignore=[r"compat/.*"],
        ),
    ]

    output_dir = "output/halstead"
    os.makedirs(output_dir, exist_ok=True)

    results = halstead_matrix_for_projects(projects)
    for proj in projects:
        metrics = results.get(proj.name, {})
        out_file = os.path.join(output_dir, f"{proj.name.replace(' ', '_').lower()}_halstead.csv")
        if metrics and "error" not in metrics:
            write_metrics_csv(out_file, metrics)
        else:
            # Write a small CSV indicating an error
            with open(out_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["error"])
                writer.writerow([metrics.get("error")])

    print(f"Wrote halstead metrics to: {output_dir}")
