# GTasks Dashboard - Docker Configuration
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./
COPY server/package*.json ./server/

# Install dependencies
RUN npm ci --only=production
RUN cd server && npm ci --only=production

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Build the server
RUN cd server && npm run build

# Expose ports
EXPOSE 3000 8080

# Create startup script
RUN echo '#!/bin/sh' > /app/start.sh && \
    echo 'npm run build' >> /app/start.sh && \
    echo 'cd server && npm run build' >> /app/start.sh && \
    echo 'npm run start' >> /app/start.sh && \
    chmod +x /app/start.sh

# Start the application
CMD ["npm", "run", "start"]