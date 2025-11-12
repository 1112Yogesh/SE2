# SE2 - Software Metrics Analyzer

A comprehensive software metrics analysis tool for C/C++ codebases. This project analyzes multiple open-source projects (JsonCPP, OGRE, SQLite, and tmux) and computes various software engineering metrics.

## Features

The analyzer computes the following software metrics:

1. **SLOC (Source Lines of Code)** - Counts physical and logical lines of code
2. **Cyclomatic Complexity (CC)** - Measures code complexity at the function level
3. **Halstead Metrics** - Analyzes operators and operands to compute complexity measures
4. **Data Flow Complexity (DFC)** - Estimates data flow complexity using Oviedo's method
5. **COCOMO** - Estimates project effort, development time, and team size

## Analyzed Projects

- **JsonCPP** - JSON parser library for C++
- **OGRE** - Object-Oriented Graphics Rendering Engine
- **SQLite** - Embedded SQL database engine
- **tmux** - Terminal multiplexer

## Prerequisites

### Option 1: Local Python Environment
- Python 3.7+
- Git (for cloning analyzed repositories)

### Option 2: Docker
- Docker installed and running

## Installation

### Local Setup

1. Clone or navigate to the project directory:
```bash
cd /path/to/SE2
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install lizard
```

4. Clone the repositories to analyze (if not already present):
```bash
git clone https://github.com/open-source-parsers/jsoncpp.git
git clone https://github.com/OGRECave/ogre.git
git clone https://github.com/sqlite/sqlite.git
git clone https://github.com/tmux/tmux.git
```

### Docker Setup

No additional setup needed if you use Docker - the container handles all dependencies.

## Usage

### Running Individual Metrics

You can run each metric analyzer separately:

```bash
python sloc.py      # Lines of Code metrics
python cc.py        # Cyclomatic Complexity
python halstead.py  # Halstead Complexity Metrics
python dfc.py       # Data Flow Complexity
python cocomo.py    # COCOMO Cost Estimation
```

### Running All Metrics

Execute all analyzers at once:

```bash
./run_all.sh
```

Or with explicit bash:
```bash
bash run_all.sh
```

### Using Docker

Run the analysis in a containerized environment:

```bash
./docker-run.sh
```

This script will:
1. Build the Docker image
2. Clone the repositories (if not present)
3. Run all analysis scripts
4. Save results to the `output/` directory

## Output

All metrics are saved as CSV files in the `output/` directory:

```
output/
├── sloc/
│   └── loc.csv
├── cc/
│   ├── [project]_cc.csv
│   └── cc_summary.csv
├── halstead/
│   └── [project]_halstead.csv
├── dfc/
│   ├── [project]_functions.csv
│   └── [project]_summary.csv
└── cocomo/
    ├── cocomo_organic.csv
    ├── cocomo_semi-detached.csv
    ├── cocomo_embedded.csv
    └── cocomo_all.csv
```

## Metric Descriptions

### SLOC (Source Lines of Code)
- **LOC**: Total lines including comments and blank lines
- **SLOC**: Source lines excluding comments and blank lines

### Cyclomatic Complexity
Measures the number of linearly independent paths through a function's source code. Higher values indicate more complex code.

### Halstead Metrics
- **n1, n2**: Number of unique operators and operands
- **N1, N2**: Total count of operators and operands
- **Vocabulary, Length, Volume, Difficulty, Effort**: Derived metrics
- **Time**: Estimated time to program (seconds)
- **Bugs**: Estimated number of bugs

### Data Flow Complexity (DFC)
Estimates data flow complexity based on parameter counts and control flow paths using Lizard analysis.

### COCOMO
Estimates project metrics using the Constructive Cost Model:
- **Effort**: Person-months required
- **Time**: Development time in months
- **People**: Average team size
- Three modes: Organic, Semi-detached, Embedded

## Notes

- Analysis scripts automatically handle encoding issues (UTF-8 with latin-1 fallback)
- Comments and string literals are stripped before complexity analysis
- Test files in SQLite are ignored from analysis
- Compatible files in tmux are excluded from DFC analysis

## Project Structure

```
.
├── sloc.py              # SLOC calculator
├── cc.py                # Cyclomatic Complexity analyzer
├── halstead.py          # Halstead metrics calculator
├── dfc.py               # Data Flow Complexity analyzer
├── cocomo.py            # COCOMO estimator
├── plot_cc.py           # Visualization utility
├── run_all.sh           # Run all analyzers
├── docker-run.sh        # Docker execution script
├── Dockerfile           # Docker image definition
├── build.sh             # Alternative Docker build/run
└── README.md            # This file
```

## Documentation

Additional notes and explanations are available in:
- `1.SLOC_Note.txt` - SLOC calculation details
- `2.CC_Note.txt` - Cyclomatic Complexity notes
- `3.Halstead_Note.md` - Halstead metrics explanation
- `4.OviedosDataFlowComplexity_Note.md` - DFC methodology
- `5.COCOMO_Note.md` - COCOMO model details

## License

This is an academic project for software engineering coursework.
