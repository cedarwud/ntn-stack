FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    iproute2 \
    iputils-ping \
    net-tools \
    tcpdump \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 9091

CMD ["python", "metrics_exporter.py", "--port", "9091", "--simulate"] 