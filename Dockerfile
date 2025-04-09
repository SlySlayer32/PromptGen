FROM python:3.9-slim

LABEL maintainer="CompLinguistics <support@comp-linguistics.io>"
LABEL org.opencontainers.image.source="https://github.com/comp-linguistics/transform-action"
LABEL org.opencontainers.image.description="Transforms text into formal computational linguistics style"
LABEL org.opencontainers.image.licenses="MIT"

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

# Create app directory
WORKDIR /app

# Copy source code
COPY src/ /app/src/

# Make entrypoint executable
RUN chmod +x /app/src/entrypoint.py

# Set entrypoint
ENTRYPOINT ["python", "/app/src/entrypoint.py"]
