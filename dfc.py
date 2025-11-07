import os
from typing import Dict, List, Optional, Tuple
import networkx as nx
from pycparser import c_parser, c_ast


class DataFlowAnalyzer(c_ast.NodeVisitor):
    """Extract simple basic blocks with defs and uses from a C AST."""

    def __init__(self):
        self.blocks: List[Dict[str, set]] = []
        self.current_block = {"defs": set(), "uses": set()}

    def add_block(self):
        if self.current_block["defs"] or self.current_block["uses"]:
            self.blocks.append(self.current_block)
        self.current_block = {"defs": set(), "uses": set()}

    # Assignments create defs on the lvalue and uses on the rvalue
    def visit_Assignment(self, node):
        if isinstance(node.lvalue, c_ast.ID):
            self.current_block["defs"].add(node.lvalue.name)
        # Recurse into rvalue to capture uses
        if node.rvalue:
            self.visit(node.rvalue)

    def visit_ID(self, node):
        # Every identifier occurrence is treated as a use (conservative)
        self.current_block["uses"].add(node.name)

    def visit_If(self, node):
        # Condition may use variables
        if node.cond:
            self.visit(node.cond)
        self.add_block()
        if node.iftrue:
            self.visit(node.iftrue)
            self.add_block()
        if node.iffalse:
            self.visit(node.iffalse)
            self.add_block()

    def visit_While(self, node):
        if node.cond:
            self.visit(node.cond)
        self.add_block()
        if node.stmt:
            self.visit(node.stmt)
        self.add_block()

    def visit_For(self, node):
        if node.init:
            self.visit(node.init)
        if node.cond:
            self.visit(node.cond)
        if node.next:
            self.visit(node.next)
        self.add_block()
        if node.stmt:
            self.visit(node.stmt)
        self.add_block()


def compute_data_flow_complexity(ast_root: c_ast.Node) -> Tuple[int, List[Dict[str, set]]]:
    """Compute a simple Data Flow Complexity (DFC) metric from the AST.

    This function builds basic blocks of defs/uses and computes reaching defs
    in a simple sequential control-flow graph. Returns (dfc, blocks).
    """
    analyzer = DataFlowAnalyzer()
    analyzer.visit(ast_root)
    # Ensure last block is captured
    analyzer.add_block()

    n = len(analyzer.blocks)
    if n == 0:
        return 0, analyzer.blocks

    # Build a simple sequential flow graph (0->1->2->...)
    G = nx.DiGraph()
    G.add_nodes_from(range(n))
    for i in range(n - 1):
        G.add_edge(i, i + 1)

    # Initialize reaching definitions sets
    reaching_defs: List[set] = [set() for _ in range(n)]
    changed = True

    while changed:
        changed = False
        for i in range(n):
            # in-defs are union of predecessors' out-defs
            in_defs = set()
            for pred in G.predecessors(i):
                in_defs |= reaching_defs[pred]

            # out_defs = (in_defs - killed) U generated
            generated = analyzer.blocks[i]["defs"]
            killed = analyzer.blocks[i]["defs"]  # simplistic: defs kill same-name previous defs
            new_out = (in_defs - killed) | generated
            if new_out != reaching_defs[i]:
                reaching_defs[i] = new_out
                changed = True

    # DFC: total number of reaching definitions across blocks
    dfc = sum(len(s) for s in reaching_defs)
    return dfc, analyzer.blocks


def analyze_file(file_path: str) -> Tuple[int, List[Dict[str, set]]]:
    """Parse a C file (with preprocessing fallback) and compute DFC.

    Tries parsing directly, then with pycparser.parse_file using the system
    preprocessor and pycparser's fake includes, and finally falls back to
    running `cpp -E -P` and parsing the result.
    """
    parser = c_parser.CParser()

    # 1) Try parsing raw file (cheap)
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()
        ast = parser.parse(code)
        dfc, blocks = compute_data_flow_complexity(ast)
        # If we found blocks, return immediately
        if blocks:
            return dfc, blocks
    except Exception:
        # ignore and try preprocessing
        pass

    # 2) Try pycparser.parse_file with cpp and fake includes (preferred)
    try:
        import pycparser
        from pycparser import parse_file
        fake_inc = os.path.join(os.path.dirname(pycparser.__file__), 'utils', 'fake_libc_include')
        # Only add the fake include dir if it actually exists. Passing a non-existent
        # include path to cpp causes an error like the one you reported.
        if os.path.isdir(fake_inc):
            cpp_args = ['-E', '-P', '-I', fake_inc]
        else:
            cpp_args = ['-E', '-P']
        ast = parse_file(file_path, use_cpp=True, cpp_path='cpp', cpp_args=cpp_args)
        dfc, blocks = compute_data_flow_complexity(ast)
        if blocks:
            return dfc, blocks
    except Exception:
        pass

    # 3) Fallback: run system cpp manually and parse the preprocessed output
    try:
        import subprocess
        proc = subprocess.run(['cpp', '-E', '-P', file_path], capture_output=True, text=True, timeout=30)
        if proc.returncode == 0 and proc.stdout:
            try:
                ast = parser.parse(proc.stdout)
                dfc, blocks = compute_data_flow_complexity(ast)
                return dfc, blocks
            except Exception:
                return 0, []
        else:
            return 0, []
    except Exception:
        return 0, []


def analyze_directory(directory: str, extensions: List[str], ignore: Optional[List[str]] = None) -> Dict[str, int]:
    """Aggregate DFC across all source files in a directory matching extensions.

    Returns a dict with total dfc, total_files, total_blocks.
    """
    if not os.path.exists(directory):
        raise FileNotFoundError(directory)

    total_dfc = 0
    total_files = 0
    total_blocks = 0

    for root, _, files in os.walk(directory):
        for name in files:
            if not any(name.endswith(ext) for ext in extensions):
                continue
            if ignore and any(__import__("re").match(pat, name) for pat in ignore):
                continue
            path = os.path.join(root, name)
            dfc, blocks = analyze_file(path)
            total_dfc += dfc
            total_blocks += len(blocks)
            total_files += 1

    return {"dfc": total_dfc, "files": total_files, "blocks": total_blocks}


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
            dfc, blocks = analyze_file(self.src)
            return {"dfc": dfc, "files": 1, "blocks": len(blocks)}
        else:
            return analyze_directory(self.src, self.src_file_extensions, self.ignore)


def write_dfc_csv(output_path: str, metrics: Dict[str, int]):
    fieldnames = ["dfc", "files", "blocks"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = __import__("csv").DictWriter(f, fieldnames=fieldnames)
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
        except FileNotFoundError:
            out_file = os.path.join(output_dir, f"{proj.name.replace(' ', '_').lower()}_dfc.csv")
            with open(out_file, "w", newline="", encoding="utf-8") as f:
                writer = __import__("csv").writer(f)
                writer.writerow(["error"])
                writer.writerow([f"path not found: {proj.src}"])

    print(f"Wrote DFC metrics to: {output_dir}")
