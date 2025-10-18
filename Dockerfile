FROM python:3.11-slim

WORKDIR /app

# Accept build-time argument
ARG DEV_MODE=false
ENV DEV_MODE=${DEV}

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy static files into the image
COPY static/ ./static/

# Copy app code and templates
COPY templates/ ./templates/
COPY src/ ./

# Declare packs/ as a volume
VOLUME ["/app/packs"]
VOLUME ["/app/static/images"]

# Expose Flask port
EXPOSE 5000

# Conditional entrypoint
CMD ["/bin/sh", "-c", "if [ \"$DEV_MODE\" = \"true\" ]; then python app.py; else gunicorn --bind 0.0.0.0:5000 app:app; fi"]
