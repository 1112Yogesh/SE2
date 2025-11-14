# -------------------------
# Base image
# -------------------------
FROM python:3.11-slim

# Install Git
RUN apt-get update && apt-get install -y git && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir lizard pandas numpy matplotlib Jinja2

# Working directory
WORKDIR /workspace

# Copy analysis script into image (optional)
COPY *.py /workspace/
COPY *.sh /workspace/

RUN chmod +x /workspace/run_all.sh


# -------------------------
# ENTRYPOINT SCRIPT
# -------------------------
# ENTRYPOINT that clones repos + runs run_all.sh
RUN echo '#!/bin/bash\n\
set -e\n\
echo \"Cloning repos...\"\n\
[ ! -d jsoncpp ] && git clone https://github.com/open-source-parsers/jsoncpp.git\n\
[ ! -d ogre ]    && git clone https://github.com/OGRECave/ogre.git\n\
[ ! -d sqlite ]  && git clone https://github.com/sqlite/sqlite.git\n\
[ ! -d tmux ]    && git clone https://github.com/tmux/tmux.git\n\
echo \"Running run_all.sh...\"\n\
/workspace/run_all.sh\n\
echo \"Finished. Opening shell...\"\n\
exec /bin/bash' > /entrypoint.sh

RUN chmod +x /entrypoint.sh
# -------------------------
# Default command
# -------------------------
ENTRYPOINT ["/entrypoint.sh"]