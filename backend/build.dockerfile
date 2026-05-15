FROM python:3.11-slim

# Install Node.js and Claude Code CLI
RUN apt-get update && apt-get install -y curl gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g @anthropic-ai/claude-code

WORKDIR /app

# Copy your backend code
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

# Copy your agent project (if it’s in the same repo)
# Assuming coteach gui/ is in the parent folder; adjust as needed
# Option A: Include it in the Docker image (if you bundle everything)
# Option B: Clone it at build time (if it’s a separate repo)

# Start the FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]