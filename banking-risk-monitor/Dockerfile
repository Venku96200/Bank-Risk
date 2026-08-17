# Start from a small, official Python image.
FROM python:3.10-slim

# All commands below run from /app inside the container.
WORKDIR /app

# Copy just the requirements file first (not the whole project yet).
# Docker caches each step — if requirements.txt hasn't changed, it skips
# reinstalling everything on your next build, which saves a lot of time.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the project in.
COPY . .

# Document that the app listens on port 8000 (informational only —
# the actual port mapping happens in docker-compose.yml).
EXPOSE 8000

# The command that runs when the container starts.
# --host 0.0.0.0 is required so the app is reachable from outside the container.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
