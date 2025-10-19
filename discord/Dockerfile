FROM python:3.11-slim

# Set working directory
WORKDIR /discord

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot script
COPY example_bot.py .

# Run the bot
CMD ["python3", "example_bot.py"]