FROM ghcr.io/home-assistant/home-assistant:stable

# Install dev tools for Smart Home development
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python development tools
RUN pip install --upgrade pip setuptools wheel && \
    pip install \
    pytest \
    pytest-asyncio \
    black \
    isort \
    mypy \
    pylint

WORKDIR /workspace
