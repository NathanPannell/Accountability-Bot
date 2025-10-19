# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY api/requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the api directory contents into the container at /app
COPY api/ .

# Copy the llm directory into the container
COPY llm/ ./llm/

# Make port available to the world outside this container
EXPOSE ${API_INTERNAL_PORT:-8000}

# Run uvicorn when the container launches
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${API_INTERNAL_PORT:-8000} --reload"]