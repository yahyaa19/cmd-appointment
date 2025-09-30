# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8007 available to the world outside this container
EXPOSE 8007

# Run app.py when the container launches
# Change this line in your Dockerfile
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8007"]
