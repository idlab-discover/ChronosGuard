# Zero-Day Detector API

The zero-day detector api builds further with the result of the **Multi-Class Classifier API** and corrects previously detected flows as attack either as `Benign` or true `Unknown` attack.

## API Endpoints

| HTTP Method | Endpoint   | Description                             |
|-------------|------------|-----------------------------------------|
| POST        | `/predict` | Run the ML pipeline for a classified flow.   |
| GET         |        `/` | Healthcheck                             |
| GET         |    `/docs` | OpenAPI documentation                   |

### Predict samples using the API

The API expects a HTTP POST request with a JSON body containing a list with the anomaly score and optional `timestamps` for the event time and processing timestamps.

```` bash
curl --location --request POST 'http://localhost:8003/predict' \
--header 'Content-Type: application/json' \
--data-raw '{
    "event_timestamp": "2022-08-10T12:53:56+00:00",
    "processing_timestamp_start": "2022-08-10T12:53:56.527624",
    "processing_timestamp_end": "2022-08-10T12:53:56.639806",
    "binary_timestamp_start": "2022-08-11T16:36:29.458953",
    "binary_timestamp_end": "2022-08-11T16:36:29.460145",
    "multi_class_timestamp_start": "2022-08-11T16:39:52.161857",
    "multi_class_timestamp_end": "2022-08-11T16:39:52.174882",
    "anomaly_score": 5.986074868310001e-05,
    "binary_prediction": "Attack",
    "multi_class_confidence": 0.4948453608247423,
    "multi_class_prediction": "Unknown"
}'
````

## Environment variables

`MODEL_TAU_U`
: The used threshold on the anomaly score to differentiate `Benign` from true `Unknown`.
**Default**: 0.0040588613744241275

### Uvicorn Environment Variables

Uvicorn is used as underlying ASGI web server and can be configured using environment variables with the prefix `UVICORN_`.

`UVICORN_HOST`
: Bind socket to this host. IPv6 addresses are supported, for example `::`
**Default**: "127.0.0.1"

`UVICORN_PORT`
: Bind socket with this port.
**Default**: "8000"

`UVICORN_WORKERS`
: Use multiple worker processes.
**Default**: "1"

For all available configuration options: see [Uvicorn Configuration](https://www.uvicorn.org/settings/).

## Build image

`docker build -t zero_day_api .`

## Run image

`docker run -it --rm -p8000:8000 zero_day_api`
