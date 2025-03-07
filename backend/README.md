# Immo Backend

## Poetry Setup

This project now uses Poetry for dependency management. Poetry has been set up locally with all the required dependencies.

### Using Poetry Locally

Poetry has been installed and configured with all the dependencies from the original requirements.txt file. You can use the following commands to manage dependencies:

```bash
# Add a new dependency
poetry add package-name

# Update dependencies
poetry update

# Generate a new lock file
poetry lock
```

### Docker Integration

Currently, the Docker setup still uses requirements.txt for compatibility. To keep both systems in sync, follow these steps when adding or updating dependencies:

1. Use Poetry to add or update dependencies:
   ```bash
   poetry add new-package
   ```

2. Export the Poetry dependencies to requirements.txt:
   ```bash
   poetry export -f requirements.txt --output requirements.txt
   ```

3. This will ensure both Poetry and Docker use the same dependencies.

### Future Docker Integration with Poetry

When you're ready to fully migrate Docker to use Poetry, update the Dockerfile with:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Configure Poetry to not use virtual environments in Docker
RUN poetry config virtualenvs.create false

# Copy Poetry configuration files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-interaction --no-ansi

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Then rebuild your Docker container:

```bash
docker-compose build backend
docker-compose up backend