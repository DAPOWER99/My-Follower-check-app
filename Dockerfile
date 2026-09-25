FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose the port for the web server
EXPOSE 8000

# Run the bot
CMD ["python", "main.py"]
