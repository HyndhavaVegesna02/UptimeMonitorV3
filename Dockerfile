FROM python:3.13-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Copy build config and application source code
COPY pyproject.toml /app/
COPY backend /app/backend
COPY config /app/config

# Install the package and its dependencies, including uvicorn
RUN pip install --no-cache-dir . uvicorn[standard]

EXPOSE 8000

# Run API by default
CMD ["uvicorn", "src.composition.asgi:app", "--host", "0.0.0.0", "--port", "8000"]
