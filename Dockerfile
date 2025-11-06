# Use a minimal, lightweight base image
FROM ubuntu:22.04
# Install git
RUN apt-get update && apt-get install -y git

# Set the working directory inside the container
# This is where we will mount the host's directory
WORKDIR /projects

# Set the command to run when the container starts
# This will clone all four repositories into the WORKDIR
# We explicitly name the target directories (e.g., "jsoncpp")
CMD ["sh", "-c", \
    "echo 'Starting to clone repositories into the current directory...'; \
    git clone https://github.com/open-source-parsers/jsoncpp.git jsoncpp && \
    git clone https://github.com/OGRECave/ogre.git ogre && \
    git clone https://github.com/sqlite/sqlite.git sqlite && \
    git clone https://github.com/tmux/tmux.git tmux; \
    echo 'Cloning complete!'"]