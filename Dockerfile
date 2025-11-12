# Use Python base image
FROM python:3.11-slim

# Install git
RUN apt-get update && apt-get install -y git && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir lizard

# Set the working directory
WORKDIR /workspace

# Default command: open bash shell
CMD ["/bin/bash"]
