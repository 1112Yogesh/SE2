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
            src_file_extensions=[".c", ".h", ".cpp"],
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
            src_file_extensions=[".c", ".h"],
        )
    ]

    output_dir = "output/sloc"
    os.makedirs(output_dir, exist_ok=True)

    try:
        with open(f"{output_dir}/loc.csv", "w") as f:
            f.write("project,LOC,SLOC\n")
            for project in projects:
                line_count = project.get_LOC()
                sloc_count = project.get_SLOC()
                f.write(f"{project.name},{line_count},{sloc_count}\n")
                print(f"Processed project: {project.name}, LOC: {line_count}, SLOC: {sloc_count}")
    except FileNotFoundError:
        print(f"File not found: {project.src}")
        sys.exit(1)