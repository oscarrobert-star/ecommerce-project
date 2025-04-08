# Stage 1: Build the app
FROM node:18-alpine as build

WORKDIR /app

# Copy package.json and package-lock.json for npm install
COPY package*.json ./

# Install dependencies (including dev dependencies)
RUN npm install

# Copy the rest of the app's source code
COPY . .

# Build the app (production build)
RUN npm run build

# Stage 2: Create a smaller image
FROM node:18-alpine

WORKDIR /app

# Copy only the necessary build files from the previous stage
COPY --from=build /app/dist /app/dist
COPY --from=build /app/node_modules /app/node_modules

# Expose the port for the application
EXPOSE 5173

# Command to run the app
CMD ["npm", "run", "dev"]
