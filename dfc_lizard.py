import os
import re
from typing import Dict, List, Optional, Tuple
import lizard


def estimate_dfc_from_function(func_info) -> int:
    """
    Estimate Data Flow Complexity using Lizard function analysis.
    
    Since we can't do full reaching definitions analysis without AST,
    we use a heuristic approach based on:
    - Number of parameters (incoming data flow)
    - Cyclomatic complexity (control flow that affects data flow)
    - Token count as proxy for variable usage
    
    DFC ≈ (parameters × complexity) + (complexity - 1)
    This approximates interblock data dependencies.
    """
    # Base DFC: parameters represent incoming data dependencies
    param_flow = func_info.parameter_count
    
    # Control flow creates more data flow paths
    # Each decision point can create data dependencies
    control_flow = max(0, func_info.cyclomatic_complexity - 1)
    
    # Estimate: parameters flow through control paths
    dfc = (param_flow * control_flow) + control_flow
    
    return dfc


def analyze_file(file_path: str) -> Tuple[int, int]:
    """
    Analyze a single file and return (dfc, function_count).
    
    Uses Lizard to parse C/C++ files and estimates DFC based on
    function complexity and parameter flow.
    """
    try:
        analysis = lizard.analyze_file(file_path)
        
        total_dfc = 0
        func_count = 0
        
        for func in analysis.function_list:
            dfc = estimate_dfc_from_function(func)
            total_dfc += dfc
            func_count += 1
        
        return total_dfc, func_count
    except Exception:
        return 0, 0


def analyze_directory(directory: str, extensions: List[str], ignore: Optional[List[str]] = None) -> Dict[str, int]:
    """
    Aggregate DFC across all source files in a directory matching extensions.
    
    Returns a dict with total dfc, total_files, total_functions.
    """
    if not os.path.exists(directory):
        raise FileNotFoundError(directory)
    
    total_dfc = 0
    total_files = 0
    total_functions = 0
    
    for root, _, files in os.walk(directory):
        for name in files:
            if not any(name.endswith(ext) for ext in extensions):
                continue
            if ignore and any(re.match(pat, name) for pat in ignore):
                continue
            path = os.path.join(root, name)
            dfc, funcs = analyze_file(path)
            total_dfc += dfc
            total_functions += funcs
            total_files += 1
    
    return {"dfc": total_dfc, "files": total_files, "functions": total_functions}


class Project:
    """Represents a code project to analyze."""
    
    def __init__(self, name: str, description: str, src: str, src_file_extensions: List[str], ignore: Optional[List[str]] = None):
        self.name = name
        self.description = description
        self.src = src
        self.src_file_extensions = src_file_extensions
        self.ignore = ignore
    
    def get_dfc_metrics(self) -> Dict[str, int]:
        """Return aggregated DFC metrics for the project source path."""
        if os.path.isfile(self.src):
            dfc, funcs = analyze_file(self.src)
            return {"dfc": dfc, "files": 1, "functions": funcs}
        else:
            return analyze_directory(self.src, self.src_file_extensions, self.ignore)


def write_dfc_csv(output_path: str, metrics: Dict[str, int]):
    import csv
    fieldnames = ["dfc", "files", "functions"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        row = {k: metrics.get(k, 0) for k in fieldnames}
        writer.writerow(row)


if __name__ == "__main__":
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
    
    output_dir = "output/dfc"
    os.makedirs(output_dir, exist_ok=True)
    
    for proj in projects:
        try:
            metrics = proj.get_dfc_metrics()
            out_file = os.path.join(output_dir, f"{proj.name.replace(' ', '_').lower()}_dfc.csv")
            write_dfc_csv(out_file, metrics)
            print(f"{proj.name}: DFC={metrics['dfc']}, Files={metrics['files']}, Functions={metrics['functions']}")
        except FileNotFoundError:
            out_file = os.path.join(output_dir, f"{proj.name.replace(' ', '_').lower()}_dfc.csv")
            with open(out_file, "w", newline="", encoding="utf-8") as f:
                import csv
                writer = csv.writer(f)
                writer.writerow(["error"])
                writer.writerow([f"path not found: {proj.src}"])
            print(f"{proj.name}: Path not found")
    
    print(f"\nWrote DFC metrics to: {output_dir}")
