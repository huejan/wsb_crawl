# Start with a Python base image
# Switch to the full python:3.11 image to test if missing system dependencies
# in the slim image were causing issues with google-generativeai import.
FROM python:3.11

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the requirements file into the container
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port the app runs on
EXPOSE 8080

# Command to run the application
# Use Gunicorn to run the Flask app
# The PORT environment variable will be picked up by gunicorn if set,
# otherwise it defaults to 8000. Our app.main also uses PORT (default 8080).
# We will bind to 0.0.0.0:$PORT. The EXPOSE directive should match this.
# Number of workers can be adjusted based on the server resources.
# Example: CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:8080", "app.main:app"]

# Check for PORT env var, default to 8080 if not set for the CMD
# This makes the Dockerfile more self-contained if PORT isn't passed at runtime,
# though our app/main.py and .env.example already default to 8080.
# The `app.main:app` refers to the `app` Flask instance in the `app/main.py` file.
# Added --log-level debug, --access-logfile -, and --error-logfile - for more verbose logging to stdout/stderr.
CMD ["sh", "-c", "gunicorn --workers ${GUNICORN_WORKERS:-2} --bind 0.0.0.0:${PORT:-8080} --log-level debug --access-logfile - --error-logfile - app.main:app"]
