# docker build -t gitlab.ilabt.imec.be:4567/josperei/multi-stage-ids-for-kubernetes/flow_generator_slim .
# docker login registry.example.com -u <username>
# docker run -it --rm -p8089:8089 flow_generator_slim

# 327 Mb container
FROM python:3.10-slim-bullseye

# 1.12 Gb container
# FROM python:3.9

WORKDIR /app

# Setup Python working environment
COPY requirements.txt .

# Upgrade pip
RUN pip install --upgrade pip

RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy clean flow samples and locustfile to working directory
COPY . .

EXPOSE 8089 5557

# Run API
ENTRYPOINT ["locust"]