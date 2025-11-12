import os
import sys
from typing import Dict, List, Optional, Tuple
import networkx as nx
from pycparser import c_parser, c_ast
from contextlib import contextmanager


@contextmanager
def suppress_stderr():
    """Context manager to suppress stderr output (preprocessing errors)."""
    devnull = open(os.devnull, 'w')
    old_stderr = sys.stderr
    sys.stderr = devnull
    try:
        yield
    finally:
        sys.stderr = old_stderr
        devnull.close()


class DataFlowAnalyzer(c_ast.NodeVisitor):
    """Extract basic blocks with definitions and uses from a C AST.
    
    This analyzer implements Oviedo's Data Flow Complexity approach by:
    1. Identifying basic blocks in the control flow
    2. Tracking variable definitions (defs) and uses in each block
    3. Computing locally exposed variables (variables used before being defined)
    """

    def __init__(self):
        self.blocks: List[Dict[str, set]] = []
        self.current_block = {"defs": set(), "uses": set(), "exposed": set()}
        self.visited_ids: set = set()  # Track IDs visited in current block

    def add_block(self):
        """Finalize current block and compute locally exposed variables."""
        if self.current_block["defs"] or self.current_block["uses"]:
            # Locally exposed variables: used before being defined in the block
            self.current_block["exposed"] = self.current_block["uses"] - self.current_block["defs"]
            self.blocks.append(self.current_block)
        self.current_block = {"defs": set(), "uses": set(), "exposed": set()}
        self.visited_ids = set()

    # Assignments create defs on the lvalue and uses on the rvalue
    def visit_Assignment(self, node):
        # First visit rvalue to capture uses
        if node.rvalue:
            self.visit(node.rvalue)
        # Then record definition
        if isinstance(node.lvalue, c_ast.ID):
            self.current_block["defs"].add(node.lvalue.name)

    def visit_ID(self, node):
        """Track identifier uses."""
        # Record as use only if not yet defined in this block
        if node.name not in self.current_block["defs"]:
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
    """Compute Oviedo's Data Flow Complexity (DFC) metric from the AST.

    Implementation of Oviedo's method:
    1. Build basic blocks with def/use/exposed variable sets
    2. Construct a control flow graph (simplified sequential for this implementation)
    3. Compute reaching definitions using iterative data flow analysis
    4. Calculate DFC as the sum of reaching definitions for locally exposed variables
    
    Returns:
        Tuple of (dfc_score, list_of_blocks)
    """
    analyzer = DataFlowAnalyzer()
    analyzer.visit(ast_root)
    # Ensure last block is captured
    analyzer.add_block()

    n = len(analyzer.blocks)
    if n == 0:
        return 0, analyzer.blocks

    # Build a simplified sequential control flow graph (0->1->2->...)
    # For more complex programs, this could be enhanced to handle branches/loops
    G = nx.DiGraph()
    G.add_nodes_from(range(n))
    for i in range(n - 1):
        G.add_edge(i, i + 1)

    # Compute reaching definitions using iterative data flow analysis
    # OUT[block] = (IN[block] - KILL[block]) ∪ GEN[block]
    # IN[block] = ∪ OUT[pred] for all predecessors
    reaching_in: List[set] = [set() for _ in range(n)]
    reaching_out: List[set] = [set() for _ in range(n)]
    
    # Iteratively compute reaching definitions until convergence
    changed = True
    iteration = 0
    while changed:
        changed = False
        iteration += 1
        
        for i in range(n):
            # IN[i] = union of OUT of all predecessors
            new_in = set()
            for pred in G.predecessors(i):
                new_in |= reaching_out[pred]
            
            # OUT[i] = (IN[i] - KILL[i]) ∪ GEN[i]
            # GEN[i] = definitions generated in block i
            generated = set((var, i) for var in analyzer.blocks[i]["defs"])
            
            # KILL[i] = definitions of same variables from other blocks
            killed_vars = analyzer.blocks[i]["defs"]
            surviving = {(var, blk) for (var, blk) in new_in if var not in killed_vars}
            
            new_out = surviving | generated
            
            if new_in != reaching_in[i] or new_out != reaching_out[i]:
                reaching_in[i] = new_in
                reaching_out[i] = new_out
                changed = True
    
    # Calculate DFC: For each block, count reaching definitions of locally exposed variables
    dfc = 0
    for i in range(n):
        exposed_vars = analyzer.blocks[i]["exposed"]
        # Count definitions from OTHER blocks that reach this block's exposed variables
        reaching_for_exposed = {(var, blk) for (var, blk) in reaching_in[i] 
                                if var in exposed_vars and blk != i}
        dfc += len(reaching_for_exposed)
    
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
        import subprocess
        fake_inc = os.path.join(os.path.dirname(pycparser.__file__), 'utils', 'fake_libc_include')
        # Only add the fake include dir if it actually exists. Passing a non-existent
        # include path to cpp causes an error like the one you reported.
        if os.path.isdir(fake_inc):
            cpp_args = ['-E', '-P', '-I', fake_inc]
        else:
            cpp_args = ['-E', '-P']
        # Redirect stderr to suppress preprocessing errors
        with suppress_stderr():
            ast = parse_file(file_path, use_cpp=True, cpp_path='cpp', cpp_args=cpp_args)
            dfc, blocks = compute_data_flow_complexity(ast)
            if blocks:
                return dfc, blocks
    except Exception:
        pass

    # 3) Fallback: run system cpp manually with suppressed errors and parse the preprocessed output
    try:
        import subprocess
        proc = subprocess.run(
            ['cpp', '-E', '-P', file_path], 
            capture_output=True, 
            text=True, 
            timeout=30,
            stderr=subprocess.DEVNULL  # Suppress preprocessing errors
        )
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
