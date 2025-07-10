FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --no-cachedir fastapi uvicorn

CMD ["python3", "main.py", "--host", "0.0.0.0", "--port", "8080"]