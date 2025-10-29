FROM ubuntu:22.04

# Avoid warnings by switching to noninteractive
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    build-essential \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Install Python 3.11
RUN add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.11 python3.11-dev python3.11-venv python3-pip && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

# Install Node.js 20.x (LTS) and npm
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Verify installations
RUN python --version && \
    node --version && \
    npm --version && \
    poetry --version

# Create a non-root user
RUN useradd -m -s /bin/bash vscode && \
    mkdir -p /home/vscode/.vscode-server /home/vscode/.vscode-server-insiders && \
    chown -R vscode:vscode /home/vscode

# Install Poetry for vscode user
USER vscode
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    echo 'export PATH="/home/vscode/.local/bin:$PATH"' >> /home/vscode/.bashrc

# Switch back to root for any final setup
USER root

# Set working directory
WORKDIR /workspaces/Team-H

# Switch back to dialog for any ad-hoc use of apt-get
ENV DEBIAN_FRONTEND=dialog
