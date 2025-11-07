FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential libpq-dev

# Create app directory
WORKDIR /app

# Copy ONLY requirements first to enable caching
COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Now copy the rest of the project
COPY . .

# Create logs directory
RUN mkdir -p /app/logs && chmod 755 /app/logs

# Collect static files at build time
RUN python manage.py collectstatic --noinput

# Run gunicorn with better logging
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-", "--error-logfile", "-", "eskd_project.wsgi:application"]

