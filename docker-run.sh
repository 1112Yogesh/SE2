#!/bin/bash

# Build the Docker image
echo "Building Docker image..."
docker build -t code-analyzer .

# Run the container with current directory mounted
echo "Running container..."
docker run -it --rm -v $(pwd):/workspace code-analyzer /bin/bash -c "
    cd /workspace
    echo 'Cloning repositories...'
    [ ! -d jsoncpp ] && git clone https://github.com/open-source-parsers/jsoncpp.git
    [ ! -d ogre ] && git clone https://github.com/OGRECave/ogre.git
    [ ! -d sqlite ] && git clone https://github.com/sqlite/sqlite.git
    [ ! -d tmux ] && git clone https://github.com/tmux/tmux.git
    echo 'Running analysis scripts...'
    bash run_all.sh
"
