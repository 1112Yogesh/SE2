import sys
import os

class project:
    def __init__(self, name, description, src, src_file_extensions):
        self.name = name
        self.description = description
        self.src = src
        self.src_file_extensions = src_file_extensions

    def get_LOC(self):
        def count_file(path):
            cnt = 0
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for _ in f:
                        cnt += 1
            except (UnicodeDecodeError, PermissionError):
                # fallback to latin-1 for files with different encoding, skip unreadable files
                try:
                    with open(path, 'r', encoding='latin-1') as f:
                        for _ in f:
                            cnt += 1
                except Exception:
                    return 0
            except IsADirectoryError:
                return 0
            return cnt
        
        if not os.path.exists(self.src):
            raise FileNotFoundError(self.src)

        total = 0
        if os.path.isfile(self.src):
            return count_file(self.src)

        for root, dirs, files in os.walk(self.src):
            for name in files:
                if not any(name.endswith(ext) for ext in self.src_file_extensions):
                    continue
                path = os.path.join(root, name)
                total += count_file(path)

        return total

    def get_SLOC(self):
        # Source Lines of Code (SLOC) counting can be implemented here
        def count_file(path):
            cnt = 0
            file_content = ""
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        file_content += line
            except (UnicodeDecodeError, PermissionError):
                # fallback to latin-1 for files with different encoding, skip unreadable files
                try:
                    with open(path, 'r', encoding='latin-1') as f:
                        for line in f:
                            file_content += line
                except Exception:
                    return 0
            except IsADirectoryError:
                return 0
            file_content.replace('\r\n', '\n').replace('\r', '\n')
            lines = file_content.split('\n')
            in_multiline_comment = False
            for line in lines:
                stripped_line = line.strip()
                if in_multiline_comment:
                    if '*/' in stripped_line:
                        in_multiline_comment = False
                        stripped_line = stripped_line.split('*/', 1)[1].strip()
                    else:
                        continue
                if not stripped_line or stripped_line.startswith('//'):
                    continue
                if '/*' in stripped_line:
                    in_multiline_comment = True
                    stripped_line = stripped_line.split('/*', 1)[0].strip()
                    if not stripped_line:
                        continue
                cnt += 1
            return cnt



        
        if not os.path.exists(self.src):
            raise FileNotFoundError(self.src)

        total = 0
        if os.path.isfile(self.src):
            return count_file(self.src)

        for root, dirs, files in os.walk(self.src):
            for name in files:
                if not any(name.endswith(ext) for ext in self.src_file_extensions):
                    continue
                path = os.path.join(root, name)
                total += count_file(path)

        return total

    def get_cocomo_metrics(self, mode="organic"):
        """
        Calculate COCOMO metrics based on SLOC.
        
        Modes:
        - organic: Small teams, familiar environment (a=2.4, b=1.05, c=2.5, d=0.38)
        - semi-detached: Medium complexity (a=3.0, b=1.12, c=2.5, d=0.35)
        - embedded: Complex, strict constraints (a=3.6, b=1.20, c=2.5, d=0.32)
        
        Returns:
        - effort: Person-months
        - time: Development time in months
        - people: Average team size
        """
        sloc_kloc = self.get_SLOC() / 1000.0  # Convert SLOC to KLOC
        
        # COCOMO coefficients for different modes
        coefficients = {
            "organic": {"a": 2.4, "b": 1.05, "c": 2.5, "d": 0.38},
            "semi-detached": {"a": 3.0, "b": 1.12, "c": 2.5, "d": 0.35},
            "embedded": {"a": 3.6, "b": 1.20, "c": 2.5, "d": 0.32}
        }
        
        if mode.lower() not in coefficients:
            mode = "organic"
        
        coeff = coefficients[mode.lower()]
        
        # Effort = a * (KLOC)^b (in person-months)
        effort = coeff["a"] * (sloc_kloc ** coeff["b"])
        
        # Development time = c * (Effort)^d (in months)
        time = coeff["c"] * (effort ** coeff["d"])
        
        # Average team size = Effort / Time
        people = effort / time if time > 0 else 0
        
        return {
            "effort": effort,
            "time": time,
            "people": people,
            "sloc_kloc": sloc_kloc
        }

if __name__ == "__main__":
    projects = [ project(
            name="Json CPP",
            description="jsoncpp",
            src="jsoncpp/src",
            src_file_extensions=[".h", ".cpp"],
        ),
        project(
            name="OGRE",
            description="Object-Oriented Graphics Rendering Engine",
            src="ogre/OgreMain",
            src_file_extensions=[".h", ".c", ".cpp"],
        ),
        project(
            name="Sqlite",
            description="SQLite",
            src="sqlite/src",
            src_file_extensions=[".h", ".c"],
        ),
        project(
            name="tmux",
            description="Terminal multiplexer",
            src="tmux",
            src_file_extensions=[".h", ".c"],
        )
    ]

    output_dir = "output/cocomo"
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Write COCOMO metrics for all three modes
        modes = ["organic", "semi-detached", "embedded"]
        
        for mode in modes:
            with open(f"{output_dir}/cocomo_{mode}.csv", "w") as f:
                f.write("project,SLOC(KLOC),Effort(person-months),Time(months),People\n")
                for proj in projects:
                    metrics = proj.get_cocomo_metrics(mode=mode)
                    f.write(f"{proj.name},{metrics['sloc_kloc']:.2f},{metrics['effort']:.2f},{metrics['time']:.2f},{metrics['people']:.2f}\n")
                print(f"\nCOCOMO metrics ({mode} mode):")
                print(f"  Written to {output_dir}/cocomo_{mode}.csv")
        
        # Write combined COCOMO metrics
        with open(f"{output_dir}/cocomo_all.csv", "w") as f:
            f.write("project,mode,SLOC(KLOC),Effort(person-months),Time(months),People\n")
            for proj in projects:
                for mode in modes:
                    metrics = proj.get_cocomo_metrics(mode=mode)
                    f.write(f"{proj.name},{mode},{metrics['sloc_kloc']:.2f},{metrics['effort']:.2f},{metrics['time']:.2f},{metrics['people']:.2f}\n")
        
        print(f"\nAll COCOMO metrics written to {output_dir}/cocomo_all.csv")
        
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        sys.exit(1)
