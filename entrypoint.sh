#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Apply database migrations
echo "Applying database migrations..."
python3.10 manage.py migrate

# Collect static files (optional, useful if you have static files)
echo "Collecting static files..."
python3.10 manage.py collectstatic --noinput

# Start the Django development server
echo "Starting Django development server..."
exec "$@"
