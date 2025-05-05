FROM node:18-slim as frontend-builder

# Set working directory for frontend
WORKDIR /frontend-build

# Copy frontend files from the parent directory
COPY ../3cf9f4ea-644d-446c-9e93-d72bd1fd11e0/package*.json ./
RUN npm ci

COPY ../3cf9f4ea-644d-446c-9e93-d72bd1fd11e0 ./

# Build frontend
RUN npm run build

# Backend and final image
FROM python:3.10-slim

# Install essential system dependencies
RUN apt-get update -y && apt-get install -y \
    awscli \
    build-essential \
    curl \
    nginx \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for serving the frontend
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy backend files
COPY ./ /app/

# Setup nginx configuration
COPY ./nginx.conf /etc/nginx/nginx.conf

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -e .

# Copy frontend build from the frontend-builder stage
COPY --from=frontend-builder /frontend-build/dist /var/www/html

# Copy frontend package.json for serving
COPY 3cf9f4ea-644d-446c-9e93-d72bd1fd11e0/package.json /app/3cf9f4ea-644d-446c-9e93-d72bd1fd11e0/

# Install serve for the frontend
RUN npm install -g serve

# Copy startup script
COPY ./start-services.sh /app/
RUN chmod +x /app/start-services.sh

# Set environment variables
ENV PORT=8080
ENV FRONTEND_PORT=80

# Expose ports
EXPOSE 80
EXPOSE 8080

# Start all services
CMD ["/app/start-services.sh"]