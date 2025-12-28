FROM python:3.10-slim

WORKDIR /app

# Copy dependency definition
COPY services/exchange_adapter/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY . /app/

# Set Python Path to root so imports work
ENV PYTHONPATH=/app

CMD ["uvicorn", "services.exchange_adapter.main:app", "--host", "0.0.0.0", "--port", "8001"]
