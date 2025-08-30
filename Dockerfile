FROM python:3.13-slim

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
RUN pip install --upgrade pip
COPY requirements.txt . 
RUN pip install -r requirements.txt

COPY main.py .
COPY lib lib/

CMD ["python3", "main.py"]