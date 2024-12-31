# Use official Python image as base
FROM python:3.12-slim

# Set metadata for the image
LABEL authors="zahla"

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the default FastAPI port
EXPOSE 2025

# Run the application with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "2025"]