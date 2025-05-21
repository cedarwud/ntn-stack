FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    iputils-ping \
    dnsutils \
    iproute2 \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY proxy_api.py /app/

RUN pip install --no-cache-dir fastapi uvicorn requests

EXPOSE 8888

CMD ["python", "proxy_api.py"]
