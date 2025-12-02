# Frontend Dockerfile for F1 WebApp
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Expose port
EXPOSE 4321

# Development command (override in production)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# Production build (uncomment for production)
# RUN npm run build
# CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0"]
