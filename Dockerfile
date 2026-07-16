FROM python:3.13-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

# Copy only the build config first so the dependency-install layer below is
# cached across source-only changes to backend/ (STORY-093 AC1). Deps are
# derived from pyproject.toml's [project] dependencies via stdlib tomllib —
# `pip install .` itself needs `backend/` present (package-dir = {""="backend"}),
# so it is deferred to after the source copy, riding on the already-installed deps.
COPY pyproject.toml /app/
RUN python -c "import tomllib; deps = tomllib.load(open('pyproject.toml', 'rb'))['project']['dependencies']; print('\n'.join(deps))" > /app/requirements.txt \
    && pip install --no-cache-dir -r /app/requirements.txt uvicorn[standard]

# Copy application source code
COPY backend /app/backend
COPY config /app/config

# Install the package itself (deps already installed above)
RUN pip install --no-cache-dir .

# Run as a non-root user (both the API and the loop process only bind a
# port / make outbound network calls and read /app — no writes to disk).
RUN useradd --create-home app
USER app

EXPOSE 8000

# Run API by default
CMD ["uvicorn", "src.composition.asgi:app", "--host", "0.0.0.0", "--port", "8000"]
