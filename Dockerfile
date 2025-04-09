FROM python:3.9.18-slim

LABEL maintainer="CompLinguistics <support@comp-linguistics.io>"
LABEL org.opencontainers.image.source="https://github.com/comp-linguistics/transform-action"
LABEL org.opencontainers.image.description="Transforms text into formal computational linguistics style"
LABEL org.opencontainers.image.licenses="MIT"

# Set Python to run in unbuffered mode
ENV PYTHONUNBUFFERED=1

# Create app directory
WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    nltk==3.8.1 \
    requests==2.31.0 \
    pyyaml==6.0.1 \
    PyGithub==1.59.1 \
    tqdm==4.66.1 \
    gitpython==3.1.40

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger'); nltk.download('wordnet')"

# Copy source code
COPY src/ /app/src/

# Make entrypoint executable
RUN chmod +x /app/src/entrypoint.py

# Create a non-root user and switch to it
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app
USER appuser

# Set entrypoint
ENTRYPOINT ["python", "/app/src/entrypoint.py"]

# Add health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1
