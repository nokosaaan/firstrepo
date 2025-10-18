FROM python:3.10-slim

# Reduce buffering for logging
ENV PYTHONUNBUFFERED=1

WORKDIR /bot

# Copy only requirements first so Docker can cache installs when source changes
COPY requirements.txt /bot/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . /bot

# Document the port the Flask app uses (optional)
EXPOSE 8080

# Start the bot
CMD ["python3", "discordbot.py"]