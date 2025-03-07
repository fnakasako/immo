FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \  # Add PostgreSQL client libraries
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

# Create a startup script
RUN echo '#!/bin/bash\n\
echo "Waiting for PostgreSQL to start..."\n\
sleep 5\n\
echo "Running database migrations..."\n\
alembic upgrade head || (alembic revision --autogenerate -m "Initial migration" && alembic upgrade head)\n\
echo "Starting application..."\n\
uvicorn app.main:app --host 0.0.0.0 --port 8000\n\
' > /app/start.sh && chmod +x /app/start.sh

# Start the application
CMD ["/app/start.sh"]
