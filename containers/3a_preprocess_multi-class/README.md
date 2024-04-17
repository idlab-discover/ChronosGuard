# Multi-Class Classifier API

This combined **Preprocessing** and **multi-class classifier API** builds further with the result of the combined **Preprocessing & Anomaly Detector API** and classifies a flow as one of the known attack classes or `Unkown` if the confidence is not high enough. When a flow is classified as `Unknown`, it is forwarded to last stage, **Zero-day Detector**.

## API Endpoints

| HTTP Method | Endpoint   | Description                             |
|-------------|------------|-----------------------------------------|
| POST        | `/predict` | Run the ML pipeline for a detected flow.   |
| GET         |        `/` | Healthcheck                             |
| GET         |    `/docs` | OpenAPI documentation                   |

### Predict samples using the API

The API expects a HTTP POST request with a JSON body containing a list with the scaled 67 features as `float` and optional `timestamps` for the event time and processing timestamps.

```` bash
curl --location --request POST 'http://localhost:8002/predict' \
--header 'Content-Type: application/json' \
--data-raw '{
    "event_timestamp": "2022-08-10T12:53:56+00:00",
    "binary_timestamp_start": "2022-08-11T16:36:29.458953",
    "binary_timestamp_end": "2022-08-11T16:36:29.460145",
    "anomaly_score": 5.986074868310001e-05,
    "binary_prediction": "Attack",
    "features_orig": [6.0,3.0,2.0,0.0,12.0,0.0,6.0,6.0,6.0,0.0,0.0,0.0,0.0,0.0,4000000.0,666666.7,3.0,0.0,3.0,3.0,3.0,3.0,0.0,3.0,3.0,0.0,0.0,0.0,0.0,0.0,0.0,40.0,0.0,666666.7,0.0,6.0,6.0,6.0,0.0,0.0,0.0,0.0,0.0,0.0,1.0,0.0,0.0,0.0,9.0,6.0,0.0,2.0,12.0,0.0,0.0,506.0,-1.0,1.0,20.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]
}'
````

## Environment variables

`MODEL_ZERO_DAY_HOST`
: The host address of the `Zero-day Classifier` in the following format: `http://<IP>:<PORT>`
**Default**: "http://zero_day_api:8003"

`MODEL_TAU_M`
: The used threshold on the confidence to classify a flow as a known attack or `Unknown`.
**Default**: 0.98

`MODEL_HTTPX_TIMEOUT`
: The http timeout used to call the next service in the chain.
**Default**: 60 (s)

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

`docker build -t preprocessing_multi_class_api .`

## Run image

`docker run -it --rm -p8000:8000 preprocessing_multi_class_api`
