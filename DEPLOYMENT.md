# Docker Deployment Guide

This guide explains how to deploy and run the code analysis tool in a Docker container.

## Prerequisites

- Docker installed on your system
- Docker Compose (optional, but recommended)

## Deployment Options

### Option 1: Using Docker Compose (Recommended)

1. **Build and run the container:**
   ```bash
   docker-compose up --build
   ```

2. **View the results:**
   The analysis output will be saved in the `output/` directory on your host machine.

3. **Stop the container:**
   ```bash
   docker-compose down
   ```

### Option 2: Using Docker CLI

1. **Build the Docker image:**
   ```bash
   docker build -f Dockerfile.new -t code-analyzer .
   ```

2. **Run the container:**
   ```bash
   docker run --rm -v $(pwd)/output:/app/output code-analyzer
   ```

   This command will:
   - Run the container
   - Mount the `output` directory to save results
   - Automatically remove the container after completion (`--rm`)

3. **Run specific analysis (optional):**
   ```bash
   # Run only cyclomatic complexity analysis
   docker run --rm -v $(pwd)/output:/app/output code-analyzer python cc.py
   
   # Run only SLOC analysis
   docker run --rm -v $(pwd)/output:/app/output code-analyzer python sloc.py
   ```

### Option 3: Interactive Mode

To explore the container interactively:

```bash
docker run -it --rm -v $(pwd)/output:/app/output code-analyzer /bin/bash
```

Inside the container, you can:
- Inspect the cloned repositories
- Run individual Python scripts
- Debug issues

## What Happens Inside the Container

1. Python 3.11 environment is set up
2. Git is installed
3. Four repositories are cloned:
   - jsoncpp
   - ogre
   - sqlite
   - tmux
4. All analysis scripts run:
   - `cc.py` - Cyclomatic Complexity
   - `cocomo.py` - COCOMO metrics
   - `dfc.py` - Data Flow Complexity
   - `halstead.py` - Halstead metrics
   - `sloc.py` - Source Lines of Code
5. Results are saved to the `output/` directory

## Output

After running, check the `output/` directory for:
- CSV files with analysis results
- Any generated plots or reports

## Troubleshooting

**Problem: Container exits immediately**
- Check logs: `docker-compose logs` or `docker logs <container-id>`

**Problem: No output generated**
- Ensure the output directory is writable
- Check if repositories were cloned successfully

**Problem: Python script errors**
- Run in interactive mode to debug
- Check if all required files are copied to the container

## Updating the Repositories

The repositories are cloned when building the image. To update them:

1. Rebuild the image:
   ```bash
   docker-compose build --no-cache
   ```

Or with Docker CLI:
   ```bash
   docker build --no-cache -f Dockerfile.new -t code-analyzer .
   ```
