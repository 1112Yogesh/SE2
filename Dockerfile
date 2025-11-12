# Use Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (git + minimal build tools if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first (for caching)
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Clone repositories directly into /app
RUN git clone https://github.com/open-source-parsers/jsoncpp.git jsoncpp && \
    git clone https://github.com/OGRECave/ogre.git ogre && \
    git clone https://github.com/sqlite/sqlite.git sqlite && \
    git clone https://github.com/tmux/tmux.git tmux

# Copy all local Python and shell scripts
COPY *.py ./
COPY *.sh ./

# Make all shell scripts executable
RUN chmod +x *.sh

# Create output directory
RUN mkdir -p output

# Default command
CMD ["/bin/bash", "run_all.sh"]