FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Configure Poetry to not use virtual environments in Docker
RUN poetry config virtualenvs.create false

# Copy Poetry configuration files
COPY pyproject.toml poetry.lock* ./

# Install dependencies (using --no-root to avoid installing the current project)
RUN poetry install --no-interaction --no-ansi --no-root

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Start the application directly with CMD
CMD bash -c "echo 'Waiting for PostgreSQL to start...' && \
    sleep 5 && \
    echo 'Running database migrations...' && \
    alembic upgrade head || (alembic revision --autogenerate -m 'Initial migration' && alembic upgrade head) && \
    echo 'Starting application...' && \
    uvicorn app.main:app --host 0.0.0.0 --port 8000"
