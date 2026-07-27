FROM node:20-alpine

# Install dependencies: PowerShell, Docker client, bash
RUN apk add --no-cache \
    bash \
    curl \
    jq \
    docker \
    pwsh \
    sudo \
    tzdata

# Create app directory
WORKDIR /app

# Copy web UI and scripts
COPY webui/ ./webui/
COPY scripts/ ./scripts/
COPY entrypoint.sh ./entrypoint.sh

RUN chmod +x entrypoint.sh

# Install Node dependencies
WORKDIR /app/webui
RUN npm init -y && npm install express body-parser cors

WORKDIR /app

EXPOSE 8080

ENTRYPOINT ["/app/entrypoint.sh"]