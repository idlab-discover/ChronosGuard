# docker build -t all_in_one_api .
# docker run -it --rm -p8004:8004 all_in_one_api

# 521 Mb container
FROM python:3.10-slim-bullseye

# 1.3 Gb container
# FROM python:3.9

WORKDIR /app

# Setup Python working environment
COPY requirements.txt .

# Upgrade pip
RUN pip install --upgrade pip

RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy fitted scalers and API to working directory
COPY . .

EXPOSE 8000

# Run API
ENTRYPOINT ["uvicorn", "main:app"]