# Use Python base image
FROM python:3.11-slim

# Install git (needed for cloning repositories)
RUN apt-get update && apt-get install -y git && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy all Python scripts
COPY *.py ./
COPY *.sh ./

# Make shell scripts executable
RUN chmod +x *.sh

# Clone the repositories if they don't exist
RUN git clone https://github.com/open-source-parsers/jsoncpp.git jsoncpp || true && \
    git clone https://github.com/OGRECave/ogre.git ogre || true && \
    git clone https://github.com/sqlite/sqlite.git sqlite || true && \
    git clone https://github.com/tmux/tmux.git tmux || true

# Create output directory
RUN mkdir -p output

# Default command: run all analysis scripts
CMD ["./run_all.sh"]
