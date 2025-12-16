FROM python:3.10-slim

WORKDIR /app

# Install dependencies
# Context is project root (.), so we copy from services/auth/
COPY services/auth/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project context into /app so that python modules defined in 'services' interact correctly
# (e.g. from services.auth.main import app)
COPY . /app/

# Set configs
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Run
CMD ["uvicorn", "services.auth.main:app", "--host", "0.0.0.0", "--port", "8000"]
