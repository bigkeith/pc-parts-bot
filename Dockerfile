# Use a slim, official Python image - small download, has everything
# we need without extra bloat
FROM python:3.12-slim

# All commands from here on run inside this folder in the container
WORKDIR /app
# Without this, Python buffers print() output, so nothing shows up
# in "docker compose logs" until the buffer fills or the container
# stops - this makes output appear immediately instead.
ENV PYTHONUNBUFFERED=1
# Copy just the requirements file first (not the whole project yet).
# This is a Docker best practice: if only your code changes but not
# your dependencies, Docker can reuse the cached "pip install" layer
# instead of reinstalling everything from scratch every time.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the project code into the container
COPY . .

# Run the bot. This starts main.py's scheduling loop, which runs
# forever (checking every CHECK_INTERVAL_MINUTES) until the
# container is stopped.
CMD ["python", "main.py"]