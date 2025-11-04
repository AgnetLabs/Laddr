FROM python:3.11-slim

WORKDIR /app

# Ensure project root is importable (so `workers` and `agents` packages resolve)
ENV PYTHONPATH=/app:${PYTHONPATH}

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt ./

# Install laddr and dependencies
# For development: laddr is installed from requirements.txt (git+ or local path)
# For production: RUN pip install --no-cache-dir laddr
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (project files mounted in dev via volumes)
COPY . .

CMD ["python", "-m", "laddr.api.main"]
