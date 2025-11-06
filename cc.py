import re
import sys
import os
import csv

control_structures = ['if', 'else if', 'for', 'while', 'do', 'case', 'switch']

class project:
    def __init__(self, name, description, src, src_file_extensions, ignore=None):
        self.name = name
        self.description = description
        self.src = src
        self.src_file_extensions = src_file_extensions
        self.ignore = ignore
    
    def get_cc_metrics(self):
        """
        Traverse self.src and compute cyclomatic complexity per function for files
        matching self.src_file_extensions. Returns a dict with total CC, file
        count and details list of dicts: {filename, function_start, function_end, cc}.
        """
        if not os.path.exists(self.src):
            raise FileNotFoundError(self.src)

        total_cc = 0
        files_count = 0
        details = []

        def handle_file(path):
            try:
                funcs = find_functions_in_file(path)
            except Exception:
                return None
            return funcs

        if os.path.isfile(self.src):
            if any(self.src.endswith(ext) for ext in self.src_file_extensions):
                recs = handle_file(self.src)
                if recs:
                    for r in recs:
                        details.append(r)
                        total_cc += r['cc']
                    files_count += 1
        else:
            for root, dirs, files in os.walk(self.src):
                for name in files:
                    if not any(name.endswith(ext) for ext in self.src_file_extensions):
                        continue
                    if self.ignore and any(re.match(pattern, name) for pattern in self.ignore):
                        continue
                    path = os.path.join(root, name)
                    recs = handle_file(path)
                    if recs:
                        for r in recs:
                            details.append(r)
                            total_cc += r['cc']
                        files_count += 1

        return {"total_cc": total_cc, "files_count": files_count, "details": details}


def calculate_edges_and_nodes(file_path):
    # Read file with encoding fallbacks
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
    except (UnicodeDecodeError, PermissionError):
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                code = f.read()
        except Exception:
            return 0, 0

    # Remove single-line and multi-line comments
    code = re.sub(r'//.*', '', code)
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.S)

    # This function is kept for backward compatibility but is no longer used
    # in the per-function calculation. Return zeros to signal unused.
    return 0, 0

def calculate_cc(file_path):
    # Deprecated for per-function calculation. Keep simple fallback.
    return 0, 0, 0


def _read_file_with_fallback(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except (UnicodeDecodeError, PermissionError):
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception:
            return None


def _strip_comments_and_strings(code):
    # remove string literals (naive) and character literals to avoid counting
    code = re.sub(r'"(\\.|[^"\\])*"', '""', code, flags=re.S)
    code = re.sub(r"'(\\.|[^'\\])*'", "''", code, flags=re.S)
    # remove single-line and multi-line comments
    code = re.sub(r'//.*', '', code)
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.S)
    return code


def find_functions_in_file(file_path):
    """Return a list of dicts: filename, function_start (line), function_end (line), cc.
    Uses a heuristic regex to find function headers followed by a brace and matches braces to find body.
    """
    content = _read_file_with_fallback(file_path)
    if content is None:
        return []

    code = _strip_comments_and_strings(content)
    results = []

    # A heuristic regex to match function headers (C/C++ style). It matches return/type and name and params
    func_pattern = re.compile(r'([A-Za-z_~][\w:\*<>,\s\&\(\)\[\]]*?)\s+([A-Za-z_~][\w:]*)\s*\([^;{]*\)\s*(?:const\s*)?(?:->\s*[A-Za-z_][\w:]*)?\s*\{', re.M)

    for m in func_pattern.finditer(code):
        open_brace_idx = m.end() - 1
        # find matching closing brace
        idx = open_brace_idx
        length = len(code)
        balance = 0
        found = False
        while idx < length:
            ch = code[idx]
            if ch == '{':
                balance += 1
            elif ch == '}':
                balance -= 1
                if balance == 0:
                    close_brace_idx = idx
                    found = True
                    break
            idx += 1
        if not found:
            continue

        # Compute line numbers
        start_line = code[:m.start()].count('\n') + 1
        end_line = code[:close_brace_idx].count('\n') + 1

        body = code[m.end():close_brace_idx]

        # Count decision points inside the body
        decisions = 0
        decisions += len(re.findall(r'\bif\b', body))
        decisions += len(re.findall(r'\bfor\b', body))
        decisions += len(re.findall(r'\bwhile\b', body))
        decisions += len(re.findall(r'\bcase\b', body))
        decisions += len(re.findall(r'\bcatch\b', body))
        # ternary operator
        decisions += body.count('?')
        # logical operators
        decisions += body.count('&&')
        decisions += body.count('||')

        cc = decisions + 1

        results.append({
            'filename': file_path,
            'function_start': start_line,
            'function_end': end_line,
            'cc': cc,
        })

    return results

if __name__ == "__main__":
    # Define projects similar to sloc.py and write a cc.csv summary
    projects = [
        project(
            name="Json CPP",
            description="jsoncpp",
            src="jsoncpp/src/lib_json",
            src_file_extensions=[".cpp"],
        ),
        project(
            name="OGRE",
            description="Object-Oriented Graphics Rendering Engine",
            src="ogre/OgreMain/src",
            src_file_extensions=[".c", ".cpp"],
        ),
        project(
            name="Sqlite",
            description="SQLite",
            src="sqlite/src",
            src_file_extensions=[".c"],
            ignore=["test.*"]
        ),
        project(
            name="tmux",
            description="Terminal multiplexer",
            src="tmux",
            src_file_extensions=[".c"],
            ignore=["compat/.*"]
        ),
    ]

    output_dir = "output/cc"
    os.makedirs(output_dir, exist_ok=True)

    try:
        for project in projects:
            with open(f"{output_dir}/{project.name.replace(' ', '_').lower()}_cc.csv", "w") as f:
                f.write("filename,function_start,function_end,cyclomatic\n")
                metrics = project.get_cc_metrics()
                for detail in metrics["details"]:
                    f.write(f"{detail['filename']},{detail['function_start']},{detail['function_end']},{detail['cc']}\n")

    except FileNotFoundError:
        print(f"File not found: {project.src}")
        sys.exit(1)
