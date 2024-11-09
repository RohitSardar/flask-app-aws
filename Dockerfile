# Use the official Python base image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app.py .

# Expose the application port
EXPOSE 5000

# Run the Flask app
CMD ["python", "app.py"]
