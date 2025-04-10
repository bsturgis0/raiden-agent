# Use multi-stage build
FROM python:3.12-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libsqlite3-dev \
    python3-dev \
    libgtk-3-dev \
    libwebkit2gtk-4.0-dev \
    libglib2.0-dev \
    libgirepository1.0-dev \
    gir1.2-gtk-3.0 \
    gir1.2-webkit2-4.0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create workspace directory
RUN mkdir -p /app/raiden_workspace_srv

# Set environment variables
ENV PYTHONPATH=/app
ENV RAIDEN_WORKSPACE=/app/raiden_workspace_srv

# Server stage
FROM base as server
EXPOSE 5000
CMD ["python", "app.py"]

# Desktop build stage
FROM base as desktop
# Install additional desktop dependencies
RUN apt-get update && apt-get install -y \
    python3-tk \
    libappindicator3-dev \
    && rm -rf /var/lib/apt/lists/*

# Build desktop app
RUN python build.py

# Output stage - choose either server or desktop
FROM ${BUILD_TYPE:-server}
# The default is server, use --build-arg BUILD_TYPE=desktop for desktop app
