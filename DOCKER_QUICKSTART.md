# Docker Quick Start Guide

## ✅ Fixed and Ready to Use!

Your Docker setup is now fully functional with all dependencies installed.

## Quick Commands

### Using Docker Compose (Easiest)
```bash
# Build and run
docker-compose up --build

# Run with existing image
docker-compose up

# Clean up
docker-compose down
```

### Using Docker CLI
```bash
# Build the image
docker build -t code-analyzer .

# Run the container
docker run --rm -v $(pwd)/output:/app/output code-analyzer

# Run specific analysis only
docker run --rm -v $(pwd)/output:/app/output code-analyzer python sloc.py
```

### Interactive Mode (Debugging)
```bash
docker run -it --rm -v $(pwd)/output:/app/output code-analyzer /bin/bash
```

## What's Inside

- **Base:** Python 3.11-slim
- **Dependencies:** lizard (for code complexity analysis)
- **Repositories cloned:**
  - jsoncpp
  - ogre
  - sqlite
  - tmux

## Analysis Scripts Run

1. `cc.py` - Cyclomatic Complexity
2. `cocomo.py` - COCOMO cost estimation
3. `dfc.py` - Data Flow Complexity (uses lizard)
4. `halstead.py` - Halstead metrics
5. `sloc.py` - Source Lines of Code

## Output

Results are automatically saved to `./output/` with subdirectories:
- `output/cc/` - Cyclomatic complexity results
- `output/cocomo/` - COCOMO metrics
- `output/dfc/` - Data flow complexity
- `output/halstead/` - Halstead metrics
- `output/sloc/` - Line counts

## Troubleshooting

If you encounter credential errors with Docker:
```bash
# Remove the credsStore setting
sed -i.bak '/"credsStore"/d' ~/.docker/config.json
```

Then rebuild:
```bash
docker-compose build --no-cache
```
