FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y \
    curl \
    gnupg \
    gcc \
    libpq-dev \
    python3-dev \
    build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python dependencies
COPY requirements.txt .
COPY main.py .
RUN pip install --upgrade pip && pip install -r requirements.txt

CMD ["/bin/python3", "main.py"]